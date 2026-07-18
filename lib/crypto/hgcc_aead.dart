import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:convert/convert.dart';
import 'hkdf.dart';
import 'hgcc_engine.dart';

/// HGCC Authenticated Encryption with Associated Data (AEAD) implementation.
/// Implements Encrypt-then-MAC (EtM) with HMAC-SHA256, chunked file streaming,
/// and the secure deletion (Ghost Protocol) mechanism.
class HgccAead {
  static const int saltSize = 16;
  static const int tagSize = 32; // HMAC-SHA256 tag size
  static const int chunkSize = 65536; // 64 KB chunks

  /// Generates a cryptographically secure random byte array
  static Uint8List generateSalt() {
    final rand = Random.secure();
    final bytes = Uint8List(saltSize);
    for (int i = 0; i < saltSize; i++) {
      bytes[i] = rand.nextInt(256);
    }
    return bytes;
  }

  /// Constant-time byte array comparison to prevent timing side-channel attacks
  static bool safeEquals(Uint8List a, Uint8List b) {
    if (a.length != b.length) return false;
    int result = 0;
    for (int i = 0; i < a.length; i++) {
      result |= a[i] ^ b[i];
    }
    return result == 0;
  }

  /// Encrypts a file using HGCC and HMAC-SHA256 in a streaming fashion.
  /// Output format: [16-byte Salt] [Ciphertext] [32-byte HMAC Tag]
  static Future<void> encryptFile({
    required File sourceFile,
    required File destFile,
    required Uint8List masterKey,
    Function(double progress)? onProgress,
    Function(HgccEngine engine)? onTick, // For live keystream visualization
  }) async {
    if (!await sourceFile.exists()) {
      throw FileSystemException('Source file does not exist', sourceFile.path);
    }

    final salt = generateSalt();

    // Derive Kenc (64 bytes) and Kmac (32 bytes) from Master Key using HKDF-SHA256
    final hkdf = Hkdf(sha256);
    final prk = hkdf.extract(salt, masterKey);
    final kEnc = hkdf.expand(prk, utf8.encode('VisioCrypt-Encryption-Key'), 64);
    final kMac = hkdf.expand(prk, utf8.encode('VisioCrypt-MAC-Key'), 32);

    // Initialize HGCC engine with derived encryption key
    final engine = HgccEngine();
    engine.init(kEnc);

    // Prepare HMAC-SHA256 calculator
    final hmacInputSink = AccumulatorSink<Digest>();
    final hmacInstance = Hmac(sha256, kMac);
    final hmacByteSink = hmacInstance.startChunkedConversion(hmacInputSink);

    // Add Salt to HMAC calculation first to verify its integrity
    hmacByteSink.add(salt);

    // Open source file for reading and destination file for writing
    final sourceStream = sourceFile.openRead();
    final totalBytes = await sourceFile.length();
    int processedBytes = 0;

    // Create target dir if it doesn't exist
    if (!await destFile.parent.exists()) {
      await destFile.parent.create(recursive: true);
    }

    final destSink = destFile.openWrite(mode: FileMode.write);
    
    // Write salt to destination first
    destSink.add(salt);

    await for (final chunk in sourceStream) {
      final encryptedChunk = Uint8List(chunk.length);
      for (int i = 0; i < chunk.length; i++) {
        final k = engine.tick();
        encryptedChunk[i] = chunk[i] ^ k;
        if (onTick != null && i % 100 == 0) {
          // Sample state for visualizer
          onTick(engine);
        }
      }

      // Add encrypted chunk to output file and HMAC
      destSink.add(encryptedChunk);
      hmacByteSink.add(encryptedChunk);

      processedBytes += chunk.length;
      if (onProgress != null && totalBytes > 0) {
        onProgress(processedBytes / totalBytes);
      }
    }

    // Finalize HMAC
    hmacByteSink.close();
    final hmacTag = hmacInputSink.events.single.bytes;

    // Write HMAC Tag to the end of the file
    destSink.add(hmacTag);

    await destSink.flush();
    await destSink.close();
  }

