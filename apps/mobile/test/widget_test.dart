import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:carbonscan_mobile/app.dart';

void main() {
  testWidgets('App boots without exceptions', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: CarbonScanApp()),
    );

    // Wait for go_router to settle.
    await tester.pump(const Duration(milliseconds: 100));

    // Should find the brand name on the home screen
    expect(find.text('CarbonScan AI'), findsOneWidget);
  });

  testWidgets('Home screen has primary CTA', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: CarbonScanApp()),
    );
    await tester.pump(const Duration(milliseconds: 100));

    // FilledButton.icon() wraps the label in a non-trivial widget tree,
    // so just verify the text content is visible somewhere on screen.
    expect(find.text('เริ่มสแกนต้นไม้'), findsOneWidget);
  });
}
