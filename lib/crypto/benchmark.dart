import 'dart:convert';
import 'dart:typed_data';
import 'package:pointycastle/export.dart';
import 'crypt_engine.dart';
import 'sse_engine.dart';

/// Cryptographic benchmarking engine to measure empirical performance of standard primitives and SSE indexing.
class CryptoBenchmark {
  /// Benchmarks AES-CTR-256 (our stream wrapper around AESEngine)
  static double benchmarkAesCtr(int sizeBytes) {
    final data = Uint8List(sizeBytes);
    final key = Uint8List(32); // 256-bit key
    final iv = Uint8List(16);  // 128-bit IV
    
    final engine = AesCtrEngine();
    engine.init(key, iv);

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

  /// Benchmarks PointyCastle pure-Dart AES-GCM-256 (Authenticated Block Cipher)
  static double benchmarkAesGcm(int sizeBytes) {
    final data = Uint8List(sizeBytes);
    final key = Uint8List(32); // 256-bit key
    final iv = Uint8List(12);  // 96-bit GCM IV
    
    final stopwatch = Stopwatch()..start();
    final encrypted = SseEngine.encryptGcm(key, iv, data);
    stopwatch.stop();

    final elapsedMs = stopwatch.elapsedMilliseconds;
    final mb = sizeBytes / (1024.0 * 1024.0);
    final seconds = elapsedMs / 1000.0;
    return mb / (seconds == 0 ? 0.0001 : seconds);
  }

  /// Benchmarks the latency of building and encrypting an SSE index with 1,000 keywords
  static double benchmarkSseIndexing() {
    final keywords = List.generate(1000, (i) => 'keyword$i').toSet();
    final key = Uint8List(64);
    final salt = Uint8List(16);
    
    // Simulate SSE keys derivation
    final sseKeys = SseEngine.deriveSseKeys(key, salt);
    final kSearch = sseKeys['kSearch']!;
    final kIndexVal = sseKeys['kIndexVal']!;

    final stopwatch = Stopwatch()..start();
    
    // Mock SSE Index Database
    final Map<String, List<String>> mockDb = {};
    for (final word in keywords) {
      final trapdoor = SseEngine.computeTrapdoor(word, kSearch);
      mockDb[trapdoor] = ['doc1.txt', 'doc2.txt'];
    }

    // Encrypt the lookup table
    for (final entry in mockDb.entries) {
      final iv = Uint8List(12);
      final plainBytes = utf8.encode(json.encode(entry.value));
      SseEngine.encryptGcm(kIndexVal, iv, Uint8List.fromList(plainBytes));
    }

    stopwatch.stop();
    return stopwatch.elapsedMicroseconds / 1000.0; // returns milliseconds for 1000 words
  }

  /// Benchmarks Trapdoor generation rate (HMAC evaluations per millisecond)
  static double benchmarkSseTrapdoor() {
    final key = Uint8List(32);
    final stopwatch = Stopwatch()..start();
    int iterations = 10000;
    
    for (int i = 0; i < iterations; i++) {
      SseEngine.computeTrapdoor('searchterm$i', key);
    }
    
    stopwatch.stop();
    final ms = stopwatch.elapsedMilliseconds;
    return iterations / (ms == 0 ? 0.0001 : ms); // Trapdoors generated per millisecond
  }
}
