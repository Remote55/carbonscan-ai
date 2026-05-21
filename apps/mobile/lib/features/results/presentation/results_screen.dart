import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';

/// Results screen after the ML pipeline finishes.
///
/// TODO Phase 2-3:
/// - Poll Job status via WebSocket
/// - Show pipeline progress (8 stages)
/// - Display final results: DBH, Height, Volume, Carbon, CO₂eq
/// - Charts (fl_chart) for breakdown
/// - Share / Save as PDF
class ResultsScreen extends ConsumerWidget {
  const ResultsScreen({super.key, required this.jobId});

  final String jobId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ผลการสแกน'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: AppColors.warning.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.timelapse, size: 16, color: AppColors.warning),
                    SizedBox(width: 6),
                    Text(
                      'กำลังประมวลผล...',
                      style: TextStyle(
                        color: AppColors.warning,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Job ID: $jobId',
                style: const TextStyle(
                  fontFamily: 'monospace',
                  color: AppColors.stone,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 32),
              const Text(
                'ขั้นตอนการประมวลผล',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              const _PipelineStage(name: 'Photogrammetry (COLMAP)', done: true),
              const _PipelineStage(name: 'Ground Classification', done: true),
              const _PipelineStage(name: 'Tree Segmentation', done: false, current: true),
              const _PipelineStage(name: 'Wood-Leaf Separation (AI)', done: false),
              const _PipelineStage(name: 'QSM Volume', done: false),
              const _PipelineStage(name: 'Carbon Calculation', done: false),
            ],
          ),
        ),
      ),
    );
  }
}

class _PipelineStage extends StatelessWidget {
  const _PipelineStage({
    required this.name,
    required this.done,
    this.current = false,
  });

  final String name;
  final bool done;
  final bool current;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(
            done
                ? Icons.check_circle
                : current
                    ? Icons.radio_button_checked
                    : Icons.radio_button_unchecked,
            color: done
                ? AppColors.success
                : current
                    ? AppColors.warning
                    : AppColors.stone,
          ),
          const SizedBox(width: 12),
          Text(
            name,
            style: TextStyle(
              fontSize: 15,
              fontWeight: current ? FontWeight.w600 : FontWeight.w400,
              color: done ? AppColors.charcoal : AppColors.stone,
            ),
          ),
        ],
      ),
    );
  }
}
