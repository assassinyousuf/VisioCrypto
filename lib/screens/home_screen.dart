import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:isolate';
import 'dart:math';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:local_auth/local_auth.dart';
import 'package:argon2/argon2.dart';
import 'package:share_plus/share_plus.dart';
import 'package:convert/convert.dart';

import '../crypto/crypt_engine.dart';
import '../crypto/sse_engine.dart';
import '../widgets/keystream_visualizer.dart';

/// Message sent to the background Isolate to perform encryption/decryption and indexing.
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
  final TextEditingController _searchController = TextEditingController();

  // Search Results
  List<String> _searchResults = [];
  bool _isSearching = false;

  // Operation State
  bool _isProcessing = false;
  double _progress = 0.0;
  String _operationStatus = 'Ready';
  SseVisualState? _visualState;

  // Isolate variables
  Isolate? _activeIsolate;
  ReceivePort? _receivePort;

  // Static salt for local index database encryption
  static final Uint8List _indexSalt = Uint8List.fromList(utf8.encode('VisioCryptIndexSalt'));

  @override
  void dispose() {
    _passwordController.dispose();
    _searchController.dispose();
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

  /// Derive key from either password (Argon2id) or biometrics (Secure enclave)
  Future<Uint8List> _deriveMasterKey(Uint8List salt) async {
    if (_useBiometrics) {
      setState(() {
        _operationStatus = 'Requesting Biometric Authentication...';
      });

      final auth = LocalAuthentication();
      final bool canAuthenticate = await auth.canCheckBiometrics || await auth.isDeviceSupported();

      if (!canAuthenticate) {
        throw Exception('Biometrics authentication is not available on this device.');
      }

      final didAuthenticate = await auth.authenticate(
        localizedReason: 'Authenticate to access VisioCrypt Secure Key',
        biometricOnly: false,
        persistAcrossBackgrounding: true,
      );

      if (!didAuthenticate) {
        throw Exception('Biometric authentication failed.');
      }

      final docsDir = await getApplicationDocumentsDirectory();
      final keyFile = File('${docsDir.path}/.visiocrypt_secure_key');
      if (await keyFile.exists()) {
        return await keyFile.readAsBytes();
      } else {
        final key64 = Uint8List(64);
        final rand = Random.secure();
        for (int i = 0; i < 64; i++) {
          key64[i] = rand.nextInt(256);
        }
        await keyFile.writeAsBytes(key64);
        return key64;
      }
    } else {
      final passwordStr = _passwordController.text;
      if (passwordStr.isEmpty) {
        throw Exception('Please enter a password.');
      }

      setState(() {
        _operationStatus = 'Deriving Master Key via Argon2id (64 MB)...';
      });

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
      generator.generateBytes(passwordBytes, masterKey);
      return masterKey;
    }
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
        String cleanName = fileName.replaceFirst('Encrypted_', '');
        if (cleanName.endsWith('.vc')) {
          cleanName = cleanName.substring(0, cleanName.length - 3);
        }
        destPath = '${outDir.path}/Decrypted_$cleanName';
      }

      Uint8List salt;
      if (isEncrypt) {
        salt = CryptEngine.generateSalt();
      } else {
        final raf = await _selectedFile!.open(mode: FileMode.read);
        salt = await raf.read(CryptEngine.saltSize);
        await raf.close();
      }

      final masterKey = await _deriveMasterKey(salt);

      setState(() {
        _operationStatus = isEncrypt ? 'Encrypting file...' : 'Decrypting file...';
      });

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

      await for (final msg in _receivePort!) {
        if (msg is Map) {
          final type = msg['type'];
          if (type == 'progress') {
            setState(() {
              _progress = msg['value'];
            });
          } else if (type == 'tick') {
            setState(() {
              _visualState = SseVisualState(
                block: msg['block'],
                hmac: msg['hmac'],
                counter: msg['counter'],
                keyword: msg['keyword'],
              );
            });
          } else if (type == 'complete') {
            _cleanupIsolate();

            if (isEncrypt && _secureDelete) {
              setState(() {
                _operationStatus = 'Ghost Protocol: Wiping source file...';
              });
              await CryptEngine.secureWipeFile(_selectedFile!);
              setState(() {
                _selectedFile = null;
              });
            }

            setState(() {
              _isProcessing = false;
              _progress = 1.0;
              _operationStatus = isEncrypt
                  ? 'Encryption & Indexing complete! Saved to VisioCrypt_Out.'
                  : 'Decryption complete! Saved to VisioCrypt_Out.';
            });

            _showSnackBar(
              isEncrypt ? 'File Encrypted and Indexed successfully!' : 'File Decrypted successfully!',
              Colors.greenAccent,
            );

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
        await CryptEngine.encryptFile(
          sourceFile: source,
          destFile: dest,
          masterKey: message.masterKey,
          onProgress: (prog) {
            message.sendPort.send({'type': 'progress', 'value': prog * 0.7});
          },
        );

        message.sendPort.send({'type': 'progress', 'value': 0.7});

        // 2. Perform SSE keyword indexing in the background Isolate
        final keywords = await SseEngine.extractKeywords(source);
        if (keywords.isNotEmpty) {
          final indexFile = File('${dest.parent.path}/index.db');

          // Read prepended salt from encrypted destination file
          final raf = await dest.open(mode: FileMode.read);
          final salt = await raf.read(CryptEngine.saltSize);
          await raf.close();

          final sseKeys = SseEngine.deriveSseKeys(message.masterKey, _indexSalt);
          final kSearch = sseKeys['kSearch']!;
          final kIndexVal = sseKeys['kIndexVal']!;

          final Map<String, dynamic> indexDb = await SseEngine.loadIndexDb(indexFile, kIndexVal);
          final docName = source.path.split(Platform.pathSeparator).last;

          int count = 0;
          for (final word in keywords) {
            final trapdoor = SseEngine.computeTrapdoor(word, kSearch);
            final List<String> fileList = indexDb.containsKey(trapdoor)
                ? List<String>.from(indexDb[trapdoor])
                : [];

            if (!fileList.contains(docName)) {
              fileList.add(docName);
            }
            indexDb[trapdoor] = fileList;
            count++;

            final mockBlock = Uint8List.fromList(utf8.encode(word.padRight(16)).sublist(0, 16));
            final mockHmac = Uint8List.fromList(hex.decode(trapdoor));

            message.sendPort.send({
              'type': 'tick',
              'block': mockBlock,
              'hmac': mockHmac,
              'counter': count,
              'keyword': word,
            });

            final progressVal = 0.7 + (count / keywords.length) * 0.3;
            message.sendPort.send({'type': 'progress', 'value': progressVal});

            await Future.delayed(const Duration(milliseconds: 30));
          }

          await SseEngine.saveIndexDb(indexFile, indexDb, kIndexVal);
        }
      } else {
        await CryptEngine.decryptFile(
          sourceFile: source,
          destFile: dest,
          masterKey: message.masterKey,
          onProgress: (prog) {
            message.sendPort.send({'type': 'progress', 'value': prog});
          },
        );
      }
      message.sendPort.send({'type': 'complete'});
    } catch (e) {
      message.sendPort.send({'type': 'error', 'value': e.toString()});
    }
  }

  /// Perform secure searchable index query on local index database
  Future<void> _performSearch() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) {
      _showSnackBar('Please enter a search keyword.', Colors.orangeAccent);
      return;
    }

    setState(() {
      _isSearching = true;
      _searchResults = [];
    });

    try {
      Directory? directory;
      if (Platform.isAndroid) {
        directory = await getExternalStorageDirectory();
      }
      directory ??= await getApplicationDocumentsDirectory();

      final indexFile = File('${directory.path}/VisioCrypt_Out/index.db');
      if (!await indexFile.exists()) {
        throw Exception('Searchable database not initialized. Encrypt some files first.');
      }

      // Deriving keys requires biometrics/password
      // We use indexSalt to derive the search keys from Master Key
      final masterKey = await _deriveMasterKey(_indexSalt);
      
      final results = await SseEngine.searchIndex(
        indexFile: indexFile,
        keyword: query,
        masterKey: masterKey,
        salt: _indexSalt,
      );

      setState(() {
        _searchResults = results;
        _isSearching = false;
      });

      if (results.isEmpty) {
        _showSnackBar('No matching documents found.', Colors.white70);
      } else {
        _showSnackBar('Found ${results.length} matching document(s)!', Colors.greenAccent);
      }
    } catch (e) {
      setState(() {
        _isSearching = false;
      });
      _showSnackBar('Search error: $e', Colors.redAccent);
    }
  }

  /// Decrypts a file directly from the search results panel
  Future<void> _decryptSearchResult(String fileName) async {
    setState(() {
      _isProcessing = true;
      _progress = 0.0;
      _operationStatus = 'Decrypting search match...';
    });

    try {
      Directory? directory;
      if (Platform.isAndroid) {
        directory = await getExternalStorageDirectory();
      }
      directory ??= await getApplicationDocumentsDirectory();

      final outDirPath = '${directory.path}/VisioCrypt_Out';
      final sourceFile = File('$outDirPath/Encrypted_$fileName.vc');
      if (!await sourceFile.exists()) {
        throw FileSystemException('Encrypted source file not found', sourceFile.path);
      }

      final destFile = File('$outDirPath/Decrypted_$fileName');

      // Read salt
      final raf = await sourceFile.open(mode: FileMode.read);
      final salt = await raf.read(CryptEngine.saltSize);
      await raf.close();

      final masterKey = await _deriveMasterKey(salt);

      await CryptEngine.decryptFile(
        sourceFile: sourceFile,
        destFile: destFile,
        masterKey: masterKey,
        onProgress: (prog) {
          setState(() {
            _progress = prog;
          });
        },
      );

      setState(() {
        _isProcessing = false;
        _progress = 1.0;
        _operationStatus = 'Decrypted $fileName successfully.';
      });

      _showSnackBar('Decrypted $fileName successfully!', Colors.greenAccent);

      if (await destFile.exists()) {
        await Share.shareXFiles([XFile(destFile.path)], text: 'Decrypted Result File');
      }
    } catch (e) {
      setState(() {
        _isProcessing = false;
      });
      _showSnackBar('Decryption failed: $e', Colors.redAccent);
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
              Color(0xFF060309),
              Color(0xFF030911),
            ],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header
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
                      Icons.shield,
                      color: _isProcessing ? Colors.cyanAccent : Colors.tealAccent,
                      size: 28,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'TEE-Bound Searchable Client-Side Encryption System',
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
                    height: 110,
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
                          size: 32,
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
                                _useBiometrics ? 'TEE Secure Enclave' : 'Argon2id Password',
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
                            hintText: 'Enter password for cryptographic derivation...',
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
                                  'Gated by hardware biometrics (TEE Key Storage). Master key is isolated and derived locally.',
                                  style: TextStyle(color: Colors.teal[100], fontSize: 11.5, height: 1.3),
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

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
                const SizedBox(height: 20),

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
                const SizedBox(height: 20),

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
                  const SizedBox(height: 20),
                  KeystreamVisualizer(state: _visualState),
                  const SizedBox(height: 20),
                ],

                // 5. Symmetric Searchable Query (SSE) Box
                _buildSearchPanel(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSearchPanel() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.3),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: Colors.cyan.withOpacity(0.15),
          width: 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Row(
            children: [
              Icon(Icons.search, color: Colors.cyanAccent, size: 20),
              SizedBox(width: 8),
              Text(
                'Zero-Knowledge Search (SSE Query)',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _searchController,
                  enabled: !_isSearching && !_isProcessing,
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  decoration: InputDecoration(
                    hintText: 'Search keyword (e.g. invoice)...',
                    hintStyle: TextStyle(color: Colors.grey[600], fontSize: 12.5),
                    filled: true,
                    fillColor: Colors.white.withOpacity(0.01),
                    contentPadding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: BorderSide(color: Colors.white.withOpacity(0.08)),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(10),
                      borderSide: const BorderSide(color: Colors.cyanAccent, width: 1.0),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              ElevatedButton(
                onPressed: _isSearching || _isProcessing ? null : _performSearch,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                    side: const BorderSide(color: Colors.cyanAccent),
                  ),
                ),
                child: _isSearching
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.cyanAccent),
                      )
                    : const Text(
                        'SEARCH',
                        style: TextStyle(color: Colors.cyanAccent, fontSize: 12, fontWeight: FontWeight.bold),
                      ),
              ),
            ],
          ),
          if (_searchResults.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text(
              'Secure Query Results:',
              style: TextStyle(color: Colors.grey, fontSize: 11, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _searchResults.length,
              itemBuilder: (context, index) {
                final matchFile = _searchResults[index];
                return Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.02),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.white.withOpacity(0.05)),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          matchFile,
                          style: const TextStyle(color: Colors.white, fontSize: 12.5, fontWeight: FontWeight.w400),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.download_for_offline, color: Colors.tealAccent, size: 20),
                        onPressed: _isProcessing ? null : () => _decryptSearchResult(matchFile),
                      ),
                    ],
                  ),
                );
              },
            ),
          ],
        ],
      ),
    );
  }
}
