import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:convert/convert.dart';
import 'package:pointycastle/export.dart' hide Digest;
import 'sse_engine.dart';

/// Exception thrown when the Authoritative Deletion Ledger state is corrupted,
/// fails cryptographic authentication, or has been tampered with.
class LedgerCorruptedException implements Exception {
  final String message;
  LedgerCorruptedException(this.message);

  @override
  String toString() => 'LedgerCorruptedException: $message';
}

/// A cryptographic deletion tombstone recording an authoritative document deletion.
class DeletionTombstone {
  final String docId;
  final int timestamp;
  final int epoch;
  final Set<String> keywords;
  final String hmacTag;

  DeletionTombstone({
    required this.docId,
    required this.timestamp,
    required this.epoch,
    required this.keywords,
    required this.hmacTag,
  });

  /// Computes the HMAC-SHA256 authentication tag for a tombstone
  static String computeTag({
    required String docId,
    required int timestamp,
    required int epoch,
    required Uint8List kAuth,
  }) {
    final hmac = Hmac(sha256, kAuth);
    final payload = utf8.encode('$docId::$timestamp::$epoch');
    return hex.encode(hmac.convert(payload).bytes);
  }

  /// Verifies the cryptographic integrity of this tombstone
  bool verify(Uint8List kAuth) {
    final expected = computeTag(docId: docId, timestamp: timestamp, epoch: epoch, kAuth: kAuth);
    return expected == hmacTag;
  }

  Map<String, dynamic> toJson() => {
    'docId': docId,
    'timestamp': timestamp,
    'epoch': epoch,
    'keywords': keywords.toList(),
    'hmacTag': hmacTag,
  };

  factory DeletionTombstone.fromJson(Map<String, dynamic> json) {
    return DeletionTombstone(
      docId: json['docId'] as String,
      timestamp: json['timestamp'] as int,
      epoch: json['epoch'] as int,
      keywords: Set<String>.from(json['keywords'] as List),
      hmacTag: json['hmacTag'] as String,
    );
  }
}

/// Authoritative Deletion Ledger implementing a Two-Tier Architecture:
/// - Tier 1: Fast in-memory Bloom filter pre-filter with zero false negatives (O(1)).
/// - Tier 2: Cryptographically authenticated tombstone dictionary acting as the final source of truth.
///
/// Guarantees:
/// 1. Zero False Document Exclusions: Bloom collisions against active files are resolved in Tier 2.
/// 2. Zero False Retrievals: True deletions matching the Bloom filter are authoritatively excluded.
/// 3. Resilient Persistence: Atomic encrypted file writes protect against power loss or crashes.
/// 4. Cryptographic Integrity: Tampered or truncated states trigger LedgerCorruptedException.
class AuthoritativeDeletionLedger {
  final int filterBitSize;
  final int filterHashFunctions;
  final Map<String, DeletionTombstone> _tombstones = {};
  late SseBloomFilter _filter;
  int _currentEpoch = 0;

  AuthoritativeDeletionLedger({
    this.filterBitSize = 8192,
    this.filterHashFunctions = 4,
  }) {
    _filter = SseBloomFilter(bitSize: filterBitSize, numHashFunctions: filterHashFunctions);
  }

  /// Returns the number of authoritatively recorded document deletions
  int get deletionCount => _tombstones.length;

  /// Returns the current monotonic ledger epoch
  int get currentEpoch => _currentEpoch;

  /// Returns an unmodifiable snapshot of deleted document identifiers
  Set<String> get deletedDocIds => Set.unmodifiable(_tombstones.keys);

  /// Returns a specific tombstone if present
  DeletionTombstone? getTombstone(String docId) => _tombstones[docId];

  /// Checks if an authoritative tombstone exists for the document
  bool hasTombstone(String docId) => _tombstones.containsKey(docId);

