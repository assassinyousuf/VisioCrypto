import 'package:flutter/material.dart';
import 'dart:typed_data';

/// State representation of the AES-CTR and SSE engine for visualization.
class SseVisualState {
  final Uint8List block;
  final Uint8List hmac;
  final int counter;
  final String keyword;

  SseVisualState({
    required this.block,
    required this.hmac,
    required this.counter,
    required this.keyword,
  });
}

/// A futuristic, glassmorphic visualizer showing standard AES-CTR blocks and HMAC-SHA256 states.
class KeystreamVisualizer extends StatelessWidget {
  final SseVisualState? state;

  const KeystreamVisualizer({Key? key, this.state}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final activeState = state;

    return Container(
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.4),
        borderRadius: BorderRadius.circular(16.0),
        border: Border.all(
          color: Colors.cyan.withOpacity(0.18),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.cyan.withOpacity(0.04),
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
                ],
              ),
              Text(
                activeState != null
                    ? 'INDEXING: ${activeState.keyword.toUpperCase()}'
                    : 'CRYPT ENGINE: IDLE',
                style: TextStyle(
                  color: activeState != null ? Colors.cyanAccent : Colors.grey[500],
                  fontSize: 11,
                  fontFamily: 'monospace',
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.8,
                ),
              ),
            ],
          ),
          const Divider(color: Colors.cyan, height: 20, thickness: 0.5),
          
          // 1. AES Counter Display (128-bit Counter)
          _buildAESCounterDisplay(activeState),
          const SizedBox(height: 16),

          // 2. AES Block State Grid (16 bytes representation)
          _buildBlockGrid(activeState),
          const SizedBox(height: 16),

          // 3. HMAC-SHA256 Running Tag Display
          _buildHmacDisplay(activeState),
        ],
      ),
    );
  }

  Widget _buildAESCounterDisplay(SseVisualState? state) {
    final blockNum = state?.counter ?? 0;
    final counterHex = blockNum.toRadixString(16).toUpperCase().padLeft(32, '0');
    
    final chunk1 = counterHex.substring(0, 8);
    final chunk2 = counterHex.substring(8, 16);
    final chunk3 = counterHex.substring(16, 24);
    final chunk4 = counterHex.substring(24, 32);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          children: [
            Icon(Icons.add_road, size: 14, color: Colors.indigoAccent),
            SizedBox(width: 6),
            Text(
              '128-bit AES-CTR Block Counter (Hex)',
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
        fontSize: 13,
        fontFamily: 'monospace',
        fontWeight: FontWeight.bold,
        letterSpacing: 1.2,
      ),
    );
  }

  Widget _hexSpace() {
    return const Padding(
      padding: EdgeInsets.symmetric(horizontal: 4.0),
      child: Text('-', style: TextStyle(color: Colors.grey, fontSize: 13)),
    );
  }

  Widget _buildBlockGrid(SseVisualState? state) {
    final block = state?.block ?? Uint8List(16);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          children: [
            Icon(Icons.grid_on, size: 14, color: Colors.tealAccent),
            SizedBox(width: 6),
            Text(
              '16-Byte AES State Block Array',
              style: TextStyle(color: Colors.grey, fontSize: 11),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.symmetric(vertical: 10.0, horizontal: 12.0),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.3),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.teal.withOpacity(0.2)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(16, (index) {
              final val = block[index];
              final hexVal = val.toRadixString(16).toUpperCase().padLeft(2, '0');
              final intensity = val / 255.0;
              final textColor = state != null
                  ? Color.lerp(Colors.teal.shade200, Colors.tealAccent, intensity)!
                  : Colors.grey.shade600;

              return Column(
                children: [
                  Text(
                    hexVal,
                    style: TextStyle(
                      color: textColor,
                      fontSize: 10,
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    width: 10,
                    height: 10,
                    decoration: BoxDecoration(
                      color: state != null
                          ? Colors.tealAccent.withOpacity(intensity.clamp(0.2, 1.0))
                          : Colors.grey.shade900,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ],
              );
            }),
          ),
        ),
      ],
    );
  }

  Widget _buildHmacDisplay(SseVisualState? state) {
    final hmac = state?.hmac ?? Uint8List(32);
    final hmacHex = hmac.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          children: [
            Icon(Icons.lock_clock, size: 14, color: Colors.purpleAccent),
            SizedBox(width: 6),
            Text(
              'HMAC-SHA256 Running Authentication Tag',
              style: TextStyle(color: Colors.grey, fontSize: 11),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.3),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.purple.withOpacity(0.2)),
          ),
          child: Text(
            state != null ? hmacHex : '0000000000000000000000000000000000000000000000000000000000000000',
            style: TextStyle(
              color: Colors.purple[100],
              fontSize: 10,
              fontFamily: 'monospace',
              letterSpacing: 1.0,
            ),
            textAlign: TextAlign.center,
          ),
        ),
      ],
    );
  }
}
