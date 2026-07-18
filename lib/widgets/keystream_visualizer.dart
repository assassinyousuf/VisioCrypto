import 'package:flutter/material.dart';
import 'dart:typed_data';
import '../crypto/hgcc_engine.dart';

/// State representation of the HGCC cipher for visualization.
class HgccVisualState {
  final int lfsr;
  final Uint8List ca;
  final BigInt chaos;
  final int counter;

  HgccVisualState({
    required this.lfsr,
    required this.ca,
    required this.chaos,
    required this.counter,
  });
}

/// A futuristic, glassmorphic visualizer showing the HGCC internal states.
class KeystreamVisualizer extends StatelessWidget {
  final HgccVisualState? state;

  const KeystreamVisualizer({Key? key, this.state}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final activeState = state;
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.4),
        borderRadius: BorderRadius.circular(16.0),
        border: Border.all(
          color: Colors.cyan.withOpacity(0.2),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.cyan.withOpacity(0.05),
            blurRadius: 10,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: activeState != null ? Colors.cyan : Colors.grey,
                      shape: BoxShape.circle,
                      boxShadow: activeState != null
                          ? [
                              BoxShadow(
                                color: Colors.cyan.withOpacity(0.8),
                                blurRadius: 6,
                                spreadRadius: 1,
                              ),
                            ]
                          : [],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'HGCC Keystream Engine Visualizer',
                    style: TextStyle(
                      color: Colors.cyan[100],
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.8,
                    ),
                  ),
                ],
              ),
              Text(
                activeState != null
                    ? 'TICK: ${activeState.counter}'
                    : 'IDLE',
                style: TextStyle(
                  color: activeState != null ? Colors.cyanAccent : Colors.grey[500],
                  fontSize: 11,
                  fontFamily: 'monospace',
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const Divider(color: Colors.cyan, height: 20, thickness: 0.5),
          
          // 1. LFSR Hex Display
          _buildLFSRDisplay(activeState),
          const SizedBox(height: 16),

          // 2. Cellular Automaton Grid
          _buildCAGrid(activeState),
          const SizedBox(height: 16),

          // 3. Chaos Attractor Attenuator
          _buildChaosDisplay(activeState),
        ],
      ),
    );
  }

  Widget _buildLFSRDisplay(HgccVisualState? state) {
    final hexString = state != null
        ? state.lfsr.toRadixString(16).toUpperCase().padLeft(16, '0')
        : '0000000000000000';
    
    // Split into 4 chunks for readability
    final chunk1 = hexString.substring(0, 4);
    final chunk2 = hexString.substring(4, 8);
    final chunk3 = hexString.substring(8, 12);
    final chunk4 = hexString.substring(12, 16);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.memory, size: 14, color: Colors.indigo[300]),
            const SizedBox(width: 6),
            const Text(
              '64-bit Galois LFSR State (Hex)',
              style: TextStyle(color: Colors.grey, fontSize: 11),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.3),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.indigo.withOpacity(0.2)),
          ),
          child: Center(
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _hexChunk(chunk1, Colors.indigoAccent),
                _hexSpace(),
                _hexChunk(chunk2, Colors.indigoAccent),
                _hexSpace(),
                _hexChunk(chunk3, Colors.cyanAccent),
                _hexSpace(),
                _hexChunk(chunk4, Colors.cyanAccent),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _hexChunk(String text, Color color) {
    return Text(
      text,
      style: TextStyle(
        color: color,
        fontSize: 14,
        fontFamily: 'monospace',
        fontWeight: FontWeight.bold,
        letterSpacing: 1.5,
      ),
    );
  }

  Widget _hexSpace() {
    return const Padding(
      padding: EdgeInsets.symmetric(horizontal: 4.0),
      child: Text('-', style: TextStyle(color: Colors.grey, fontSize: 14)),
    );
  }

  Widget _buildCAGrid(HgccVisualState? state) {
    final caList = state?.ca ?? Uint8List(64);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.grid_on, size: 14, color: Colors.teal[300]),
            const SizedBox(width: 6),
            const Text(
              'Rule 30 CA 512-bit Array (Circular byte-wise)',
              style: TextStyle(color: Colors.grey, fontSize: 11),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.all(8.0),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.3),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.teal.withOpacity(0.2)),
          ),
          child: GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: 64,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 16,
              crossAxisSpacing: 3,
              mainAxisSpacing: 3,
            ),
            itemBuilder: (context, index) {
              final val = caList[index];
              // Map byte value to colors: 0 (dark) to 255 (teal glow)
              final intensity = val / 255.0;
              final color = state != null
                  ? Color.lerp(Colors.teal.shade900.withOpacity(0.3), Colors.tealAccent, intensity)!
                  : Colors.grey.shade900;
              
              return AnimatedContainer(
                duration: const Duration(milliseconds: 100),
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(2),
                  boxShadow: state != null && val > 200
                      ? [
                          BoxShadow(
                            color: Colors.tealAccent.withOpacity(0.5),
                            blurRadius: 4,
                            spreadRadius: 0.5,
                          ),
                        ]
                      : [],
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildChaosDisplay(HgccVisualState? state) {
    final maxChaos = HgccEngine.primeP;
    final chaosVal = state?.chaos ?? BigInt.zero;
    
    // Convert to double percentage safely
    double percentage = 0.0;
    if (chaosVal > BigInt.zero && maxChaos > BigInt.zero) {
      percentage = (chaosVal.toDouble() / maxChaos.toDouble()).clamp(0.0, 1.0);
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.grain, size: 14, color: Colors.purple[300]),
            const SizedBox(width: 6),
            const Text(
              'Discrete Prime Logistic Map State (53-bit Attractor)',
              style: TextStyle(color: Colors.grey, fontSize: 11),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.3),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.purple.withOpacity(0.2)),
          ),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      'X_n: $chaosVal',
                      style: TextStyle(
                        color: Colors.purple[100],
                        fontSize: 10.5,
                        fontFamily: 'monospace',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${(percentage * 100).toStringAsFixed(2)}%',
                    style: const TextStyle(
                      color: Colors.purpleAccent,
                      fontSize: 11,
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Stack(
                children: [
                  Container(
                    height: 6,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: Colors.purple.shade900.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                  FractionallySizedBox(
                    widthFactor: percentage,
                    child: Container(
                      height: 6,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Colors.purple, Colors.pinkAccent],
                        ),
                        borderRadius: BorderRadius.circular(3),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.pinkAccent.withOpacity(0.5),
                            blurRadius: 4,
                            spreadRadius: 0.5,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}
