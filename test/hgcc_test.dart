import 'dart:io';
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:crypto/crypto.dart';

import 'package:visiocrypt/crypto/hkdf.dart';
import 'package:visiocrypt/crypto/hgcc_engine.dart';
import 'package:visiocrypt/crypto/hgcc_aead.dart';

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
      expect(derivedKey1, derivedKey2); // Determinism
    });
  });

  group('HGCC Cipher Engine Tests', () {
    test('HGCC engine initialization and tick sequence', () {
      final key = Uint8List.fromList(List.generate(64, (i) => i * 3));
      
      final engine = HgccEngine();
      engine.init(key);
      
      final byte1 = engine.tick();
      final byte2 = engine.tick();
      
      // Keystream bytes should be between 0 and 255
      expect(byte1 >= 0 && byte1 <= 255, true);
      expect(byte2 >= 0 && byte2 <= 255, true);
    });

    test('Different keys produce different keystreams', () {
      final key1 = Uint8List.fromList(List.generate(64, (i) => i));
      final key2 = Uint8List.fromList(List.generate(64, (i) => i + 1));

      final engine1 = HgccEngine()..init(key1);
      final engine2 = HgccEngine()..init(key2);

      final stream1 = List.generate(20, (_) => engine1.tick());
      final stream2 = List.generate(20, (_) => engine2.tick());

      expect(stream1, isNot(equals(stream2)));
    });
  });

  group('HGCC AEAD File Operations Tests', () {
    late File plaintextFile;
    late File encryptedFile;
    late File decryptedFile;
    late Uint8List masterKey;

    setUp(() async {
      plaintextFile = File('test_plain.txt');
      encryptedFile = File('test_encrypted.vc');
      decryptedFile = File('test_decrypted.txt');

      // Create dummy plaintext
      await plaintextFile.writeAsString(
        'This is a secret message. VisioCrypt uses Galois LFSR and Rule 30 CA!',
      );

      masterKey = Uint8List.fromList(List.generate(64, (i) => i * 4));
    });

    tearDown(() async {
      if (await plaintextFile.exists()) await plaintextFile.delete();
      if (await encryptedFile.exists()) await encryptedFile.delete();
      if (await decryptedFile.exists()) await decryptedFile.delete();
    });

    test('Encrypt and decrypt roundtrip matches original data', () async {
      // Encrypt
      await HgccAead.encryptFile(
        sourceFile: plaintextFile,
        destFile: encryptedFile,
        masterKey: masterKey,
      );

      expect(await encryptedFile.exists(), true);
      expect(await encryptedFile.length() > await plaintextFile.length(), true); // should have 48-byte overhead

      // Decrypt
      await HgccAead.decryptFile(
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
      // Encrypt
      await HgccAead.encryptFile(
        sourceFile: plaintextFile,
        destFile: encryptedFile,
        masterKey: masterKey,
      );

      // Modify the ciphertext by flipping a bit in the middle of the file
      final bytes = await encryptedFile.readAsBytes();
      final midPoint = bytes.length ~/ 2;
      bytes[midPoint] = bytes[midPoint] ^ 0x01; // flip 1 bit
      await encryptedFile.writeAsBytes(bytes);

      // Attempt decryption, which should fail the HMAC check
      expect(
        () => HgccAead.decryptFile(
          sourceFile: encryptedFile,
          destFile: decryptedFile,
          masterKey: masterKey,
        ),
        throwsA(isA<SecurityException>()),
      );
    });
  });
}
