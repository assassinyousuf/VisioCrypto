import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:convert/convert.dart';
import 'package:pointycastle/export.dart' hide Digest;
import 'hkdf.dart';

/// Symmetric Searchable Encryption (SSE) engine for secure cloud indexing.
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
      // Fallback for binary/corrupt files
      return {};
    }
  }

  /// Derived SSE keys
  static Map<String, Uint8List> deriveSseKeys(Uint8List masterKey, Uint8List salt) {
    final hkdf = Hkdf(sha256);
    final prk = hkdf.extract(salt, masterKey);
    final kSearch = hkdf.expand(prk, utf8.encode('VisioCrypt-Search-Key'), 32);
    final kIndexVal = hkdf.expand(prk, utf8.encode('VisioCrypt-IndexVal-Key'), 32);
    return {
      'kSearch': kSearch,
      'kIndexVal': kIndexVal,
    };
  }

  /// Computes the trapdoor for a keyword
  static String computeTrapdoor(String word, Uint8List kSearch) {
    final hmac = Hmac(sha256, kSearch);
    final digest = hmac.convert(utf8.encode(word.toLowerCase().trim()));
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

  /// Adds a document to the encrypted SSE index database.
  /// If the index file doesn't exist, a new one is initialized.
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

    // Load existing index or initialize new
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
  }

  /// Searches the encrypted index database using a keyword trapdoor.
  static Future<List<String>> searchIndex({
    required File indexFile,
    required String keyword,
    required Uint8List masterKey,
    required Uint8List salt,
  }) async {
    if (!await indexFile.exists()) return [];

    final sseKeys = deriveSseKeys(masterKey, salt);
    final kSearch = sseKeys['kSearch']!;
    final kIndexVal = sseKeys['kIndexVal']!;

    final trapdoor = computeTrapdoor(keyword, kSearch);
    final Map<String, dynamic> indexDb = await loadIndexDb(indexFile, kIndexVal);

    if (indexDb.containsKey(trapdoor)) {
      return List<String>.from(indexDb[trapdoor]);
    }
    return [];
  }

  /// Helper: Load and decrypt index file from disk
  static Future<Map<String, dynamic>> loadIndexDb(File file, Uint8List kIndexVal) async {
    if (!await file.exists()) {
      return {};
    }

    try {
      final rawContent = await file.readAsString();
      final Map<String, dynamic> encryptedJson = json.decode(rawContent);
      final Map<String, dynamic> decryptedDb = {};

      for (final entry in encryptedJson.entries) {
        final trapdoor = entry.key;
        final parts = base64.decode(entry.value);

        if (parts.length < 12) continue; // Invalid entry (GCM IV is 12 bytes)

        final iv = parts.sublist(0, 12);
        final ciphertext = parts.sublist(12);

        final decryptedBytes = decryptGcm(kIndexVal, iv, ciphertext);
        final fileList = json.decode(utf8.decode(decryptedBytes)) as List;
        decryptedDb[trapdoor] = List<String>.from(fileList);
      }
      return decryptedDb;
    } catch (_) {
      // Return empty database if corrupted or decryption fails
      return {};
    }
  }

  /// Helper: Encrypt and save index database to disk
  static Future<void> saveIndexDb(File file, Map<String, dynamic> indexDb, Uint8List kIndexVal) async {
    final Map<String, String> encryptedJson = {};
    final rand = Random.secure();

    for (final entry in indexDb.entries) {
      final trapdoor = entry.key;
      final fileList = entry.value as List<String>;

      // Serialize value
      final plainBytes = utf8.encode(json.encode(fileList));

      // Generate 12-byte random IV for GCM
      final iv = Uint8List(12);
      for (int i = 0; i < 12; i++) {
        iv[i] = rand.nextInt(256);
      }

      final cipherBytes = encryptGcm(kIndexVal, iv, Uint8List.fromList(plainBytes));

      // Concatenate IV and Ciphertext
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
