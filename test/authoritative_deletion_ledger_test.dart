import 'dart:io';
import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:crypto/crypto.dart';

import 'package:visiocrypt/crypto/hkdf.dart';
import 'package:visiocrypt/crypto/sse_engine.dart';
import 'package:visiocrypt/crypto/deletion_ledger.dart';

void main() {
  group('Authoritative Deletion Ledger Core & Cryptographic Verification', () {
    late Uint8List masterKey;
    late Uint8List salt;
    late Uint8List kLedgerEnc;
    late Uint8List kLedgerAuth;

    setUp(() {
      masterKey = Uint8List.fromList(List.generate(64, (i) => (i * 7) % 256));
      salt = Uint8List.fromList(List.generate(16, (i) => (i * 13) % 256));
      final sseKeys = SseEngine.deriveSseKeys(masterKey, salt);
      kLedgerEnc = sseKeys['kLedgerEnc']!;
      kLedgerAuth = sseKeys['kLedgerAuth']!;
    });

    test('Tombstone cryptographic HMAC creation and verification', () {
      final docId = 'classified_doc_001.pdf';
      final timestamp = 1700000000000;
      final epoch = 1;

      final tag = DeletionTombstone.computeTag(
        docId: docId,
        timestamp: timestamp,
        epoch: epoch,
        kAuth: kLedgerAuth,
      );

      final tombstone = DeletionTombstone(
        docId: docId,
        timestamp: timestamp,
        epoch: epoch,
        keywords: {'classified', 'topsecret'},
        hmacTag: tag,
      );

      expect(tombstone.verify(kLedgerAuth), true);

      // Wrong key must fail verification
      final wrongKey = Uint8List(32);
      expect(tombstone.verify(wrongKey), false);

      // Tampered docId must fail
      final tamperedTombstone = DeletionTombstone(
        docId: 'classified_doc_002.pdf',
        timestamp: timestamp,
        epoch: epoch,
        keywords: {'classified'},
        hmacTag: tag,
      );
      expect(tamperedTombstone.verify(kLedgerAuth), false);
    });

    test('Active documents vs Deleted documents: accurate classification', () {
      final ledger = AuthoritativeDeletionLedger(filterBitSize: 4096, filterHashFunctions: 4);

      ledger.markDeleted(
        docId: 'deleted_report.txt',
        keywords: {'finance', 'report'},
        kAuth: kLedgerAuth,
      );

      // Deleted document should be true
      expect(ledger.isDeleted('deleted_report.txt', keyword: 'finance'), true);
      expect(ledger.isDeleted('deleted_report.txt', keyword: 'report'), true);
      expect(ledger.isDeleted('deleted_report.txt'), true);

      // Active document should be false
      expect(ledger.isDeleted('active_statement.txt', keyword: 'finance'), false);
      expect(ledger.isDeleted('active_statement.txt', keyword: 'other'), false);
      expect(ledger.isDeleted('active_statement.txt'), false);
    });

    test('Zero False Exclusions: Bloom Filter collisions against active documents are resolved', () {
      // Use tiny filter (64 bits, 3 hashes) to intentionally induce collisions
      final smallLedger = AuthoritativeDeletionLedger(filterBitSize: 64, filterHashFunctions: 3);

      // Insert 30 deleted items into the tiny 64-bit filter so bits become saturated
      for (int i = 0; i < 30; i++) {
        smallLedger.markDeleted(
          docId: 'del_file_$i.txt',
          keywords: {'common_term', 'term_$i'},
          kAuth: kLedgerAuth,
        );
      }

      // Check an active document that was never deleted
      final activeDoc = 'active_vital_record.pdf';
      expect(smallLedger.hasTombstone(activeDoc), false);

      // Querying with keyword 'common_term':
      // The saturated Bloom filter might report true (a false positive collision),
      // but the authoritative ledger MUST resolve it and return false!
      final isDel = smallLedger.isDeleted(activeDoc, keyword: 'common_term');
      expect(isDel, false, reason: 'Bloom filter false positive must NEVER exclude an active document!');
    });

    test('Zero False Negatives: deleted documents are never missed', () {
      final ledger = AuthoritativeDeletionLedger(filterBitSize: 8192, filterHashFunctions: 4);

      for (int i = 0; i < 50; i++) {
        ledger.markDeleted(
          docId: 'doc_to_delete_$i.dat',
          keywords: {'alpha', 'beta', 'kw_$i'},
          kAuth: kLedgerAuth,
        );
      }

      for (int i = 0; i < 50; i++) {
        expect(ledger.isDeleted('doc_to_delete_$i.dat', keyword: 'alpha'), true);
        expect(ledger.isDeleted('doc_to_delete_$i.dat', keyword: 'beta'), true);
        expect(ledger.isDeleted('doc_to_delete_$i.dat', keyword: 'kw_$i'), true);
        expect(ledger.isDeleted('doc_to_delete_$i.dat'), true);
      }
    });

    test('Duplicate deletion idempotency', () {
      final ledger = AuthoritativeDeletionLedger();

      ledger.markDeleted(
        docId: 'dup_file.txt',
        keywords: {'duplicate'},
        kAuth: kLedgerAuth,
        timestamp: 1000,
      );
      final count1 = ledger.deletionCount;
      final epoch1 = ledger.currentEpoch;

      // Repeat deletion
      ledger.markDeleted(
        docId: 'dup_file.txt',
        keywords: {'duplicate', 'extra'},
        kAuth: kLedgerAuth,
        timestamp: 2000,
      );
      final count2 = ledger.deletionCount;
      final epoch2 = ledger.currentEpoch;

      expect(count2, count1, reason: 'Duplicate deletion must not increment document count');
      expect(epoch2 > epoch1, true, reason: 'Epoch should increment to reflect state mutation');
      expect(ledger.isDeleted('dup_file.txt', keyword: 'duplicate'), true);
      expect(ledger.isDeleted('dup_file.txt', keyword: 'extra'), true);
    });
  });

  group('Authoritative Deletion Ledger Persistence & Recovery Tests', () {
    late File ledgerFile;
    late Uint8List masterKey;
    late Uint8List salt;
    late Uint8List kLedgerEnc;
    late Uint8List kLedgerAuth;

    setUp(() {
      ledgerFile = File('test_ledger_encrypted.db');
      masterKey = Uint8List.fromList(List.generate(64, (i) => i));
      salt = Uint8List.fromList(List.generate(16, (i) => i * 3));
      final sseKeys = SseEngine.deriveSseKeys(masterKey, salt);
      kLedgerEnc = sseKeys['kLedgerEnc']!;
      kLedgerAuth = sseKeys['kLedgerAuth']!;
    });

    tearDown(() async {
      if (await ledgerFile.exists()) await ledgerFile.delete();
      final tmpFiles = ledgerFile.parent.listSync().where((f) => f.path.contains('test_ledger_encrypted.db.tmp'));
      for (final f in tmpFiles) {
        f.deleteSync();
      }
    });

    test('Restart Recovery: Encrypted ledger roundtrip and Bloom filter rehydration', () async {
      final ledgerOriginal = AuthoritativeDeletionLedger(filterBitSize: 4096, filterHashFunctions: 4);

      ledgerOriginal.markDeleted(
        docId: 'report_2024.pdf',
        keywords: {'quarterly', 'earnings'},
        kAuth: kLedgerAuth,
      );
      ledgerOriginal.markDeleted(
        docId: 'memo_secret.txt',
        keywords: {'confidential', 'merger'},
        kAuth: kLedgerAuth,
      );

      // Save to encrypted file
      await ledgerOriginal.saveToFile(ledgerFile, kLedgerEnc, kLedgerAuth);
      expect(await ledgerFile.exists(), true);

      // Simulate app restart: load into a completely fresh instance
      final restoredLedger = await AuthoritativeDeletionLedger.loadFromFile(
        ledgerFile,
        kLedgerEnc,
        kLedgerAuth,
      );

      expect(restoredLedger.deletionCount, 2);
      expect(restoredLedger.currentEpoch, ledgerOriginal.currentEpoch);

      // Verify deletion queries on restored ledger
      expect(restoredLedger.isDeleted('report_2024.pdf', keyword: 'quarterly'), true);
      expect(restoredLedger.isDeleted('report_2024.pdf', keyword: 'earnings'), true);
      expect(restoredLedger.isDeleted('memo_secret.txt', keyword: 'confidential'), true);
      expect(restoredLedger.isDeleted('memo_secret.txt', keyword: 'merger'), true);

      // Non-deleted document must remain active
      expect(restoredLedger.isDeleted('active_memo.txt', keyword: 'confidential'), false);
    });

    test('Corrupted or Tampered Ledger: Triggers LedgerCorruptedException and never assumes deleted', () async {
      final ledgerOriginal = AuthoritativeDeletionLedger();
      ledgerOriginal.markDeleted(
        docId: 'doc_alpha.txt',
        keywords: {'alpha'},
        kAuth: kLedgerAuth,
      );
      await ledgerOriginal.saveToFile(ledgerFile, kLedgerEnc, kLedgerAuth);

      // Tamper with ciphertext bytes
      final bytes = await ledgerFile.readAsBytes();
      final mid = bytes.length ~/ 2;
      bytes[mid] ^= 0xFF; // flip bits
      await ledgerFile.writeAsBytes(bytes);

      // Load must throw LedgerCorruptedException due to GCM AEAD authentication failure
      expect(
        () => AuthoritativeDeletionLedger.loadFromFile(ledgerFile, kLedgerEnc, kLedgerAuth),
        throwsA(isA<LedgerCorruptedException>()),
      );
    });

    test('Missing Ledger file returns fresh empty state (does not assume all files deleted)', () async {
      final nonExistentFile = File('non_existent_ledger.db');
      expect(await nonExistentFile.exists(), false);

      final freshLedger = await AuthoritativeDeletionLedger.loadFromFile(
        nonExistentFile,
        kLedgerEnc,
        kLedgerAuth,
      );

      expect(freshLedger.deletionCount, 0);
      expect(freshLedger.isDeleted('any_file.txt', keyword: 'any_word'), false);
    });

    test('Synchronization & Conflict Resolution: Merge remote state via LWW', () {
      final localLedger = AuthoritativeDeletionLedger();
      final remoteLedger = AuthoritativeDeletionLedger();

      // Local deletion
      localLedger.markDeleted(
        docId: 'local_only.txt',
        keywords: {'local'},
        kAuth: kLedgerAuth,
        timestamp: 1000,
      );

      // Remote deletion (different file)
      remoteLedger.markDeleted(
        docId: 'remote_only.txt',
        keywords: {'remote'},
        kAuth: kLedgerAuth,
        timestamp: 2000,
      );

      // Shared file deleted on both, but remote is newer
      localLedger.markDeleted(
        docId: 'shared.txt',
        keywords: {'shared', 'v1'},
        kAuth: kLedgerAuth,
        timestamp: 1500,
      );
      remoteLedger.markDeleted(
        docId: 'shared.txt',
        keywords: {'shared', 'v2'},
        kAuth: kLedgerAuth,
        timestamp: 2500,
      );

      // Merge remote into local
      localLedger.mergeRemote(remoteLedger, kLedgerAuth);

      expect(localLedger.deletionCount, 3);
      expect(localLedger.isDeleted('local_only.txt', keyword: 'local'), true);
      expect(localLedger.isDeleted('remote_only.txt', keyword: 'remote'), true);
      expect(localLedger.isDeleted('shared.txt', keyword: 'shared'), true);
      expect(localLedger.isDeleted('shared.txt', keyword: 'v2'), true);
      expect(localLedger.getTombstone('shared.txt')!.timestamp, 2500);
    });
  });

  group('Full End-to-End SSE Search with Authoritative Deletion Ledger Integration', () {
    late File indexFile;
    late File ledgerFile;
    late Uint8List masterKey;
    late Uint8List salt;

    setUp(() async {
      indexFile = File('test_sse_ledger_index.db');
      ledgerFile = File('test_sse_ledger_state.db');
      masterKey = Uint8List.fromList(List.generate(64, (i) => (i * 3) % 256));
      salt = Uint8List.fromList(List.generate(16, (i) => (i * 5) % 256));
    });

    tearDown(() async {
      if (await indexFile.exists()) await indexFile.delete();
      if (await ledgerFile.exists()) await ledgerFile.delete();
    });

    test('End-to-End: Indexing multiple documents, authoritatively deleting one, and searching', () async {
      final ledger = AuthoritativeDeletionLedger(filterBitSize: 2048, filterHashFunctions: 3);

      // Index 3 documents under keyword 'tax'
      await SseEngine.indexDocument(
        indexFile: indexFile,
        documentPath: 'tax_return_2022.pdf',
        keywords: {'tax', 'audit'},
        masterKey: masterKey,
        salt: salt,
      );
      await SseEngine.indexDocument(
        indexFile: indexFile,
        documentPath: 'tax_return_2023.pdf',
        keywords: {'tax', 'irs'},
        masterKey: masterKey,
        salt: salt,
      );
      await SseEngine.indexDocument(
        indexFile: indexFile,
        documentPath: 'tax_return_2024.pdf',
        keywords: {'tax', 'deductions'},
        masterKey: masterKey,
        salt: salt,
      );

      // Authoritatively delete tax_return_2022.pdf
      await SseEngine.deleteDocument(
        ledger: ledger,
        documentName: 'tax_return_2022.pdf',
        keywords: {'tax', 'audit'},
        masterKey: masterKey,
        salt: salt,
        ledgerFile: ledgerFile,
      );

      // Execute search query for 'tax' using deletion ledger
      final searchResults = await SseEngine.searchIndex(
        indexFile: indexFile,
        keyword: 'tax',
        masterKey: masterKey,
        salt: salt,
        deletionLedger: ledger,
      );

      // Deleted doc must be absent
      expect(searchResults.contains('tax_return_2022.pdf'), false);
      // Active docs must be present
      expect(searchResults.contains('tax_return_2023.pdf'), true);
      expect(searchResults.contains('tax_return_2024.pdf'), true);
      expect(searchResults.length, 2);
    });

    test('Stale local cache / file presence independence', () async {
      final ledger = AuthoritativeDeletionLedger();

      // Create a local file on disk that is authoritatively deleted
      final lingeringLocalFile = File('lingering_file.txt');
      await lingeringLocalFile.writeAsString('I linger on disk');

      await SseEngine.indexDocument(
        indexFile: indexFile,
        documentPath: 'lingering_file.txt',
        keywords: {'lingering'},
        masterKey: masterKey,
        salt: salt,
      );

      // Delete in ledger
      await SseEngine.deleteDocument(
        ledger: ledger,
        documentName: 'lingering_file.txt',
        keywords: {'lingering'},
        masterKey: masterKey,
        salt: salt,
      );

      // Even though File.existsSync() is true on disk, searchIndex MUST exclude it!
      expect(await lingeringLocalFile.exists(), true);

      final results = await SseEngine.searchIndex(
        indexFile: indexFile,
        keyword: 'lingering',
        masterKey: masterKey,
        salt: salt,
        deletionLedger: ledger,
      );

      expect(results.contains('lingering_file.txt'), false);
      await lingeringLocalFile.delete();
    });
  });
}
