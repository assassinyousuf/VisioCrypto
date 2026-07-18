import 'dart:typed_data';
import 'package:crypto/crypto.dart';

/// Implementation of RFC 5869 HMAC-based Extract-and-Expand Key Derivation Function (HKDF).
class Hkdf {
  final Hash hash;
  final int hashLength;

  Hkdf(this.hash) : hashLength = hash.convert(const []).bytes.length;

  /// HKDF-Extract: PRK = HMAC-Hash(salt, IKM)
  Uint8List extract(Uint8List salt, Uint8List ikm) {
    final effectiveSalt = salt.isEmpty ? Uint8List(hashLength) : salt;
    final hmac = Hmac(hash, effectiveSalt);
    final prk = hmac.convert(ikm);
    return Uint8List.fromList(prk.bytes);
  }

  /// HKDF-Expand: OKM = HKDF-Expand(PRK, info, L)
  Uint8List expand(Uint8List prk, Uint8List info, int length) {
    final hmac = Hmac(hash, prk);
    final n = (length / hashLength).ceil();
    if (n > 255) {
      throw ArgumentError('Output length too long for HKDF-Expand ($length bytes).');
    }

    final result = BytesBuilder();
    Uint8List t = Uint8List(0);

    for (int i = 1; i <= n; i++) {
      final builder = BytesBuilder();
      builder.add(t);
      builder.add(info);
      builder.addByte(i);
      t = Uint8List.fromList(hmac.convert(builder.toBytes()).bytes);
      result.add(t);
    }

    final okm = result.takeBytes();
    return Uint8List.sublistView(okm, 0, length);
  }

  /// Convenient single-step HKDF (Extract and then Expand)
  Uint8List deriveKey(Uint8List salt, Uint8List ikm, Uint8List info, int length) {
    final prk = extract(salt, ikm);
    return expand(prk, info, length);
  }
}
