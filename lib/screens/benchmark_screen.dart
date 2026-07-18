import 'package:flutter/material.dart';
import '../crypto/benchmark.dart';

class BenchmarkScreen extends StatefulWidget {
  const BenchmarkScreen({Key? key}) : super(key: key);

  @override
  State<BenchmarkScreen> createState() => _BenchmarkScreenState();
}

class _BenchmarkScreenState extends State<BenchmarkScreen> with SingleTickerProviderStateMixin {
  bool _isRunning = false;
  double? _hgccSpeed;
  double? _aesSpeed;
  double? _chachaSpeed;
  String _statusText = 'Click "Run Profiler" to measure hardware performance.';
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
      _hgccSpeed = null;
      _aesSpeed = null;
      _chachaSpeed = null;
      _statusText = 'Initializing 2 MB mock payload in memory...';
    });
    _animationController.repeat();

    // Give UI a chance to render spinner
    await Future.delayed(const Duration(milliseconds: 500));

    try {
      const payloadSize = 2 * 1024 * 1024; // 2 MB test buffer

      setState(() {
        _statusText = 'Profiling HGCC (Galois-Cellular)...';
      });
      await Future.delayed(const Duration(milliseconds: 200));
      final hgcc = CryptoBenchmark.benchmarkHGCC(payloadSize);

      setState(() {
        _statusText = 'Profiling AES-256 (Pure-Dart Block)...';
      });
      await Future.delayed(const Duration(milliseconds: 200));
      final aes = CryptoBenchmark.benchmarkAES256(payloadSize);

      setState(() {
        _statusText = 'Profiling ChaCha20 (Pure-Dart Stream)...';
      });
      await Future.delayed(const Duration(milliseconds: 200));
      final chacha = CryptoBenchmark.benchmarkChaCha20(payloadSize);

      setState(() {
        _isRunning = false;
        _hgccSpeed = hgcc;
        _aesSpeed = aes;
        _chachaSpeed = chacha;
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
    final maxSpeed = [_hgccSpeed ?? 1.0, _aesSpeed ?? 1.0, _chachaSpeed ?? 1.0].reduce((a, b) => a > b ? a : b);

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF0D0B18), // deep dark violet
              Color(0xFF07121A), // deep dark blue-teal
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
                        'PERFORMANCE',
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
                  'Empirical hardware benchmarks executed in volatile RAM.',
                  style: TextStyle(
                    color: Colors.grey[400],
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 24),

                // Benchmark Status Panel
                Container(
                  padding: const EdgeInsets.all(16.0),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.03),
                    borderRadius: BorderRadius.circular(16.0),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.08),
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
                const SizedBox(height: 24),

                // Chart Panel
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(20.0),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(24.0),
                      border: Border.all(
                        color: Colors.cyan.withOpacity(0.15),
                        width: 1.5,
                      ),
                    ),
                    child: _hgccSpeed == null && !_isRunning
                        ? _buildEmptyState()
                        : _buildChart(maxSpeed),
                  ),
                ),
                const SizedBox(height: 24),

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

  Widget _buildEmptyState() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          Icons.analytics_outlined,
          size: 64,
          color: Colors.cyan.withOpacity(0.3),
        ),
        const SizedBox(height: 16),
        const Text(
          'No Benchmark Data',
          style: TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Run the suite to measure and compare encryption throughput speeds (MB/s) on this device.',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: Colors.grey[500],
            fontSize: 13,
          ),
        ),
      ],
    );
  }

  Widget _buildChart(double maxSpeed) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Throughput Speed Comparison',
          style: TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Higher values indicate faster processing speeds.',
          style: TextStyle(
            color: Colors.grey[500],
            fontSize: 11,
          ),
        ),
        const SizedBox(height: 24),
        
        // Bars
        Expanded(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildBar(
                name: 'HGCC (VisioCrypt)',
                speed: _hgccSpeed,
                maxSpeed: maxSpeed,
                color1: Colors.cyan,
                color2: Colors.tealAccent,
                description: 'Galois-Cellular Cascade Cipher (Pure Dart)',
              ),
              _buildBar(
                name: 'ChaCha20 (PointyCastle)',
                speed: _chachaSpeed,
                maxSpeed: maxSpeed,
                color1: Colors.pink,
                color2: Colors.orangeAccent,
                description: 'ARX Stream Cipher (Pure Dart)',
              ),
              _buildBar(
                name: 'AES-256 (PointyCastle)',
                speed: _aesSpeed,
                maxSpeed: maxSpeed,
                color1: Colors.purple,
                color2: Colors.indigoAccent,
                description: 'Standard Block Cipher (Pure Dart)',
              ),
            ],
          ),
        ),
        
        const Divider(color: Colors.cyan, height: 32, thickness: 0.5),
        
        // Note
        Text(
          'NOTE: Stream ciphers (HGCC, ChaCha20) generally process sequential data bytes faster in pure software environments than block ciphers (AES) because they bypass block structuring, padding, and S-box lookup tables.',
          style: TextStyle(
            color: Colors.grey[500],
            fontSize: 10.5,
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
    required Color color1,
    required Color color2,
    required String description,
  }) {
    final double ratio = speed != null ? (speed / maxSpeed).clamp(0.05, 1.0) : 0.05;
    
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
              speed != null ? '${speed.toStringAsFixed(2)} MB/s' : 'Pending...',
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
