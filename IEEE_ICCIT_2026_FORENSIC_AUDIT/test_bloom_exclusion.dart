import 'dart:io';
import 'dart:typed_data';
import '../lib/crypto/sse_engine.dart';

void main() async {
  // Create a Bloom filter and fill it until we get a false positive
  final filter = SseBloomFilter(bitSize: 256, numHashFunctions: 3); // small filter to easily trigger FP
  
  // Add 40 deleted items
  for (int i = 0; i < 40; i++) {
    filter.add('secret::deleted_file_$i.txt');
  }

  // Now find a non-deleted file that triggers a false positive
  String? fpDoc;
  for (int i = 0; i < 10000; i++) {
    final candidate = 'active_file_$i.txt';
    if (filter.mightContain('secret::$candidate')) {
      fpDoc = candidate;
      print('Found false positive document candidate: $fpDoc');
      break;
    }
  }

  if (fpDoc == null) {
    print('No FP found');
    return;
  }

  // Create mock index file
  final tempDir = await Directory.systemTemp.createTemp('sse_fp_test');
  final indexFile = File('${tempDir.path}/index.db');
  final masterKey = Uint8List(64);
  final salt = Uint8List(16);

  // Index active document
  await SseEngine.indexDocument(
    indexFile: indexFile,
    documentPath: fpDoc,
    keywords: {'secret'},
    masterKey: masterKey,
    salt: salt,
  );

  // Search with deletion filter
  final results = await SseEngine.searchIndex(
    indexFile: indexFile,
    keyword: 'secret',
    masterKey: masterKey,
    salt: salt,
    deletionFilter: filter,
  );

  print('Search results for keyword "secret": $results');
  if (results.contains(fpDoc)) {
    print('CORRECT: Active document was retained.');
  } else {
    print('CRITICAL DEFECT: Active document was FALSELY EXCLUDED due to Bloom filter false positive!');
  }

  await tempDir.delete(recursive: true);
}
