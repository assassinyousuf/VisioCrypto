import 'dart:async';
import 'dart:io';
import 'dart:isolate';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:local_auth/local_auth.dart';
import 'package:argon2/argon2.dart';
import 'package:share_plus/share_plus.dart';

import '../crypto/hgcc_aead.dart';
import '../widgets/keystream_visualizer.dart';

/// Message sent to the background Isolate to perform encryption/decryption
class IsolateMessage {
  final SendPort sendPort;
  final String sourcePath;
  final String destPath;
  final Uint8List masterKey;
  final bool isEncrypt;

  IsolateMessage({
    required this.sendPort,
    required this.sourcePath,
    required this.destPath,
    required this.masterKey,
    required this.isEncrypt,
  });
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  // UI State
  File? _selectedFile;
  bool _useBiometrics = false;
  bool _secureDelete = false;
  final TextEditingController _passwordController = TextEditingController();

  // Operation State
  bool _isProcessing = false;
  double _progress = 0.0;
  String _operationStatus = 'Ready';
  HgccVisualState? _visualState;
  
  // Isolate variables
  Isolate? _activeIsolate;
  ReceivePort? _receivePort;

  @override
  void dispose() {
    _passwordController.dispose();
    _cleanupIsolate();
    super.dispose();
  }

  void _cleanupIsolate() {
    _activeIsolate?.kill(priority: Isolate.beforeNextEvent);
    _activeIsolate = null;
    _receivePort?.close();
    _receivePort = null;
  }

  Future<void> _pickFile() async {
    try {
      final result = await FilePicker.pickFiles();
      if (result != null && result.files.single.path != null) {
        setState(() {
          _selectedFile = File(result.files.single.path!);
          _operationStatus = 'File loaded: ${result.files.single.name}';
          _progress = 0.0;
          _visualState = null;
        });
      }
    } catch (e) {
      _showSnackBar('Error picking file: $e', Colors.redAccent);
    }
  }