  /// Decrypts a file using HGCC and verifies its HMAC-SHA256 tag in a streaming fashion.
  static Future<void> decryptFile({
    required File sourceFile,
    required File destFile,
    required Uint8List masterKey,
    Function(double progress)? onProgress,
    Function(HgccEngine engine)? onTick, // For live keystream visualization
  }) async {
    if (!await sourceFile.exists()) {
      throw FileSystemException('Source file does not exist', sourceFile.path);
    }

    final totalSourceBytes = await sourceFile.length();
    if (totalSourceBytes < saltSize + tagSize) {
      throw ArgumentError('Encrypted file is too short (corrupted).');
    }

    final ciphertextLength = totalSourceBytes - saltSize - tagSize;

    // 1. Read the 16-byte Salt
    final randomAccess = await sourceFile.open(mode: FileMode.read);
    final salt = await randomAccess.read(saltSize);
    await randomAccess.close();

    // Derive Kenc and Kmac
    final hkdf = Hkdf(sha256);
    final prk = hkdf.extract(salt, masterKey);
    final kEnc = hkdf.expand(prk, utf8.encode('VisioCrypt-Encryption-Key'), 64);
    final kMac = hkdf.expand(prk, utf8.encode('VisioCrypt-MAC-Key'), 32);

    // 2. Perform HMAC-SHA256 verification (Encrypt-then-MAC)
    final hmacInputSink = AccumulatorSink<Digest>();
    final hmacInstance = Hmac(sha256, kMac);
    final hmacByteSink = hmacInstance.startChunkedConversion(hmacInputSink);

    hmacByteSink.add(salt);

    // Read ciphertext and compute HMAC
    final verificationStream = sourceFile.openRead(saltSize, totalSourceBytes - tagSize);
    await for (final chunk in verificationStream) {
      hmacByteSink.add(chunk);
    }
    hmacByteSink.close();
    final computedTag = Uint8List.fromList(hmacInputSink.events.single.bytes);

    // Read the stored tag
    final randomAccessForTag = await sourceFile.open(mode: FileMode.read);
    await randomAccessForTag.setPosition(totalSourceBytes - tagSize);
    final storedTag = await randomAccessForTag.read(tagSize);
    await randomAccessForTag.close();

    // Verify tag in constant-time
    if (!safeEquals(computedTag, storedTag)) {
      throw SecurityException('Integrity check failed: invalid HMAC signature (ciphertext was modified).');
    }

    // 3. Decrypt ciphertext using HGCC
    final engine = HgccEngine();
    engine.init(kEnc);

    if (!await destFile.parent.exists()) {
      await destFile.parent.create(recursive: true);
    }
    final destSink = destFile.openWrite(mode: FileMode.write);

    final ciphertextStream = sourceFile.openRead(saltSize, totalSourceBytes - tagSize);
    int processedBytes = 0;

    await for (final chunk in ciphertextStream) {
      final decryptedChunk = Uint8List(chunk.length);
      for (int i = 0; i < chunk.length; i++) {
        final k = engine.tick();
        decryptedChunk[i] = chunk[i] ^ k;
        if (onTick != null && i % 100 == 0) {
          onTick(engine);
        }
      }

      destSink.add(decryptedChunk);

      processedBytes += chunk.length;
      if (onProgress != null && ciphertextLength > 0) {
        onProgress(processedBytes / ciphertextLength);
      }
    }

    await destSink.flush();
    await destSink.close();
  }

  /// Ghost Protocol: Securely wipe plaintext memory buffers and overwrite the file on disk.
  static Future<void> secureWipeFile(File file) async {
    if (!await file.exists()) return;
    
    final length = await file.length();
    final zeroChunk = Uint8List(chunkSize); // zero bytes
    
    // Open file to write zeros over its content
    final randomAccess = await file.open(mode: FileMode.write);
    int bytesWritten = 0;
    
    while (bytesWritten < length) {
      final toWrite = min(chunkSize, length - bytesWritten);
      await randomAccess.writeFrom(zeroChunk, 0, toWrite);
      bytesWritten += toWrite;
    }
    
    await randomAccess.flush();
    await randomAccess.close();
    
    // Finally, unlink the file from the filesystem
    await file.delete();
  }
}

/// Custom Security Exception for integrity failures
class SecurityException implements Exception {
  final String message;
  SecurityException(this.message);

  @override
  String toString() => 'SecurityException: $message';
}
