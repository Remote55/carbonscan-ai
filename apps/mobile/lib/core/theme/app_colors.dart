import 'package:flutter/material.dart';

/// CarbonScan AI brand colors.
///
/// Source of truth: packages/design-tokens/tokens/colors.json
/// Matches Web Tailwind config (apps/web/tailwind.config.ts).
abstract final class AppColors {
  AppColors._();

  // --- Forest Green (Primary) ---
  static const Color forest50 = Color(0xFFF0F9F4);
  static const Color forest100 = Color(0xFFD6F0DE);
  static const Color forest300 = Color(0xFF7CC59A);
  static const Color forest500 = Color(0xFF2D6A4F); // Primary brand
  static const Color forest700 = Color(0xFF1B4332);
  static const Color forest900 = Color(0xFF0D2E1F);

  // --- Sky Blue (Accent) ---
  static const Color sky300 = Color(0xFF7DD3FC);
  static const Color sky500 = Color(0xFF74C0FC); // Brand secondary
  static const Color sky700 = Color(0xFF0369A1);

  // --- Neutrals ---
  static const Color sand = Color(0xFFFAFAF8); // Page bg (light)
  static const Color stone = Color(0xFF5C5C52); // Secondary text
  static const Color charcoal = Color(0xFF14140F); // Body text
  static const Color cloud = Color(0xFFE9F5EE); // Subtle bg

  // --- Semantic ---
  static const Color success = Color(0xFF52B788);
  static const Color warning = Color(0xFFF4A261);
  static const Color error = Color(0xFFE63946);
  static const Color info = Color(0xFF74C0FC);
}
