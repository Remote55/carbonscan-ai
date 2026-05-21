import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/camera/presentation/camera_screen.dart';
import '../../features/results/presentation/results_screen.dart';
import '../../features/tree_scan/presentation/tree_scan_screen.dart';
import '../../shared/screens/home_screen.dart';

/// Build the app's GoRouter instance.
///
/// Routes:
///   /                            → HomeScreen
///   /scan                        → TreeScanScreen (wizard / checklist)
///   /scan/camera                 → CameraScreen (multi-shot capture)
///   /scan/results/:jobId         → ResultsScreen (pipeline status + results)
GoRouter buildRouter(Ref ref) {
  return GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(
        path: '/',
        name: 'home',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/scan',
        name: 'scan',
        builder: (context, state) => const TreeScanScreen(),
        routes: [
          GoRoute(
            path: 'camera',
            name: 'camera',
            builder: (context, state) => const CameraScreen(),
          ),
          GoRoute(
            path: 'results/:jobId',
            name: 'results',
            builder: (context, state) {
              final jobId = state.pathParameters['jobId']!;
              return ResultsScreen(jobId: jobId);
            },
          ),
        ],
      ),
    ],
    errorBuilder: (context, state) => _ErrorScreen(error: state.error),
  );
}

class _ErrorScreen extends StatelessWidget {
  const _ErrorScreen({this.error});
  final Exception? error;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Text('Navigation error: ${error ?? "unknown"}'),
      ),
    );
  }
}
