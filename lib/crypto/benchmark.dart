import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';
import 'crypt_engine.dart';
import 'sse_engine.dart';

/// Cryptographic benchmarking engine to measure empirical performance of standard primitives,
/// dynamic forward/backward private SSE indexing, and volume-hiding candidate padding.
class CryptoBenchmark {
  /// Benchmarks AES-CTR-256 stream encryption throughput (MB/s)
  static double benchmarkAesCtr(int sizeBytes) {
    final data = Uint8List(sizeBytes);
    final key = Uint8List(32);
    final iv = Uint8List(16);
    
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

  /// Benchmarks PointyCastle AES-GCM-256 authenticated throughput (MB/s)
  static double benchmarkAesGcm(int sizeBytes) {
    final data = Uint8List(sizeBytes);
    final key = Uint8List(32);
    final iv = Uint8List(12);
    
    final stopwatch = Stopwatch()..start();
    SseEngine.encryptGcm(key, iv, data);
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
    
    final sseKeys = SseEngine.deriveSseKeys(key, salt);
    final kSearch = sseKeys['kSearch']!;
    final kIndexVal = sseKeys['kIndexVal']!;

    final stopwatch = Stopwatch()..start();
    
    final Map<String, List<String>> mockDb = {};
    for (final word in keywords) {
      final trapdoor = SseEngine.computeTrapdoor(word, kSearch);
      mockDb[trapdoor] = ['doc1.txt', 'doc2.txt'];
    }

    for (final entry in mockDb.entries) {
      final iv = Uint8List(12);
      final padded = SseEngine.padFileList(entry.value);
      final plainBytes = utf8.encode(json.encode(padded));
      SseEngine.encryptGcm(kIndexVal, iv, Uint8List.fromList(plainBytes));
    }

    stopwatch.stop();
    return stopwatch.elapsedMicroseconds / 1000.0;
  }

  /// Benchmarks Trapdoor generation rate (evaluations per millisecond)
  static double benchmarkSseTrapdoor() {
    final key = Uint8List(32);
    final stopwatch = Stopwatch()..start();
    int iterations = 10000;
    
    for (int i = 0; i < iterations; i++) {
      SseEngine.computeTrapdoor('searchterm$i', key);
    }
    
    stopwatch.stop();
    final ms = stopwatch.elapsedMilliseconds;
    return iterations / (ms == 0 ? 0.0001 : ms);
  }

  /// Benchmarks Bloom Filter verification throughput (operations per millisecond)
  static double benchmarkBloomFilter() {
    final filter = SseBloomFilter(bitSize: 8192, numHashFunctions: 4);
    for (int i = 0; i < 500; i++) {
      filter.add('keyword$i::deleted_doc$i.pdf');
    }

    final stopwatch = Stopwatch()..start();
    int lookups = 20000;
    for (int i = 0; i < lookups; i++) {
      filter.mightContain('keyword${i % 1000}::test_doc$i.pdf');
    }
    stopwatch.stop();
    final ms = stopwatch.elapsedMilliseconds;
    return lookups / (ms == 0 ? 0.0001 : ms);
  }

  /// Benchmarks simulated SQLCipher B-Tree page traversal query latency
  static double benchmarkSqlCipherQuery(int databaseSize) {
    final key = Uint8List(32);
    final iv = Uint8List(12);
    final dummyPage = Uint8List(4096);
    
    final int pageReads = databaseSize > 1 ? (log(databaseSize) / ln2).ceil() : 1;

    final stopwatch = Stopwatch()..start();
    for (int i = 0; i < pageReads; i++) {
      SseEngine.decryptGcm(key, iv, dummyPage);
    }
    stopwatch.stop();
    return stopwatch.elapsedMicroseconds / 1000.0;
  }
}
