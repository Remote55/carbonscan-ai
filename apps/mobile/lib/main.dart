/// CarbonScan AI Mobile App — entry point.
///
/// Run:
///   flutter run                            (dev)
///   flutter build apk --release            (Android release)
///   flutter build ios --release            (iOS, needs Mac)
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app.dart';
import 'core/config/app_config.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load env-specific config (dev/staging/prod)
  await AppConfig.load();

  // TODO Phase 1: Initialize Supabase, Sentry, etc.
  // await Supabase.initialize(url: ..., anonKey: ...);

  runApp(
    const ProviderScope(
      child: CarbonScanApp(),
    ),
  );
}
