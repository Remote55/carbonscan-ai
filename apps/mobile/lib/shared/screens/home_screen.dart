import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 32),

              // Logo + Title
              Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [AppColors.forest500, AppColors.forest700],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Center(
                      child: Text(
                        'C',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'CarbonScan AI',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 48),

              // Hero
              //
              // Was 'แปลงต้นไม้ของคุณ / เป็นรายได้' — turn your trees into
              // income. Every web surface states the opposite: this system is
              // not certification-grade and cannot issue a carbon credit, so
              // there is nothing here to sell. The app promising the one thing
              // the rest of the product spends its copy disclaiming is wrong
              // whether this app is finished or retired.
              Text(
                'วัดคาร์บอนในต้นไม้ของคุณ',
                style: theme.textTheme.displaySmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  height: 1.2,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'สแกนด้วยกล้องมือถือเพื่อประเมินชีวมวลและคาร์บอน '
                '— ไม่ใช่การรับรองคาร์บอนเครดิต',
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                ),
              ),

              const SizedBox(height: 40),

              // Primary CTA
              FilledButton.icon(
                onPressed: () => context.push('/scan'),
                icon: const Icon(Icons.camera_alt_outlined),
                label: const Text('เริ่มสแกนต้นไม้'),
              ),

              const SizedBox(height: 12),

              // Secondary
              OutlinedButton.icon(
                onPressed: () {
                  // TODO Phase 1: navigate to history
                },
                icon: const Icon(Icons.history),
                label: const Text('ดูประวัติการสแกน'),
              ),

              const SizedBox(height: 48),

              // Stats card
              _StatsCard(),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatsCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'สรุปของคุณ',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
            ),
            const SizedBox(height: 16),
            // No revenue tile. It read '฿0 / รายได้' — zero baht of income —
            // which is not a measurement waiting for data but a category this
            // product does not have. There is no credit to sell and no payout
            // to count, so a counter for it only teaches the reader to expect
            // one.
            const Row(
              children: [
                Expanded(child: _StatItem(value: '0', label: 'ต้นไม้ที่สแกน')),
                Expanded(child: _StatItem(value: '0', label: 'kg CO₂eq')),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  const _StatItem({required this.value, required this.label});
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: AppColors.forest500,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(fontSize: 12, color: AppColors.stone),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
