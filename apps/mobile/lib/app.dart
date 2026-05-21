import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import 'core/config/routes.dart';
import 'core/theme/app_theme.dart';

class CarbonScanApp extends ConsumerWidget {
  const CarbonScanApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'CarbonScan AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: ThemeMode.system,
      routerConfig: router,

      // Use Sarabun for Thai + Inter for Latin via Google Fonts
      builder: (context, child) => Theme(
        data: Theme.of(context).copyWith(
          textTheme: GoogleFonts.sarabunTextTheme(Theme.of(context).textTheme),
        ),
        child: child ?? const SizedBox.shrink(),
      ),
    );
  }
}

final routerProvider = Provider<GoRouter>((ref) => buildRouter(ref));
