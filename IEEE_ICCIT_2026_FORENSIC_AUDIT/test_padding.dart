import 'dart:convert';
import 'dart:typed_data';
import '../lib/crypto/sse_engine.dart';

void main() {
  final testCounts = [0, 1, 3, 4, 5, 8, 32, 33, 65, 300, 4096, 4097, 5000];
  print('Count | PaddedCapacity | Dummies | Expansion | Bucket Match');
  print('-----------------------------------------------------------');
  for (final c in testCounts) {
    final list = List.generate(c, (i) => 'doc_$i.pdf');
    final padded = SseEngine.padFileList(list);
    final cap = SseEngine.computePaddedCapacity(c);
    final dummies = padded.length - c;
    final exp = c == 0 ? 0.0 : cap / c;
    print('$c | $cap | $dummies | ${exp.toStringAsFixed(2)}x | ${padded.length == cap ? 'MATCH' : 'MISMATCH'}');
  }
}
