import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:convert/convert.dart';
import 'package:pointycastle/export.dart' hide Digest;
import 'hkdf.dart';

/// AES-CTR-256 stream engine using PointyCastle's core AES block cipher.
class AesCtrEngine {
  final AESEngine _aes = AESEngine();
  late Uint8List _counter;
  final Uint8List _keystreamBuffer = Uint8List(16);
  int _keystreamIdx = 16;

  void init(Uint8List key, Uint8List iv) {
    if (key.length != 32) {
      throw ArgumentError('AES-256 key must be 32 bytes.');
    }
    if (iv.length != 16) {
      throw ArgumentError('AES IV must be 16 bytes.');
    }
    _aes.init(true, KeyParameter(key));
    _counter = Uint8List.fromList(iv);
    _keystreamIdx = 16; // Force initial keystream generation block
  }

  int tick() {
    if (_keystreamIdx == 16) {
      _aes.processBlock(_counter, 0, _keystreamBuffer, 0);
      
      // Increment 128-bit big-endian counter
      for (int i = 15; i >= 0; i--) {
        _counter[i]++;
        if (_counter[i] != 0) break;
      }
      _keystreamIdx = 0;
    }
    return _keystreamBuffer[_keystreamIdx++];
  }
}

/// Standard Authenticated Encryption with Associated Data (AEAD) implementation.
/// Implements Encrypt-then-MAC (EtM) with AES-CTR-256, HMAC-SHA256, and Ghost Protocol.
class CryptEngine {
  static const int saltSize = 16;
  static const int tagSize = 32; // HMAC-SHA256 tag size
  static const int chunkSize = 65536; // 64 KB chunks

  static Uint8List generateSalt() {
    final rand = Random.secure();
    final bytes = Uint8List(saltSize);
    for (int i = 0; i < saltSize; i++) {
      bytes[i] = rand.nextInt(256);
    }
    return bytes;
  }

  static bool safeEquals(Uint8List a, Uint8List b) {
    if (a.length != b.length) return false;
    int result = 0;
    for (int i = 0; i < a.length; i++) {
      result |= a[i] ^ b[i];
    }
    return result == 0;
  }

  /// Encrypts a file using AES-CTR-256 and HMAC-SHA256.
  /// Output format: [16-byte Salt] [Ciphertext] [32-byte HMAC Tag]
  static Future<void> encryptFile({
    required File sourceFile,
    required File destFile,
    required Uint8List masterKey,
    Function(double progress)? onProgress,
  }) async {
    if (!await sourceFile.exists()) {
      throw FileSystemException('Source file does not exist', sourceFile.path);
    }

    final salt = generateSalt();

    // Derive Kenc, IV, and Kmac
    final hkdf = Hkdf(sha256);
    final prk = hkdf.extract(salt, masterKey);
    final kEnc = hkdf.expand(prk, utf8.encode('VisioCrypt-AES-Key'), 32);
    final iv = hkdf.expand(prk, utf8.encode('VisioCrypt-AES-IV'), 16);
    final kMac = hkdf.expand(prk, utf8.encode('VisioCrypt-MAC-Key'), 32);

    final engine = AesCtrEngine();
    engine.init(kEnc, iv);

    final hmacInputSink = AccumulatorSink<Digest>();
    final hmacInstance = Hmac(sha256, kMac);
    final hmacByteSink = hmacInstance.startChunkedConversion(hmacInputSink);

    hmacByteSink.add(salt);

    final sourceStream = sourceFile.openRead();
    final totalBytes = await sourceFile.length();
    int processedBytes = 0;

    if (!await destFile.parent.exists()) {
      await destFile.parent.create(recursive: true);
    }
    final destSink = destFile.openWrite(mode: FileMode.write);
    destSink.add(salt);

    await for (final chunk in sourceStream) {
      final encryptedChunk = Uint8List(chunk.length);
      for (int i = 0; i < chunk.length; i++) {
        encryptedChunk[i] = chunk[i] ^ engine.tick();
      }

      destSink.add(encryptedChunk);
      hmacByteSink.add(encryptedChunk);

      processedBytes += chunk.length;
      if (onProgress != null && totalBytes > 0) {
        onProgress(processedBytes / totalBytes);
      }
    }

    hmacByteSink.close();
    final hmacTag = hmacInputSink.events.single.bytes;
    destSink.add(hmacTag);

    await destSink.flush();
    await destSink.close();
  }