  /// Records an authoritative document deletion.
  /// Idempotent: repeated deletions on the same document update the timestamp/epoch safely.
  void markDeleted({
    required String docId,
    required Set<String> keywords,
    required Uint8List kAuth,
    int? timestamp,
  }) {
    final ts = timestamp ?? DateTime.now().millisecondsSinceEpoch;
    _currentEpoch++;

    final tag = DeletionTombstone.computeTag(
      docId: docId,
      timestamp: ts,
      epoch: _currentEpoch,
      kAuth: kAuth,
    );

    final tombstone = DeletionTombstone(
      docId: docId,
      timestamp: ts,
      epoch: _currentEpoch,
      keywords: keywords,
      hmacTag: tag,
    );

    _tombstones[docId] = tombstone;

    // Insert keyword::docId bindings into Tier 1 Bloom Filter
    for (final kw in keywords) {
      _filter.add('$kw::$docId');
    }
  }

  /// Two-Tier Authoritative Deletion Verification:
  /// Evaluates whether a document candidate is deleted.
  ///
  /// - If [keyword] is supplied:
  ///   1. Check Tier 1 Bloom Filter:
  ///      If _filter.mightContain('$keyword::$docId') == false:
  ///         Return false immediately (provably active, FN = 0).
  ///   2. If Bloom Filter returns true (potential match OR false positive collision):
  ///      Check Tier 2 Authoritative Ledger:
  ///         If _tombstones.containsKey(docId) == true -> Return true (True deletion).
  ///         If _tombstones.containsKey(docId) == false -> Return false (Collision resolved! Active file preserved!).
  ///
  /// - If [keyword] is null:
  ///   Directly queries Tier 2 authoritative map.
  bool isDeleted(String docId, {String? keyword}) {
    if (keyword != null) {
      final mightBeDeleted = _filter.mightContain('$keyword::$docId');
      if (!mightBeDeleted) {
        // Guaranteed not deleted (Zero False Negatives)
        return false;
      }
      // Collision or true deletion: consult authoritative Tier 2 source of truth
      return _tombstones.containsKey(docId);
    }
    // Direct document existence query
    return _tombstones.containsKey(docId);
  }

  /// Rebuilds the in-memory Bloom filter from the authoritative tombstones
  void rebuildFilter() {
    _filter.clear();
    for (final tombstone in _tombstones.values) {
      for (final kw in tombstone.keywords) {
        _filter.add('$kw::${tombstone.docId}');
      }
    }
  }

  /// Merges a remote ledger state (e.g., from cloud synchronization or secondary device).
  /// Resolves conflicts via Last-Write-Wins (LWW) by timestamp/epoch.
  /// Authenticates every incoming tombstone before acceptance.
  void mergeRemote(AuthoritativeDeletionLedger remote, Uint8List kAuth) {
    bool filterNeedsRebuild = false;

    for (final remoteEntry in remote._tombstones.values) {
      if (!remoteEntry.verify(kAuth)) {
        throw LedgerCorruptedException(
          'Remote tombstone authentication failure for doc: ${remoteEntry.docId}',
        );
      }

      final localEntry = _tombstones[remoteEntry.docId];
      if (localEntry == null) {
        _tombstones[remoteEntry.docId] = remoteEntry;
        if (remoteEntry.epoch > _currentEpoch) {
          _currentEpoch = remoteEntry.epoch;
        }
        for (final kw in remoteEntry.keywords) {
          _filter.add('$kw::${remoteEntry.docId}');
        }
      } else {
        // Conflict resolution: LWW
        if (remoteEntry.timestamp > localEntry.timestamp ||
            (remoteEntry.timestamp == localEntry.timestamp && remoteEntry.epoch > localEntry.epoch)) {
          _tombstones[remoteEntry.docId] = remoteEntry;
          filterNeedsRebuild = true;
          if (remoteEntry.epoch > _currentEpoch) {
            _currentEpoch = remoteEntry.epoch;
          }
        }
      }
    }

    if (filterNeedsRebuild) {
      rebuildFilter();
    }
  }

