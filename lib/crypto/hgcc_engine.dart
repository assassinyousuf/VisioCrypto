import 'dart:typed_data';

/// The Hyper-Dimensional Galois-Cellular Cipher (HGCC) Engine.
/// Combines a 64-bit Galois LFSR, a Rule 30 Cellular Automaton, and a Prime Logistic Map.
class HgccEngine {
  static const int feedbackConstant = 0x800000000000000D;
  static final BigInt primeP = BigInt.parse('9007199254740881');
  static final BigInt bigFour = BigInt.from(4);

  // Cipher state
  int _lfsr = 0;
  
  // Double-buffering for Cellular Automaton to eliminate allocations during ticks
  Uint8List _ca = Uint8List(64);
  Uint8List _caNext = Uint8List(64);
  
  BigInt _chaos = BigInt.zero;
  int _counter = 0;

  int get lfsrState => _lfsr;
  Uint8List get caState => Uint8List.fromList(_ca);
  BigInt get chaosState => _chaos;
  int get counterState => _counter;

  void init(Uint8List masterKey) {
    if (masterKey.length < 64) {
      throw ArgumentError('Master Key must be at least 64 bytes.');
    }

    _ca = Uint8List.fromList(masterKey.sublist(0, 64));
    _caNext = Uint8List(64);

    final bd = ByteData.view(masterKey.buffer, masterKey.offsetInBytes);
    _lfsr = bd.getUint64(0, Endian.big);
    if (_lfsr == 0) {
      _lfsr = 0xACE1ACE1ACE1ACE1;
    }

    final xVal = bd.getUint64(8, Endian.big);
    _chaos = BigInt.from(xVal) % primeP;
    if (_chaos == BigInt.zero) {
      _chaos = BigInt.from(1337);
    }

    _counter = 0;
    for (int k = 0; k < 3072; k++) {
      tick();
    }

    _counter = 0;
  }

  /// Optimized division-free, allocation-free CA evolution
  void evolveSynchronous() {
    final C = _ca;
    final next = _caNext;

    // Handle boundary index 0 (left wraps to 63)
    next[0] = (C[63] ^ (C[0] | C[1])) & 0xFF;

    // Handle middle indices 1..62 without modulo arithmetic
    for (int i = 1; i < 63; i++) {
      next[i] = (C[i - 1] ^ (C[i] | C[i + 1])) & 0xFF;
    }

    // Handle boundary index 63 (right wraps to 0)
    next[63] = (C[62] ^ (C[63] | C[0])) & 0xFF;

    // Swap buffers
    _ca = next;
    _caNext = C;
  }

  int tick() {
    // 1. 64-bit Galois LFSR Step
    final lsb = _lfsr & 1;
    _lfsr = (_lfsr >> 1) & 0x7FFFFFFFFFFFFFFF;
    if (lsb == 1) {
      _lfsr = _lfsr ^ feedbackConstant;
    }

    // 2. Synchronous CA Evolution (Every 8 ticks)
    if (_counter % 8 == 0) {
      evolveSynchronous();
    }

    // 3. Discrete Prime Chaos Map: X_{n+1} = 4 * X_n * (P - X_n) (mod P)
    _chaos = (bigFour * _chaos * (primeP - _chaos)) % primeP;

    // 4. Bit-Folding Mixer
    final lfsrByte = ((_lfsr >> 56) ^ (_lfsr >> 32) ^ (_lfsr >> 8)) & 0xFF;
    final chaosInt = _chaos.toInt();
    final chaosByte = ((chaosInt >> 40) ^ (chaosInt >> 20) ^ chaosInt) & 0xFF;

    final k = ((lfsrByte ^ _ca[_counter % 64]) + chaosByte) & 0xFF;

    _counter = (_counter + 1) & 0xFFFFFFFFFFFFFFFF;
    return k;
  }
}