  /// Decrypts a file using AES-CTR-256 and verifies HMAC-SHA256 integrity.
  static Future<void> decryptFile({
    required File sourceFile,
    required File destFile,
    required Uint8List masterKey,
    Function(double progress)? onProgress,
  }) async {
    if (!await sourceFile.exists()) {
      throw FileSystemException('Source file does not exist', sourceFile.path);
    }

    final totalSourceBytes = await sourceFile.length();
    if (totalSourceBytes < saltSize + tagSize) {
      throw ArgumentError('Encrypted file is too short (corrupted).');
    }

    final ciphertextLength = totalSourceBytes - saltSize - tagSize;

    final randomAccess = await sourceFile.open(mode: FileMode.read);
    final salt = await randomAccess.read(saltSize);
    await randomAccess.close();

    // Derive keys
    final hkdf = Hkdf(sha256);
    final prk = hkdf.extract(salt, masterKey);
    final kEnc = hkdf.expand(prk, utf8.encode('VisioCrypt-AES-Key'), 32);
    final iv = hkdf.expand(prk, utf8.encode('VisioCrypt-AES-IV'), 16);
    final kMac = hkdf.expand(prk, utf8.encode('VisioCrypt-MAC-Key'), 32);

    // Verify tag
    final hmacInputSink = AccumulatorSink<Digest>();
    final hmacInstance = Hmac(sha256, kMac);
    final hmacByteSink = hmacInstance.startChunkedConversion(hmacInputSink);

    hmacByteSink.add(salt);

    final verificationStream = sourceFile.openRead(saltSize, totalSourceBytes - tagSize);
    await for (final chunk in verificationStream) {
      hmacByteSink.add(chunk);
    }
    hmacByteSink.close();
    final computedTag = Uint8List.fromList(hmacInputSink.events.single.bytes);

    final randomAccessForTag = await sourceFile.open(mode: FileMode.read);
    await randomAccessForTag.setPosition(totalSourceBytes - tagSize);
    final storedTag = await randomAccessForTag.read(tagSize);
    await randomAccessForTag.close();

    if (!safeEquals(computedTag, storedTag)) {
      throw SecurityException('Integrity check failed: invalid HMAC signature (ciphertext was modified).');
    }

    final engine = AesCtrEngine();
    engine.init(kEnc, iv);

    if (!await destFile.parent.exists()) {
      await destFile.parent.create(recursive: true);
    }
    final destSink = destFile.openWrite(mode: FileMode.write);

    final ciphertextStream = sourceFile.openRead(saltSize, totalSourceBytes - tagSize);
    int processedBytes = 0;

    await for (final chunk in ciphertextStream) {
      final decryptedChunk = Uint8List(chunk.length);
      for (int i = 0; i < chunk.length; i++) {
        decryptedChunk[i] = chunk[i] ^ engine.tick();
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
    final zeroChunk = Uint8List(chunkSize);
    
    final randomAccess = await file.open(mode: FileMode.write);
    int bytesWritten = 0;
    
    while (bytesWritten < length) {
      final toWrite = min(chunkSize, length - bytesWritten);
      await randomAccess.writeFrom(zeroChunk, 0, toWrite);
      bytesWritten += toWrite;
    }
    
    await randomAccess.flush();
    await randomAccess.close();
    await file.delete();
  }
}

class SecurityException implements Exception {
  final String message;
  SecurityException(this.message);

  @override
  String toString() => 'SecurityException: $message';
}
