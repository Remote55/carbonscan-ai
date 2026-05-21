import 'package:flutter/material.dart';

/// Convenience wrapper around FilledButton with loading state.
class AppButton extends StatelessWidget {
  const AppButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.loading = false,
    this.variant = AppButtonVariant.primary,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool loading;
  final AppButtonVariant variant;

  @override
  Widget build(BuildContext context) {
    final child = loading
        ? const SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(strokeWidth: 2),
          )
        : icon != null
            ? Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(icon, size: 20),
                  const SizedBox(width: 8),
                  Text(label),
                ],
              )
            : Text(label);

    final effectiveOnPressed = loading ? null : onPressed;

    switch (variant) {
      case AppButtonVariant.primary:
        return FilledButton(onPressed: effectiveOnPressed, child: child);
      case AppButtonVariant.secondary:
        return OutlinedButton(onPressed: effectiveOnPressed, child: child);
      case AppButtonVariant.text:
        return TextButton(onPressed: effectiveOnPressed, child: child);
    }
  }
}

enum AppButtonVariant { primary, secondary, text }