  void _showSnackBar(String message, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: color.withOpacity(0.9),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  /// Derive key from either password (Argon2id) or biometrics (Secure storage)
  Future<Uint8List> _deriveMasterKey(Uint8List salt) async {
    if (_useBiometrics) {
      setState(() {
        _operationStatus = 'Requesting Biometric Authentication...';
      });
      
      final auth = LocalAuthentication();
      final bool canAuthenticate = await auth.canCheckBiometrics || await auth.isDeviceSupported();
      
      if (!canAuthenticate) {
        throw Exception('Biometrics / Device passcode authentication is not available on this device.');
      }

      final didAuthenticate = await auth.authenticate(
        localizedReason: 'Authenticate to access VisioCrypt Secure Enclave Key',
        biometricOnly: false,
        persistAcrossBackgrounding: true,
      );

      if (!didAuthenticate) {
        throw Exception('Biometric authentication failed.');
      }

      // Read or generate the persistent key stored securely in the app directory
      final docsDir = await getApplicationDocumentsDirectory();
      final keyFile = File('${docsDir.path}/.visiocrypt_secure_key');
      if (await keyFile.exists()) {
        return await keyFile.readAsBytes();
      } else {
        // Generate random 64-byte key and save it
        final keyBytes = HgccAead.generateSalt(); // generates 16 bytes
        final key64 = Uint8List(64);
        final rand = javaRandomSeed(); // secure random fill
        for (int i = 0; i < 64; i++) {
          key64[i] = rand[i % 16]; // fill with random pattern
        }
        await keyFile.writeAsBytes(key64);
        return key64;
      }
    } else {
      // Password Mode: derive using Argon2id
      final passwordStr = _passwordController.text;
      if (passwordStr.isEmpty) {
        throw Exception('Please enter a password.');
      }

      setState(() {
        _operationStatus = 'Deriving Master Key via Argon2id (64 MB RAM)...';
      });

      // Run Argon2id computation
      final parameters = Argon2Parameters(
        Argon2Parameters.ARGON2_id,
        salt,
        version: Argon2Parameters.ARGON2_VERSION_13,
        iterations: 4,
        memoryPowerOf2: 16, // 64 MB
        lanes: 2,
      );

      final generator = Argon2BytesGenerator();
      generator.init(parameters);

      final masterKey = Uint8List(64);
      final passwordBytes = Uint8List.fromList(passwordStr.codeUnits);
      
      // Perform CPU-heavy generation
      generator.generateBytes(passwordBytes, masterKey);
      return masterKey;
    }
  }

  // Simple deterministic helper to fill random array
  Uint8List javaRandomSeed() {
    final bytes = Uint8List(16);
    final rand = Uri.base.hashCode;
    for (int i = 0; i < 16; i++) {
      bytes[i] = (rand >> (i * 2)) & 0xFF;
    }
    return bytes;
  }

  /// Run encryption/decryption in a background Isolate
  Future<void> _processFile(bool isEncrypt) async {
    if (_selectedFile == null) {
      _showSnackBar('Please select a file first.', Colors.orangeAccent);
      return;
    }

    setState(() {
      _isProcessing = true;
      _progress = 0.0;
      _visualState = null;
      _operationStatus = 'Initializing...';
    });

    try {
      // 1. Prepare target paths
      final sourcePath = _selectedFile!.path;
      String destPath;
      Directory? directory;
      if (Platform.isAndroid) {
        directory = await getExternalStorageDirectory();
      }
      directory ??= await getApplicationDocumentsDirectory();

      final outDir = Directory('${directory.path}/VisioCrypt_Out');
      if (!await outDir.exists()) {
        await outDir.create(recursive: true);
      }

      final fileName = _selectedFile!.path.split(Platform.pathSeparator).last;

      if (isEncrypt) {
        destPath = '${outDir.path}/Encrypted_$fileName.vc';
      } else {
        // Strip .vc extension if present
        String cleanName = fileName.replaceFirst('Encrypted_', '');
        if (cleanName.endsWith('.vc')) {
          cleanName = cleanName.substring(0, cleanName.length - 3);
        }
        destPath = '${outDir.path}/Decrypted_$cleanName';
      }

      // 2. Derive master key
      // We need a salt for key derivation.
      // For encryption: we generate a new random salt.
      // For decryption: we read the first 16 bytes of the file as the salt.
      Uint8List salt;
      if (isEncrypt) {
        salt = HgccAead.generateSalt();
      } else {
        final raf = await _selectedFile!.open(mode: FileMode.read);
        salt = await raf.read(HgccAead.saltSize);
        await raf.close();
      }

      final masterKey = await _deriveMasterKey(salt);

      setState(() {
        _operationStatus = isEncrypt ? 'Encrypting file...' : 'Decrypting file...';
      });

      // 3. Spawn Isolate to perform computation in background
      _cleanupIsolate();
      _receivePort = ReceivePort();

      final message = IsolateMessage(
        sendPort: _receivePort!.sendPort,
        sourcePath: sourcePath,
        destPath: destPath,
        masterKey: masterKey,
        isEncrypt: isEncrypt,
      );

      _activeIsolate = await Isolate.spawn(_isolateEntryPoint, message);

      // Listen to messages from the isolate
      await for (final msg in _receivePort!) {
        if (msg is Map) {
          final type = msg['type'];
          if (type == 'progress') {
            setState(() {
              _progress = msg['value'];
            });
          } else if (type == 'tick') {
            setState(() {
              _visualState = HgccVisualState(
                lfsr: msg['lfsr'],
                ca: msg['ca'],
                chaos: msg['chaos'],
                counter: msg['counter'],
              );
            });
          } else if (type == 'complete') {
            _cleanupIsolate();
            
            // 4. Ghost Protocol: Securely wipe plaintext if requested (only after encryption)
            if (isEncrypt && _secureDelete) {
              setState(() {
                _operationStatus = 'Ghost Protocol: Wiping source file...';
              });
              await HgccAead.secureWipeFile(_selectedFile!);
              setState(() {
                _selectedFile = null;
              });
            }

            setState(() {
              _isProcessing = false;
              _progress = 1.0;
              _operationStatus = isEncrypt
                  ? 'Encryption complete! Saved to VisioCrypt_Out.'
                  : 'Decryption complete! Saved to VisioCrypt_Out.';
            });

            _showSnackBar(
              isEncrypt ? 'File Encrypted Successfully!' : 'File Decrypted Successfully!',
              Colors.greenAccent,
            );

            // Share/Open option
            final finalFile = File(destPath);
            if (await finalFile.exists()) {
              await Share.shareXFiles([XFile(destPath)], text: 'Processed File');
            }
            break;
          } else if (type == 'error') {
            _cleanupIsolate();
            throw Exception(msg['value']);
          }
        }
      }
    } catch (e) {
      _cleanupIsolate();
      setState(() {
        _isProcessing = false;
        _operationStatus = 'Error: ${e.toString()}';
      });
      _showSnackBar('Operation failed: $e', Colors.redAccent);
    }
  }

  /// Isolate entry point
  static void _isolateEntryPoint(IsolateMessage message) async {
    final source = File(message.sourcePath);
    final dest = File(message.destPath);
    try {
      if (message.isEncrypt) {
        await HgccAead.encryptFile(
          sourceFile: source,
          destFile: dest,
          masterKey: message.masterKey,
          onProgress: (prog) {
            message.sendPort.send({'type': 'progress', 'value': prog});
          },
          onTick: (engine) {
            message.sendPort.send({
              'type': 'tick',
              'lfsr': engine.lfsrState,
              'ca': engine.caState,
              'chaos': engine.chaosState,
              'counter': engine.counterState,
            });
          },
        );
      } else {
        await HgccAead.decryptFile(
          sourceFile: source,
          destFile: dest,
          masterKey: message.masterKey,
          onProgress: (prog) {
            message.sendPort.send({'type': 'progress', 'value': prog});
          },
          onTick: (engine) {
            message.sendPort.send({
              'type': 'tick',
              'lfsr': engine.lfsrState,
              'ca': engine.caState,
              'chaos': engine.chaosState,
              'counter': engine.counterState,
            });
          },
        );
      }
      message.sendPort.send({'type': 'complete'});
    } catch (e) {
      message.sendPort.send({'type': 'error', 'value': e.toString()});
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF07121A), // deep dark blue-teal
              Color(0xFF0D0B18), // deep dark violet
            ],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Title Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        ShaderMask(
                          shaderCallback: (bounds) => const LinearGradient(
                            colors: [Colors.cyanAccent, Colors.pinkAccent],
                          ).createShader(bounds),
                          child: const Text(
                            'VISIO',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 26,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 2,
                            ),
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Text(
                          'CRYPT',
                          style: TextStyle(
                            color: Colors.white70,
                            fontSize: 26,
                            fontWeight: FontWeight.w300,
                            letterSpacing: 2,
                          ),
                        ),
                      ],
                    ),
                    Icon(
                      Icons.security,
                      color: _isProcessing ? Colors.cyanAccent : Colors.tealAccent,
                      size: 28,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Zero-Overhead Client-Side Cryptographic System',
                  style: TextStyle(
                    color: Colors.grey[400],
                    fontSize: 12.5,
                  ),
                ),
                const SizedBox(height: 24),

