import 'dart:io';
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:crypto/crypto.dart';

import 'package:visiocrypt/crypto/hkdf.dart';
import 'package:visiocrypt/crypto/crypt_engine.dart';
import 'package:visiocrypt/crypto/sse_engine.dart';

void main() {
  group('HKDF Tests', () {
    test('HKDF-Extract and Expand produces deterministic split keys', () {
      final ikm = Uint8List.fromList(List.generate(64, (i) => i));
      final salt = Uint8List.fromList(List.generate(16, (i) => i * 2));
      final info = Uint8List.fromList('TestContext'.codeUnits);

      final hkdf = Hkdf(sha256);
      final derivedKey1 = hkdf.deriveKey(salt, ikm, info, 32);
      final derivedKey2 = hkdf.deriveKey(salt, ikm, info, 32);

      expect(derivedKey1.length, 32);
      expect(derivedKey1, derivedKey2);
    });
  });

  group('AES-CTR-256 Stream Cipher Engine Tests', () {
    test('AES-CTR engine initialization and keystream sequence', () {
      final key = Uint8List(32); // All zeros key
      final iv = Uint8List(16);  // All zeros IV
      
      final engine = AesCtrEngine();
      engine.init(key, iv);
      
      final byte1 = engine.tick();
      final byte2 = engine.tick();
      
      expect(byte1 >= 0 && byte1 <= 255, true);
      expect(byte2 >= 0 && byte2 <= 255, true);
    });

    test('Different keys produce different keystreams', () {
      final key1 = Uint8List.fromList(List.generate(32, (i) => i));
      final key2 = Uint8List.fromList(List.generate(32, (i) => i + 1));
      final iv = Uint8List(16);

      final engine1 = AesCtrEngine()..init(key1, iv);
      final engine2 = AesCtrEngine()..init(key2, iv);

      final stream1 = List.generate(20, (_) => engine1.tick());
      final stream2 = List.generate(20, (_) => engine2.tick());

      expect(stream1, isNot(equals(stream2)));
    });
  });

  group('Symmetric Searchable Encryption (SSE) Tokenization & Trapdoor Tests', () {
    test('Tokenization removes stopwords and filters valid keywords', () {
      final text = 'The quick brown fox jumps over the lazy dog and a simple invoice of 1000 dollars.';
      final tokens = SseEngine.tokenize(text);

      expect(tokens.contains('quick'), true);
      expect(tokens.contains('brown'), true);
      expect(tokens.contains('fox'), true);
      expect(tokens.contains('jumps'), true);
      expect(tokens.contains('lazy'), true);
      expect(tokens.contains('dog'), true);
      expect(tokens.contains('simple'), true);
      expect(tokens.contains('invoice'), true);
      expect(tokens.contains('dollars'), true);

      // Stopwords and numbers should be removed
      expect(tokens.contains('the'), false);
      expect(tokens.contains('and'), false);
      expect(tokens.contains('of'), false);
      expect(tokens.contains('1000'), false);
    });

    test('Trapdoor generation is deterministic', () {
      final key = Uint8List.fromList(List.generate(32, (i) => i * 2));
      final term = 'secure_keyword';

      final trapdoor1 = SseEngine.computeTrapdoor(term, key);
      final trapdoor2 = SseEngine.computeTrapdoor(term, key);

      expect(trapdoor1, trapdoor2);
      expect(trapdoor1.length, 64); // Hex encoded SHA256 is 64 characters
    });
  });

  group('CryptEngine AEAD File Operations Tests', () {
    late File plaintextFile;
    late File encryptedFile;
    late File decryptedFile;
    late Uint8List masterKey;

    setUp(() async {
      plaintextFile = File('test_plain.txt');
      encryptedFile = File('test_encrypted.vc');
      decryptedFile = File('test_decrypted.txt');

      await plaintextFile.writeAsString(
        'This is a top-secret document containing classified keywords: invoice, financial, budget.',
      );

      masterKey = Uint8List.fromList(List.generate(64, (i) => i * 4));
    });

    tearDown(() async {
      if (await plaintextFile.exists()) await plaintextFile.delete();
      if (await encryptedFile.exists()) await encryptedFile.delete();
      if (await decryptedFile.exists()) await decryptedFile.delete();
    });

    test('Encrypt and decrypt roundtrip matches original data', () async {
      await CryptEngine.encryptFile(
        sourceFile: plaintextFile,
        destFile: encryptedFile,
        masterKey: masterKey,
      );

      expect(await encryptedFile.exists(), true);
      
      // Salt (16 bytes) + Ciphertext + Tag (32 bytes)
      expect(await encryptedFile.length() > await plaintextFile.length(), true);

      await CryptEngine.decryptFile(
        sourceFile: encryptedFile,
        destFile: decryptedFile,
        masterKey: masterKey,
      );

      expect(await decryptedFile.exists(), true);
      final decryptedText = await decryptedFile.readAsString();
      final originalText = await plaintextFile.readAsString();
      expect(decryptedText, originalText);
    });

    test('Decryption fails if ciphertext is altered (AEAD integrity check)', () async {
      await CryptEngine.encryptFile(
        sourceFile: plaintextFile,
        destFile: encryptedFile,
        masterKey: masterKey,
      );

      // Modify a bit in the middle of ciphertext
      final bytes = await encryptedFile.readAsBytes();
      final midPoint = bytes.length ~/ 2;
      bytes[midPoint] = bytes[midPoint] ^ 0x01;
      await encryptedFile.writeAsBytes(bytes);

      expect(
        () => CryptEngine.decryptFile(
          sourceFile: encryptedFile,
          destFile: decryptedFile,
          masterKey: masterKey,
        ),
        throwsA(isA<SecurityException>()),
      );
    });
  });

  group('SSE Index Database Tests', () {
    late File indexFile;
    late Uint8List masterKey;
    late Uint8List salt;

    setUp(() async {
      indexFile = File('test_index.db');
      masterKey = Uint8List.fromList(List.generate(64, (i) => i));
      salt = Uint8List.fromList(List.generate(16, (i) => i * 3));
    });

    tearDown(() async {
      if (await indexFile.exists()) await indexFile.delete();
    });

    test('Indexing and searching a document retrieves matching files', () async {
      final docPath = 'E:\\_PROJECTS\\visiocrypto\\dummy_invoice.txt';
      final keywords = {'invoice', 'financial', 'secret'};

      await SseEngine.indexDocument(
        indexFile: indexFile,
        documentPath: docPath,
        keywords: keywords,
        masterKey: masterKey,
        salt: salt,
      );

      expect(await indexFile.exists(), true);

      // Search keyword 'invoice'
      final searchResults1 = await SseEngine.searchIndex(
        indexFile: indexFile,
        keyword: 'invoice',
        masterKey: masterKey,
        salt: salt,
      );

      expect(searchResults1.contains('dummy_invoice.txt'), true);

      // Search keyword 'financial'
      final searchResults2 = await SseEngine.searchIndex(
        indexFile: indexFile,
        keyword: 'financial',
        masterKey: masterKey,
        salt: salt,
      );

      expect(searchResults2.contains('dummy_invoice.txt'), true);

      // Search non-existent keyword
      final searchResults3 = await SseEngine.searchIndex(
        indexFile: indexFile,
        keyword: 'nonexistent',
        masterKey: masterKey,
        salt: salt,
      );

      expect(searchResults3.isEmpty, true);
    });

    test('Volume-Hiding padding pads index lists and search filters dummy matching records', () async {
      final docPath = 'E:\\_PROJECTS\\visiocrypto\\dummy_report.txt';
      final keywords = {'report'};

      await SseEngine.indexDocument(
        indexFile: indexFile,
        documentPath: docPath,
        keywords: keywords,
        masterKey: masterKey,
        salt: salt,
      );

      // Load index raw decrypted db entries
      final sseKeys = SseEngine.deriveSseKeys(masterKey, salt);
      final kIndexVal = sseKeys['kIndexVal']!;
      final rawDb = await SseEngine.loadIndexDb(indexFile, kIndexVal);

      // Extract raw list
      final trapdoor = SseEngine.computeTrapdoor('report', sseKeys['kSearch']!);
      expect(rawDb.containsKey(trapdoor), true);
      
      final rawList = rawDb[trapdoor] as List<String>;
      // Padding must make the list a power of 2, minimum 4
      expect(rawList.length >= 4, true);
      expect((rawList.length & (rawList.length - 1)) == 0, true); // power of 2 check
      expect(rawList.any((entry) => entry.startsWith('__DUMMY_MATCH_')), true);

      // Now verify that searching filters the dummy matches out
      final searchResults = await SseEngine.searchIndex(
        indexFile: indexFile,
        keyword: 'report',
        masterKey: masterKey,
        salt: salt,
      );

      expect(searchResults.length, 1);
      expect(searchResults.contains('dummy_report.txt'), true);
      expect(searchResults.any((entry) => entry.startsWith('__DUMMY_MATCH_')), false);
    });

    test('Volume-Hiding padding correctly handles result sets exceeding 32 entries', () {
      // 0 entries -> floor 4
      expect(SseEngine.computePaddedCapacity(0), 4);
      // 3 entries -> floor 4
      expect(SseEngine.computePaddedCapacity(3), 4);
      // 5 entries -> 8
      expect(SseEngine.computePaddedCapacity(5), 8);
      // 33 entries -> 64
      expect(SseEngine.computePaddedCapacity(33), 64);
      // 65 entries -> 128
      expect(SseEngine.computePaddedCapacity(65), 128);
      // 300 entries -> 512
      expect(SseEngine.computePaddedCapacity(300), 512);
      // 2500 entries -> 4096
      expect(SseEngine.computePaddedCapacity(2500), 4096);
      // 5000 entries (exceeds single bucket 4096) -> multi-bucket chunking 8192
      expect(SseEngine.computePaddedCapacity(5000), 8192);

      final mockList35 = List.generate(35, (i) => 'doc_$i.txt');
      final padded35 = SseEngine.padFileList(mockList35);
      expect(padded35.length, 64);
      expect(padded35.where((doc) => !doc.startsWith('__DUMMY_MATCH_')).length, 35);
    });
  });
}
