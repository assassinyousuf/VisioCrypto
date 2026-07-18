import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'screens/home_screen.dart';
import 'screens/benchmark_screen.dart';

void main() {
  runApp(const VisioCryptApp());
}

class VisioCryptApp extends StatelessWidget {
  const VisioCryptApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VisioCrypt',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF07050F),
        colorScheme: const ColorScheme.dark(
          primary: Colors.cyanAccent,
          secondary: Colors.pinkAccent,
          surface: Color(0xFF100E1C),
        ),
        textTheme: GoogleFonts.outfitTextTheme(
          ThemeData.dark().textTheme,
        ),
        cardTheme: CardThemeData(
          color: const Color(0xFF121020),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16.0),
            side: BorderSide(
              color: Colors.white.withOpacity(0.05),
              width: 1.0,
            ),
          ),
        ),
      ),
      home: const MainNavigationHolder(),
    );
  }
}

class MainNavigationHolder extends StatefulWidget {
  const MainNavigationHolder({Key? key}) : super(key: key);

  @override
  State<MainNavigationHolder> createState() => _MainNavigationHolderState();
}

class _MainNavigationHolderState extends State<MainNavigationHolder> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    HomeScreen(),
    BenchmarkScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          border: Border(
            top: BorderSide(
              color: Colors.white.withOpacity(0.05),
              width: 1.0,
            ),
          ),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) {
            setState(() {
              _currentIndex = index;
            });
          },
          backgroundColor: const Color(0xFF090714),
          selectedItemColor: _currentIndex == 0 ? Colors.cyanAccent : Colors.pinkAccent,
          unselectedItemColor: Colors.grey[500],
          showSelectedLabels: true,
          showUnselectedLabels: false,
          selectedFontSize: 11,
          iconSize: 22,
          type: BottomNavigationBarType.fixed,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.shield_outlined),
              activeIcon: Icon(Icons.shield, color: Colors.cyanAccent),
              label: 'DASHBOARD',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.speed_outlined),
              activeIcon: Icon(Icons.speed, color: Colors.pinkAccent),
              label: 'PROFILER',
            ),
          ],
        ),
      ),
    );
  }
}
