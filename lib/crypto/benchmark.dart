import 'dart:typed_data';
import 'package:pointycastle/export.dart';
import 'hgcc_engine.dart';

/// Cryptographic benchmarking engine to measure empirical performance in MB/s.
class CryptoBenchmark {
  /// Benchmarks our custom HGCC Stream Cipher
  static double benchmarkHGCC(int sizeBytes) {
    final data = Uint8List(sizeBytes);
    final key = Uint8List(64); // 64-byte key
    
    final engine = HgccEngine();
    engine.init(key);

    final stopwatch = Stopwatch()..start();
    for (int i = 0; i < sizeBytes; i++) {
      final k = engine.tick();
      data[i] = data[i] ^ k;
    }
    stopwatch.stop();

    final elapsedMs = stopwatch.elapsedMilliseconds;
    final mb = sizeBytes / (1024.0 * 1024.0);
    final seconds = elapsedMs / 1000.0;
    return mb / (seconds == 0 ? 0.0001 : seconds);
  }

  /// Benchmarks PointyCastle pure-Dart AES-256 (Block Cipher)
  static double benchmarkAES256(int sizeBytes) {
    final data = Uint8List(sizeBytes);
    final key = Uint8List(32); // 256-bit key
    
    final aes = AESEngine();
    aes.init(true, KeyParameter(key));

    final outBlock = Uint8List(16);
    final stopwatch = Stopwatch()..start();
    
    // Process block-by-block (16 bytes)
    for (int i = 0; i < sizeBytes; i += 16) {
      if (i + 16 <= sizeBytes) {
        aes.processBlock(data, i, outBlock, 0);
      }
    }
    stopwatch.stop();

    final elapsedMs = stopwatch.elapsedMilliseconds;
    final mb = sizeBytes / (1024.0 * 1024.0);
    final seconds = elapsedMs / 1000.0;
    return mb / (seconds == 0 ? 0.0001 : seconds);
  }

  /// Benchmarks PointyCastle pure-Dart ChaCha20 (Stream Cipher)
  static double benchmarkChaCha20(int sizeBytes) {
    final data = Uint8List(sizeBytes);
    final key = Uint8List(32); // 256-bit key
    final nonce = Uint8List(12); // 96-bit nonce
    
    final params = ParametersWithIV(KeyParameter(key), nonce);
    final chacha = ChaCha7539Engine();
    chacha.init(true, params);

    final out = Uint8List(sizeBytes);
    final stopwatch = Stopwatch()..start();
    chacha.processBytes(data, 0, sizeBytes, out, 0);
    stopwatch.stop();

    final elapsedMs = stopwatch.elapsedMilliseconds;
    final mb = sizeBytes / (1024.0 * 1024.0);
    final seconds = elapsedMs / 1000.0;
    return mb / (seconds == 0 ? 0.0001 : seconds);
  }
}
