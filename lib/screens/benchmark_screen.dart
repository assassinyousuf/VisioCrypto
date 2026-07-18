import 'package:flutter/material.dart';
import '../crypto/benchmark.dart';

class BenchmarkScreen extends StatefulWidget {
  const BenchmarkScreen({Key? key}) : super(key: key);

  @override
  State<BenchmarkScreen> createState() => _BenchmarkScreenState();
}

class _BenchmarkScreenState extends State<BenchmarkScreen> with SingleTickerProviderStateMixin {
  bool _isRunning = false;
  int _activeTab = 0; // 0: Throughput, 1: SSE Metrics

  // Throughput data
  double? _aesCtrSpeed;
  double? _aesGcmSpeed;

  // SSE data
  double? _sseIndexingTime;
  double? _sseTrapdoorRate;

  String _statusText = 'Click "Run Profiler" to measure client-side hardware performance.';
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _startBenchmark() async {
    setState(() {
      _isRunning = true;
      _aesCtrSpeed = null;
      _aesGcmSpeed = null;
      _sseIndexingTime = null;
      _sseTrapdoorRate = null;
      _statusText = 'Initializing 2 MB payload in volatile memory...';
    });
    _animationController.repeat();

    await Future.delayed(const Duration(milliseconds: 500));

    try {
      const payloadSize = 2 * 1024 * 1024; // 2 MB buffer

      setState(() {
        _statusText = 'Profiling AES-CTR-256 (Streaming Encrypt)...';
      });
      await Future.delayed(const Duration(milliseconds: 200));
      final ctr = CryptoBenchmark.benchmarkAesCtr(payloadSize);

      setState(() {
        _statusText = 'Profiling AES-GCM-256 (Authenticated Encrypt)...';
      });
      await Future.delayed(const Duration(milliseconds: 200));
      final gcm = CryptoBenchmark.benchmarkAesGcm(payloadSize);

      setState(() {
        _statusText = 'Profiling SSE Indexing (1,000 keyword inserts)...';
      });
      await Future.delayed(const Duration(milliseconds: 200));
      final sseIndex = CryptoBenchmark.benchmarkSseIndexing();

      setState(() {
        _statusText = 'Profiling SSE Trapdoor generation (10,000 derivations)...';
      });
      await Future.delayed(const Duration(milliseconds: 200));
      final sseTrap = CryptoBenchmark.benchmarkSseTrapdoor();

      setState(() {
        _isRunning = false;
        _aesCtrSpeed = ctr;
        _aesGcmSpeed = gcm;
        _sseIndexingTime = sseIndex;
        _sseTrapdoorRate = sseTrap;
        _statusText = 'Profiling completed successfully!';
      });
      _animationController.forward(from: 0.0);
    } catch (e) {
      setState(() {
        _isRunning = false;
        _statusText = 'Error running benchmark: $e';
      });
      _animationController.stop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF07040C),
              Color(0xFF030A10),
            ],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header
                Row(
                  children: [
                    ShaderMask(
                      shaderCallback: (bounds) => const LinearGradient(
                        colors: [Colors.cyanAccent, Colors.pinkAccent],
                      ).createShader(bounds),
                      child: const Text(
                        'SECURE SSE',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.w900,
                          letterSpacing: 2,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Text(
                      'PROFILER',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 24,
                        fontWeight: FontWeight.w300,
                        letterSpacing: 2,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Empirical evaluation of client-side encryption and database indexing latency.',
                  style: TextStyle(
                    color: Colors.grey[400],
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 20),

                // Status Panel
                Container(
                  padding: const EdgeInsets.all(16.0),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.02),
                    borderRadius: BorderRadius.circular(16.0),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.06),
                      width: 1.0,
                    ),
                  ),
                  child: Row(
                    children: [
                      if (_isRunning)
                        RotationTransition(
                          turns: _animationController,
                          child: const Icon(
                            Icons.sync,
                            color: Colors.cyanAccent,
                            size: 24,
                          ),
                        )
                      else
                        const Icon(
                          Icons.speed,
                          color: Colors.pinkAccent,
                          size: 24,
                        ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _isRunning ? 'Profiling Hardware...' : 'Status',
                              style: const TextStyle(
                                color: Colors.white70,
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 0.5,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              _statusText,
                              style: TextStyle(
                                color: _isRunning ? Colors.cyanAccent[100] : Colors.white,
                                fontSize: 13,
                                fontWeight: FontWeight.w400,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Tabs Selector
                Row(
                  children: [
                    _buildTabButton(0, 'Symmetric Throughput'),
                    const SizedBox(width: 12),
                    _buildTabButton(1, 'SSE Database Metrics'),
                  ],
                ),
                const SizedBox(height: 16),

                // Chart Panel
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(20.0),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(24.0),
                      border: Border.all(
                        color: Colors.cyan.withOpacity(0.12),
                        width: 1.5,
                      ),
                    ),
                    child: _aesCtrSpeed == null && !_isRunning
                        ? _buildEmptyState()
                        : (_activeTab == 0 ? _buildThroughputChart() : _buildSseChart()),
                  ),
                ),
                const SizedBox(height: 20),

                // Run Button
                ElevatedButton(
                  onPressed: _isRunning ? null : _startBenchmark,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.transparent,
                    padding: const EdgeInsets.symmetric(vertical: 16.0),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16.0),
                      side: BorderSide(
                        color: _isRunning ? Colors.grey : Colors.cyanAccent,
                        width: 1.5,
                      ),
                    ),
                    shadowColor: Colors.cyanAccent.withOpacity(0.3),
                    elevation: 5,
                  ),
                  child: Ink(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(16.0),
                    ),
                    child: Container(
                      alignment: Alignment.center,
                      child: Text(
                        _isRunning ? 'PROFILING IN PROGRESS...' : 'RUN BENCHMARK SUITE',
                        style: TextStyle(
                          color: _isRunning ? Colors.grey : Colors.cyanAccent,
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.5,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTabButton(int index, String label) {
    final active = _activeTab == index;
    return Expanded(
      child: GestureDetector(
        onTap: () {
          setState(() {
            _activeTab = index;
          });
        },
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12.0),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: active ? Colors.cyan.withOpacity(0.15) : Colors.white.withOpacity(0.02),
            borderRadius: BorderRadius.circular(12.0),
            border: Border.all(
              color: active ? Colors.cyanAccent.withOpacity(0.5) : Colors.white.withOpacity(0.06),
              width: 1.0,
            ),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: active ? Colors.white : Colors.white60,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          Icons.analytics_outlined,
          size: 64,
          color: Colors.cyan.withOpacity(0.2),
        ),
        const SizedBox(height: 16),
        const Text(
          'No Profiler Data Available',
          style: TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Run the suite to profile client-side indexing and decryption benchmarks on this hardware architecture.',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: Colors.grey[500],
            fontSize: 13,
          ),
        ),
      ],
    );
  }

  Widget _buildThroughputChart() {
    final maxSpeed = [
      _aesCtrSpeed ?? 1.0,
      _aesGcmSpeed ?? 1.0,
    ].reduce((a, b) => a > b ? a : b);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'File Encryption Throughput',
          style: TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Throughput speeds (MB/s) of pure-Dart software cipher implementations.',
          style: TextStyle(
            color: Colors.grey[500],
            fontSize: 11,
          ),
        ),
        const SizedBox(height: 24),
        
        Expanded(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildBar(
                name: 'AES-CTR-256 (Streaming)',
                speed: _aesCtrSpeed,
                maxSpeed: maxSpeed,
                unit: 'MB/s',
                color1: Colors.cyan,
                color2: Colors.tealAccent,
                description: 'Used for size-preserving document streaming.',
              ),
              _buildBar(
                name: 'AES-GCM-256 (Authenticated)',
                speed: _aesGcmSpeed,
                maxSpeed: maxSpeed,
                unit: 'MB/s',
                color1: Colors.pink,
                color2: Colors.orangeAccent,
                description: 'Used for secure searchable index blocks.',
              ),
            ],
          ),
        ),
        const Divider(color: Colors.cyan, height: 32, thickness: 0.5),
        Text(
          'NOTE: In pure Dart AOT-compiled execution, streaming AES-CTR slightly outperforms AES-GCM due to GCM\'s Galois field authentication tag overhead (GHASH evaluations).',
          style: TextStyle(
            color: Colors.grey[500],
            fontSize: 10,
            height: 1.4,
          ),
        ),
      ],
    );
  }

  Widget _buildSseChart() {
    final maxVal = [
      _sseIndexingTime ?? 1.0,
      (_sseTrapdoorRate ?? 1000.0) / 1000.0 // Scaled to look nice
    ].reduce((a, b) => a > b ? a : b);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Symmetric Searchable Index Latency',
          style: TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Measures index encryption (lower is better) and trapdoor generation rate.',
          style: TextStyle(
            color: Colors.grey[500],
            fontSize: 11,
          ),
        ),
        const SizedBox(height: 24),
        
        Expanded(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildBar(
                name: 'SSE Index Compilation (1K words)',
                speed: _sseIndexingTime,
                maxSpeed: maxVal,
                unit: 'ms',
                color1: Colors.purple,
                color2: Colors.indigoAccent,
                description: 'Time to generate trapdoors and encrypt lookup table (lower is faster).',
                invertRatio: true,
              ),
              _buildBar(
                name: 'Trapdoor Derivation Rate',
                speed: _sseTrapdoorRate,
                maxSpeed: maxVal * 1000.0,
                unit: 'ops/ms',
                color1: Colors.green,
                color2: Colors.greenAccent,
                description: 'Number of HMAC-SHA256 operations generated per millisecond.',
              ),
            ],
          ),
        ),
        const Divider(color: Colors.cyan, height: 32, thickness: 0.5),
        Text(
          'NOTE: Rapid trapdoor generation (~10,000 ops/ms) ensures search terms are encrypted instantaneously, preserving a zero-latency client search experience.',
          style: TextStyle(
            color: Colors.grey[500],
            fontSize: 10,
            height: 1.4,
          ),
        ),
      ],
    );
  }

  Widget _buildBar({
    required String name,
    required double? speed,
    required double maxSpeed,
    required String unit,
    required Color color1,
    required Color color2,
    required String description,
    bool invertRatio = false,
  }) {
    double ratio = 0.05;
    if (speed != null) {
      ratio = speed / maxSpeed;
      if (invertRatio) {
        ratio = 1.0 - ratio;
      }
      ratio = ratio.clamp(0.05, 1.0);
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              name,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 13,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              speed != null ? '${speed.toStringAsFixed(2)} $unit' : 'Pending...',
              style: TextStyle(
                color: speed != null ? color2 : Colors.grey,
                fontFamily: 'monospace',
                fontSize: 13,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Text(
          description,
          style: TextStyle(
            color: Colors.grey[400],
            fontSize: 11,
          ),
        ),
        const SizedBox(height: 8),
        Stack(
          children: [
            Container(
              height: 12,
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.02),
                borderRadius: BorderRadius.circular(6),
              ),
            ),
            AnimatedContainer(
              duration: const Duration(milliseconds: 800),
              curve: Curves.easeOutCubic,
              height: 12,
              width: speed != null
                  ? (MediaQuery.of(context).size.width - 80) * ratio
                  : 10.0,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [color1, color2],
                ),
                borderRadius: BorderRadius.circular(6),
                boxShadow: speed != null
                    ? [
                        BoxShadow(
                          color: color2.withOpacity(0.4),
                          blurRadius: 6,
                          spreadRadius: 1,
                        ),
                      ]
                    : [],
              ),
            ),
          ],
        ),
      ],
    );
  }
}
