import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';

/// Step-by-step wizard before opening the camera.
class TreeScanScreen extends StatelessWidget {
  const TreeScanScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('สแกนต้นไม้ใหม่'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'ก่อนเริ่มสแกน',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 8),
              const Text(
                'เตรียมตัวก่อนสแกนเพื่อความแม่นยำ',
                style: TextStyle(color: AppColors.stone),
              ),
              const SizedBox(height: 32),
              const _ChecklistItem(
                icon: Icons.wb_sunny_outlined,
                title: 'แสงสว่างพอ',
                description: 'หลีกเลี่ยงสแกนตอนเย็นหรือฝนตก',
              ),
              const _ChecklistItem(
                icon: Icons.straighten,
                title: 'ยืนห่างต้นไม้ 2-5 เมตร',
                description: 'เห็นทั้งต้นในเฟรมได้',
              ),
              const _ChecklistItem(
                icon: Icons.threed_rotation,
                title: 'เดินรอบต้นไม้',
                description: 'ถ่ายจากหลายมุม 30-50 รูป',
              ),
              const _ChecklistItem(
                icon: Icons.location_on_outlined,
                title: 'เปิด GPS',
                description: 'พิกัดต้นไม้จะถูกบันทึกอัตโนมัติ',
              ),
              const Spacer(),
              FilledButton.icon(
                onPressed: () => context.push('/scan/camera'),
                icon: const Icon(Icons.camera_alt),
                label: const Text('เปิดกล้องเริ่มสแกน'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ChecklistItem extends StatelessWidget {
  const _ChecklistItem({
    required this.icon,
    required this.title,
    required this.description,
  });
  final IconData icon;
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.forest500.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: AppColors.forest500, size: 22),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  description,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.stone,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
