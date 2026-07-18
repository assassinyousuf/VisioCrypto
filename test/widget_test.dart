import 'package:flutter_test/flutter_test.dart';
import 'package:visiocrypt/main.dart';

void main() {
  testWidgets('VisioCrypt app renders and dashboard header is visible', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const VisioCryptApp());

    // Verify that our application title header exists
    expect(find.text('VISIO'), findsOneWidget);
    expect(find.text('CRYPT'), findsOneWidget);
  });
}