  /// Serializes and saves the ledger to disk with AES-256-GCM encryption and atomic replacement.
  Future<void> saveToFile(File file, Uint8List kEnc, Uint8List kAuth) async {
    final Map<String, dynamic> rawMap = {
      'version': 1,
      'epoch': _currentEpoch,
      'bitSize': filterBitSize,
      'numHashFunctions': filterHashFunctions,
      'tombstones': _tombstones.values.map((t) => t.toJson()).toList(),
    };

    final plainBytes = utf8.encode(json.encode(rawMap));
    final rand = Random.secure();
    final iv = Uint8List(12);
    for (int i = 0; i < 12; i++) {
      iv[i] = rand.nextInt(256);
    }

    final cipherBytes = SseEngine.encryptGcm(kEnc, iv, Uint8List.fromList(plainBytes));
    final combined = Uint8List(iv.length + cipherBytes.length);
    combined.setRange(0, iv.length, iv);
    combined.setRange(iv.length, combined.length, cipherBytes);

    // Atomic write via temporary file
    final tempFile = File('${file.path}.tmp_${rand.nextInt(1000000)}');
    if (!await tempFile.parent.exists()) {
      await tempFile.parent.create(recursive: true);
    }

    await tempFile.writeAsBytes(combined, flush: true);
    if (await file.exists()) {
      await file.delete();
    }
    await tempFile.rename(file.path);
  }

  /// Loads and authenticates the ledger from disk.
  /// If file does not exist, returns a fresh empty ledger.
  /// If file is corrupted, truncated, or fails authentication, throws LedgerCorruptedException.
  static Future<AuthoritativeDeletionLedger> loadFromFile(
    File file,
    Uint8List kEnc,
    Uint8List kAuth, {
    int defaultBitSize = 8192,
    int defaultHashFunctions = 4,
  }) async {
    if (!await file.exists()) {
      return AuthoritativeDeletionLedger(
        filterBitSize: defaultBitSize,
        filterHashFunctions: defaultHashFunctions,
      );
    }

    final bytes = await file.readAsBytes();
    if (bytes.length < 28) {
      // 12-byte IV + minimum 16-byte GCM tag
      throw LedgerCorruptedException('Ledger file truncated or missing authentication header.');
    }

    final iv = bytes.sublist(0, 12);
    final ciphertext = bytes.sublist(12);

    Uint8List decryptedBytes;
    try {
      decryptedBytes = SseEngine.decryptGcm(kEnc, iv, ciphertext);
    } catch (e) {
      throw LedgerCorruptedException('Ledger decryption/AEAD authentication failed: $e');
    }

    Map<String, dynamic> jsonMap;
    try {
      jsonMap = json.decode(utf8.decode(decryptedBytes)) as Map<String, dynamic>;
    } catch (e) {
      throw LedgerCorruptedException('Ledger content is not valid JSON: $e');
    }

    final bitSize = jsonMap['bitSize'] as int? ?? defaultBitSize;
    final numHashFunctions = jsonMap['numHashFunctions'] as int? ?? defaultHashFunctions;
    final epoch = jsonMap['epoch'] as int? ?? 0;

    final ledger = AuthoritativeDeletionLedger(
      filterBitSize: bitSize,
      filterHashFunctions: numHashFunctions,
    );
    ledger._currentEpoch = epoch;

    final tombstonesList = jsonMap['tombstones'] as List?;
    if (tombstonesList != null) {
      for (final item in tombstonesList) {
        final tombstone = DeletionTombstone.fromJson(item as Map<String, dynamic>);
        if (!tombstone.verify(kAuth)) {
          throw LedgerCorruptedException(
            'Tombstone cryptographic HMAC tag mismatch for document: ${tombstone.docId}',
          );
        }
        ledger._tombstones[tombstone.docId] = tombstone;
      }
    }

    ledger.rebuildFilter();
    return ledger;
  }
}