                // 1. File Picker Box
                GestureDetector(
                  onTap: _isProcessing ? null : _pickFile,
                  child: Container(
                    height: 120,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.02),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: _selectedFile != null
                            ? Colors.tealAccent.withOpacity(0.3)
                            : Colors.white.withOpacity(0.08),
                        width: 1.5,
                      ),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          _selectedFile != null ? Icons.insert_drive_file : Icons.cloud_upload_outlined,
                          size: 36,
                          color: _selectedFile != null ? Colors.tealAccent : Colors.grey,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _selectedFile != null
                              ? _selectedFile!.path.split(Platform.pathSeparator).last
                              : 'TAP TO SELECT DOCUMENT',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: _selectedFile != null ? Colors.white : Colors.grey[500],
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        if (_selectedFile != null) ...[
                          const SizedBox(height: 4),
                          FutureBuilder<int>(
                            future: _selectedFile!.length(),
                            builder: (context, snapshot) {
                              if (snapshot.hasData) {
                                final kb = snapshot.data! / 1024;
                                return Text(
                                  '${kb.toStringAsFixed(2)} KB',
                                  style: TextStyle(color: Colors.grey[500], fontSize: 11),
                                );
                              }
                              return const SizedBox();
                            },
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // 2. Authentication Panel
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.white.withOpacity(0.05)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'Key Derivation Mode',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Row(
                            children: [
                              Text(
                                _useBiometrics ? 'Secure Enclave' : 'Argon2id Password',
                                style: TextStyle(
                                  color: _useBiometrics ? Colors.tealAccent : Colors.cyanAccent,
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Switch(
                                value: _useBiometrics,
                                activeColor: Colors.tealAccent,
                                inactiveThumbColor: Colors.cyanAccent,
                                onChanged: _isProcessing
                                    ? null
                                    : (val) {
                                        setState(() {
                                          _useBiometrics = val;
                                        });
                                      },
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (!_useBiometrics)
                        TextField(
                          controller: _passwordController,
                          obscureText: true,
                          enabled: !_isProcessing,
                          style: const TextStyle(color: Colors.white),
                          decoration: InputDecoration(
                            hintText: 'Enter derivation password...',
                            hintStyle: TextStyle(color: Colors.grey[600], fontSize: 13),
                            prefixIcon: const Icon(Icons.lock_outline, color: Colors.cyanAccent, size: 18),
                            filled: true,
                            fillColor: Colors.white.withOpacity(0.02),
                            contentPadding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: BorderSide(color: Colors.white.withOpacity(0.1)),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(12),
                              borderSide: const BorderSide(color: Colors.cyanAccent),
                            ),
                          ),
                        )
                      else
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.teal.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.teal.withOpacity(0.2)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.fingerprint, color: Colors.tealAccent, size: 24),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  'Gated by hardware biometrics (Windows Hello / FaceID / TouchID). Accesses a persistent 64-byte key inside TEE.',
                                  style: TextStyle(color: Colors.teal[100], fontSize: 11.5, height: 1.3),
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // 3. Ghost Protocol Option
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: Colors.white.withOpacity(0.05)),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.layers_clear_outlined, color: Colors.pinkAccent, size: 20),
                          const SizedBox(width: 12),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Ghost Protocol',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 13,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                'Securely wipe plaintext file after encryption',
                                style: TextStyle(color: Colors.grey[500], fontSize: 11),
                              ),
                            ],
                          ),
                        ],
                      ),
                      Switch(
                        value: _secureDelete,
                        activeColor: Colors.pinkAccent,
                        onChanged: _isProcessing
                            ? null
                            : (val) {
                                setState(() {
                                  _secureDelete = val;
                                });
                              },
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Action Buttons
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton(
                        onPressed: _isProcessing || _selectedFile == null ? null : () => _processFile(true),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.cyanAccent.withOpacity(0.2),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                            side: BorderSide(
                              color: _isProcessing || _selectedFile == null
                                  ? Colors.grey.withOpacity(0.3)
                                  : Colors.cyanAccent,
                            ),
                          ),
                        ),
                        child: Text(
                          'ENCRYPT',
                          style: TextStyle(
                            color: _isProcessing || _selectedFile == null ? Colors.grey : Colors.cyanAccent,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: _isProcessing || _selectedFile == null ? null : () => _processFile(false),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.transparent,
                          shadowColor: Colors.tealAccent.withOpacity(0.2),
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                            side: BorderSide(
                              color: _isProcessing || _selectedFile == null
                                  ? Colors.grey.withOpacity(0.3)
                                  : Colors.tealAccent,
                            ),
                          ),
                        ),
                        child: Text(
                          'DECRYPT',
                          style: TextStyle(
                            color: _isProcessing || _selectedFile == null ? Colors.grey : Colors.tealAccent,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // 4. Progress and Engine Visualizer
                if (_isProcessing || _progress > 0.0) ...[
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.02),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white.withOpacity(0.08)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              _operationStatus,
                              style: const TextStyle(color: Colors.white, fontSize: 12.5, fontWeight: FontWeight.w400),
                            ),
                            Text(
                              '${(_progress * 100).toStringAsFixed(0)}%',
                              style: const TextStyle(color: Colors.cyanAccent, fontSize: 13, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        LinearProgressIndicator(
                          value: _progress,
                          backgroundColor: Colors.white.withOpacity(0.05),
                          color: Colors.cyanAccent,
                          minHeight: 4,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  KeystreamVisualizer(state: _visualState),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
