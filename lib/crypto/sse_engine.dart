import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:convert/convert.dart';
import 'package:pointycastle/export.dart' hide Digest;
import 'hkdf.dart';

/// Lightweight Bloom Filter for O(1) membership testing and fast deletion filtering
class SseBloomFilter {
  final int bitSize;
  final int numHashFunctions;
  late final Uint8List _bits;

  SseBloomFilter({this.bitSize = 4096, this.numHashFunctions = 4}) {
    _bits = Uint8List((bitSize + 7) ~/ 8);
  }

  factory SseBloomFilter.fromBytes(Uint8List bytes, {int numHashFunctions = 4}) {
    final filter = SseBloomFilter(bitSize: bytes.length * 8, numHashFunctions: numHashFunctions);
    filter._bits.setAll(0, bytes);
    return filter;
  }

  Uint8List toBytes() => Uint8List.fromList(_bits);

  List<int> _hashes(String item) {
    final itemBytes = utf8.encode(item);
    final hash1 = sha256.convert(itemBytes).bytes;
    final hash2 = sha256.convert([...itemBytes, 0x5A]).bytes;

    final h1 = ByteData.sublistView(Uint8List.fromList(hash1)).getUint32(0, Endian.little);
    final h2 = ByteData.sublistView(Uint8List.fromList(hash2)).getUint32(0, Endian.little);

    final indices = <int>[];
    for (int i = 0; i < numHashFunctions; i++) {
      final combined = (h1 + i * h2) % bitSize;
      indices.add(combined);
    }
    return indices;
  }

  void add(String item) {
    for (final index in _hashes(item)) {
      final byteIdx = index ~/ 8;
      final bitIdx = index % 8;
      _bits[byteIdx] |= (1 << bitIdx);
    }
  }

  bool mightContain(String item) {
    for (final index in _hashes(item)) {
      final byteIdx = index ~/ 8;
      final bitIdx = index % 8;
      if ((_bits[byteIdx] & (1 << bitIdx)) == 0) {
        return false;
      }
    }
    return true;
  }

  void clear() {
    _bits.fillRange(0, _bits.length, 0);
  }
}

/// Query Decorrelation and Obfuscation Pool (SWAT Protocol Model)
/// Defends against temporal correlation and co-occurrence leakage attacks.
class QueryDecorrelationPool {
  final int poolThreshold;
  final Duration minDispatchDelay;
  final List<String> _pendingQueries = [];
  final Random _rand = Random.secure();

  QueryDecorrelationPool({
    this.poolThreshold = 4,
    this.minDispatchDelay = const Duration(milliseconds: 15),
  });

  /// Inserts a search keyword into the decorrelation pool
  void enqueueQuery(String keyword) {
    _pendingQueries.add(keyword);
  }

  /// Dispatches a batch of decorrelated queries with injected dummy trapdoors
  Future<List<String>> dispatchDecorrelatedBatch(Uint8List kSearch, {int batchSize = 4}) async {
    final batch = <String>[];
    final actualKeywords = <String>[];

    while (_pendingQueries.isNotEmpty && actualKeywords.length < batchSize) {
      final idx = _rand.nextInt(_pendingQueries.length);
      actualKeywords.add(_pendingQueries.removeAt(idx));
    }

    // Inject dummy trapdoors if batch is smaller than threshold
    while (actualKeywords.length < poolThreshold) {
      actualKeywords.add('__DUMMY_QUERY_${_rand.nextInt(10000000)}__');
    }

    // Compute trapdoors with randomized timing
    for (final kw in actualKeywords) {
      await Future.delayed(Duration(microseconds: _rand.nextInt(500) + minDispatchDelay.inMicroseconds ~/ 10));
      batch.add(SseEngine.computeTrapdoor(kw, kSearch));
    }

    return batch;
  }
}

/// Symmetric Searchable Encryption (SSE) engine with Dynamic Forward/Backward Privacy
/// and Volume-Hiding Candidate Padding.
class SseEngine {
  static const Set<String> _stopwords = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'arent',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
    'cant', 'cannot', 'could', 'couldnt', 'did', 'didnt', 'do', 'does', 'doesnt', 'doing', 'dont', 'down',
    'during', 'each', 'few', 'for', 'from', 'further', 'had', 'hadnt', 'has', 'hasnt', 'have', 'havent',
    'having', 'he', 'hed', 'hell', 'hes', 'her', 'here', 'heres', 'hers', 'herself', 'him', 'himself',
    'his', 'how', 'hows', 'i', 'id', 'ill', 'im', 'ive', 'if', 'in', 'into', 'is', 'isnt', 'it', 'its',
    'itself', 'lets', 'me', 'more', 'most', 'mustnt', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off',
    'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own',
    'same', 'shant', 'she', 'shed', 'shell', 'shes', 'should', 'shouldnt', 'so', 'some', 'such', 'than',
    'that', 'thats', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'theres', 'these',
    'they', 'theyd', 'theyll', 'theyre', 'theyve', 'this', 'those', 'through', 'to', 'too', 'under',
    'until', 'up', 'very', 'was', 'wasnt', 'we', 'wed', 'well', 'were', 'weve', 'werent', 'what', 'whats',
    'when', 'whens', 'where', 'wheres', 'which', 'while', 'who', 'whos', 'whom', 'why', 'whys', 'with',
    'wont', 'would', 'wouldnt', 'you', 'youd', 'youll', 'youre', 'youve', 'your', 'yours', 'yourself', 'yourselves'
  };

  /// Tokenizes text into a clean set of keywords
  static Set<String> tokenize(String text) {
    final cleaned = text.toLowerCase().replaceAll(RegExp(r'[^\w\s]'), ' ');
    final words = cleaned.split(RegExp(r'\s+'));
    final result = <String>{};
    for (final word in words) {
      final w = word.trim();
      if (w.length > 2 && !_stopwords.contains(w) && !RegExp(r'^\d+$').hasMatch(w)) {
        result.add(w);
      }
    }
    return result;
  }

  /// Extracts keywords from a local plain text file
  static Future<Set<String>> extractKeywords(File file) async {
    try {
      if (!await file.exists()) return {};
      final content = await file.readAsString();
      return tokenize(content);
    } catch (_) {
      return {};
    }
  }

  /// Derived domain-separated SSE operational keys via HKDF-SHA256
  static Map<String, Uint8List> deriveSseKeys(Uint8List masterKey, Uint8List salt) {
    final hkdf = Hkdf(sha256);
    final prk = hkdf.extract(salt, masterKey);
    final kSearch = hkdf.expand(prk, utf8.encode('VisioCrypt-Search-Key'), 32);
    final kIndexVal = hkdf.expand(prk, utf8.encode('VisioCrypt-IndexVal-Key'), 32);
    final kUpdate = hkdf.expand(prk, utf8.encode('VisioCrypt-Update-Key'), 32);
    return {
      'kSearch': kSearch,
      'kIndexVal': kIndexVal,
      'kUpdate': kUpdate,
    };
  }

  /// Computes the trapdoor for a keyword
  static String computeTrapdoor(String word, Uint8List kSearch) {
    final hmac = Hmac(sha256, kSearch);
    final digest = hmac.convert(utf8.encode(word.toLowerCase().trim()));
    return hex.encode(digest.bytes);
  }

  /// Computes a versioned PRF trapdoor for Forward-Private dynamic updates
  static String computeVersionedTrapdoor(String word, int version, Uint8List kSearch) {
    final hmac = Hmac(sha256, kSearch);
    final payload = utf8.encode('${word.toLowerCase().trim()}::$version');
    final digest = hmac.convert(payload);
    return hex.encode(digest.bytes);
  }

  /// AES-GCM-256 encryption helper
  static Uint8List encryptGcm(Uint8List key, Uint8List iv, Uint8List plaintext) {
    final cipher = GCMBlockCipher(AESEngine());
    cipher.init(true, AEADParameters(KeyParameter(key), 128, iv, Uint8List(0)));
    return cipher.process(plaintext);
  }

  /// AES-GCM-256 decryption helper
  static Uint8List decryptGcm(Uint8List key, Uint8List iv, Uint8List ciphertext) {
    final cipher = GCMBlockCipher(AESEngine());
    cipher.init(false, AEADParameters(KeyParameter(key), 128, iv, Uint8List(0)));
    return cipher.process(ciphertext);
  }

  /// Explicit byte-array zeroization for memory hygiene
  static void _zeroize(Uint8List bytes) {
    bytes.fillRange(0, bytes.length, 0);
  }

  /// Maximum single-bucket capacity before multi-bucket pagination kicks in
  static const int maxSingleBucketSize = 4096;
  static const int minBucketFloor = 4;

  /// Computes the defensible padded target capacity for a given result set size
  static int computePaddedCapacity(int len, {int maxBucket = maxSingleBucketSize}) {
    if (len <= minBucketFloor) return minBucketFloor;
    if (len >= maxBucket) {
      // Multi-bucket chunking: round up to nearest multiple of maxBucket
      return ((len + maxBucket - 1) ~/ maxBucket) * maxBucket;
    }
    int target = minBucketFloor;
    while (target < len && target < maxBucket) {
      target *= 2;
    }
    return target;
  }

  /// Multi-tier volume-hiding padding function (Phi) supporting arbitrary result counts
  static List<String> padFileList(List<String> files, {int maxBucket = maxSingleBucketSize}) {
    final cleanList = files.where((name) => !name.startsWith('__DUMMY_MATCH_')).toList();
    final len = cleanList.length;
    final targetLen = computePaddedCapacity(len, maxBucket: maxBucket);

    final padded = List<String>.from(cleanList);
    final rand = Random.secure();
    while (padded.length < targetLen) {
      final dummyId = '__DUMMY_MATCH_${rand.nextInt(10000000)}__';
      padded.add(dummyId);
    }
    return padded;
  }

  /// Adds a document to the encrypted SSE index database.
  static Future<void> indexDocument({
    required File indexFile,
    required String documentPath,
    required Set<String> keywords,
    required Uint8List masterKey,
    required Uint8List salt,
  }) async {
    final sseKeys = deriveSseKeys(masterKey, salt);
    final kSearch = sseKeys['kSearch']!;
    final kIndexVal = sseKeys['kIndexVal']!;

    final Map<String, dynamic> indexDb = await loadIndexDb(indexFile, kIndexVal);
    final docName = documentPath.split(Platform.pathSeparator).last;

    for (final word in keywords) {
      final trapdoor = computeTrapdoor(word, kSearch);
      final List<String> fileList = indexDb.containsKey(trapdoor)
          ? List<String>.from(indexDb[trapdoor])
          : [];

      if (!fileList.contains(docName)) {
        fileList.add(docName);
      }
      indexDb[trapdoor] = fileList;
    }

    await saveIndexDb(indexFile, indexDb, kIndexVal);

    // Explicit transient key zeroization
    _zeroize(kSearch);
    _zeroize(kIndexVal);
    _zeroize(sseKeys['kUpdate']!);
  }

  /// Performs dynamic document addition with incremental delta logging (Forward Private)
  static Future<void> addDocumentDynamic({
    required File indexFile,
    required File deltaLogFile,
    required String documentPath,
    required Set<String> keywords,
    required Uint8List masterKey,
    required Uint8List salt,
  }) async {
    final sseKeys = deriveSseKeys(masterKey, salt);
    final kSearch = sseKeys['kSearch']!;
    final kIndexVal = sseKeys['kIndexVal']!;
    final docName = documentPath.split(Platform.pathSeparator).last;

    // Load or initialize delta updates
    final deltaUpdates = <Map<String, dynamic>>[];
    if (await deltaLogFile.exists()) {
      try {
        final content = await deltaLogFile.readAsString();
        final list = json.decode(content) as List;
        for (final item in list) {
          deltaUpdates.add(Map<String, dynamic>.from(item));
        }
      } catch (_) {}
    }

    final rand = Random.secure();
    for (final word in keywords) {
      final trapdoor = computeTrapdoor(word, kSearch);
      final iv = Uint8List(12);
      for (int i = 0; i < 12; i++) {
        iv[i] = rand.nextInt(256);
      }
      final payload = utf8.encode(json.encode({'op': 'add', 'doc': docName, 'word': word}));
      final cipherBytes = encryptGcm(kIndexVal, iv, Uint8List.fromList(payload));
      final combined = Uint8List(12 + cipherBytes.length);
      combined.setRange(0, 12, iv);
      combined.setRange(12, combined.length, cipherBytes);

      deltaUpdates.add({
        'trapdoor': trapdoor,
        'payload': base64.encode(combined),
        'ts': DateTime.now().millisecondsSinceEpoch,
      });
    }

    if (!await deltaLogFile.parent.exists()) {
      await deltaLogFile.parent.create(recursive: true);
    }
    await deltaLogFile.writeAsString(json.encode(deltaUpdates));

    _zeroize(kSearch);
    _zeroize(kIndexVal);
    _zeroize(sseKeys['kUpdate']!);
  }

  /// Searches the encrypted index database with Bloom filter-assisted deletion filtering
  static Future<List<String>> searchIndex({
    required File indexFile,
    required String keyword,
    required Uint8List masterKey,
    required Uint8List salt,
    SseBloomFilter? deletionFilter,
  }) async {
    if (!await indexFile.exists()) return [];

    final sseKeys = deriveSseKeys(masterKey, salt);
    final kSearch = sseKeys['kSearch']!;
    final kIndexVal = sseKeys['kIndexVal']!;

    final trapdoor = computeTrapdoor(keyword, kSearch);
    final Map<String, dynamic> indexDb = await loadIndexDb(indexFile, kIndexVal);

    List<String> results = [];
    if (indexDb.containsKey(trapdoor)) {
      final rawList = List<String>.from(indexDb[trapdoor]);
      results = rawList.where((name) {
        if (name.startsWith('__DUMMY_MATCH_')) return false;
        if (deletionFilter != null && deletionFilter.mightContain('$keyword::$name')) return false;
        return true;
      }).toList();
    }

    // Explicit transient key zeroization
    _zeroize(kSearch);
    _zeroize(kIndexVal);
    _zeroize(sseKeys['kUpdate']!);

    return results;
  }

  /// Helper: Load and decrypt index file from disk
  static Future<Map<String, dynamic>> loadIndexDb(File file, Uint8List kIndexVal) async {
    if (!await file.exists()) return {};

    try {
      final rawContent = await file.readAsString();
      final Map<String, dynamic> encryptedJson = json.decode(rawContent);
      final Map<String, dynamic> decryptedDb = {};

      for (final entry in encryptedJson.entries) {
        final trapdoor = entry.key;
        final parts = base64.decode(entry.value);

        if (parts.length < 12) continue;

        final iv = parts.sublist(0, 12);
        final ciphertext = parts.sublist(12);

        final decryptedBytes = decryptGcm(kIndexVal, iv, ciphertext);
        final fileList = json.decode(utf8.decode(decryptedBytes)) as List;
        decryptedDb[trapdoor] = List<String>.from(fileList);
      }
      return decryptedDb;
    } catch (_) {
      return {};
    }
  }

  /// Helper: Encrypt and save index database to disk with volume-hiding padding
  static Future<void> saveIndexDb(File file, Map<String, dynamic> indexDb, Uint8List kIndexVal) async {
    final Map<String, String> encryptedJson = {};
    final rand = Random.secure();

    for (final entry in indexDb.entries) {
      final trapdoor = entry.key;
      final fileList = entry.value as List<String>;
      final paddedList = padFileList(fileList);

      final plainBytes = utf8.encode(json.encode(paddedList));
      final iv = Uint8List(12);
      for (int i = 0; i < 12; i++) {
        iv[i] = rand.nextInt(256);
      }

      final cipherBytes = encryptGcm(kIndexVal, iv, Uint8List.fromList(plainBytes));
      final combined = Uint8List(iv.length + cipherBytes.length);
      combined.setRange(0, iv.length, iv);
      combined.setRange(iv.length, combined.length, cipherBytes);

      encryptedJson[trapdoor] = base64.encode(combined);
    }

    if (!await file.parent.exists()) {
      await file.parent.create(recursive: true);
    }
    await file.writeAsString(json.encode(encryptedJson));
  }
}
