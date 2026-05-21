# 🎨 Design Tokens

> **Owner:** Person B
> **Purpose:** Single source of truth สำหรับ colors, typography, spacing
>
> Exported จาก Figma → ใช้ใน Web (Tailwind), Mobile (Flutter)

---

## Why Design Tokens?

ก่อนหน้านี้:
- Figma มี color `#2D6A4F`
- Web ใช้ `forest-500: '#2D6A4F'`
- Mobile ใช้ `Color(0xFF2D6A4F)`
- เปลี่ยนสี = แก้ 3 ที่

ตอนนี้:
- Figma export → `tokens.json`
- Web + Mobile import มาใช้
- เปลี่ยนสี = แก้ 1 ที่

---

## Folder Structure

```
packages/design-tokens/
├── README.md                (this file)
├── package.json
├── tokens/
│   ├── colors.json
│   ├── typography.json
│   ├── spacing.json
│   ├── shadows.json
│   └── animations.json
├── src/
│   ├── index.ts             Re-exports for TypeScript
│   ├── colors.ts
│   ├── typography.ts
│   └── ...
└── build/                   Generated outputs
    ├── tailwind.config.cjs  For Web (Person A imports)
    ├── flutter_theme.dart   For Mobile (User imports)
    └── tokens.css           Plain CSS variables
```

---

## Tokens Format

### Colors
```json
// tokens/colors.json
{
  "brand": {
    "primary": {
      "value": "#2D6A4F",
      "type": "color",
      "description": "Forest Green — main brand color"
    },
    "secondary": {
      "value": "#74C0FC",
      "type": "color",
      "description": "Sky Blue — accent"
    }
  },
  "neutral": {
    "50": { "value": "#FAFAF8", "type": "color" },
    "100": { "value": "#F5F5F0", "type": "color" },
    "200": { "value": "#E8E8E0", "type": "color" },
    "300": { "value": "#D1D1C7", "type": "color" },
    "400": { "value": "#A8A89E", "type": "color" },
    "500": { "value": "#7A7A70", "type": "color" },
    "600": { "value": "#5C5C52", "type": "color" },
    "700": { "value": "#3E3E36", "type": "color" },
    "800": { "value": "#27271F", "type": "color" },
    "900": { "value": "#14140F", "type": "color" }
  },
  "forest": {
    "50":  { "value": "#F0F9F4", "type": "color" },
    "100": { "value": "#D6F0DE", "type": "color" },
    "300": { "value": "#7CC59A", "type": "color" },
    "500": { "value": "#2D6A4F", "type": "color" },
    "700": { "value": "#1B4332", "type": "color" },
    "900": { "value": "#0D2E1F", "type": "color" }
  },
  "semantic": {
    "success": { "value": "#52B788", "type": "color" },
    "warning": { "value": "#F4A261", "type": "color" },
    "error":   { "value": "#E63946", "type": "color" },
    "info":    { "value": "#74C0FC", "type": "color" }
  }
}
```

### Typography
```json
// tokens/typography.json
{
  "fontFamily": {
    "thai":   { "value": "'Sarabun', sans-serif", "type": "fontFamily" },
    "latin":  { "value": "'Inter', sans-serif",   "type": "fontFamily" },
    "display":{ "value": "'Space Grotesk', sans-serif", "type": "fontFamily" }
  },
  "fontSize": {
    "xs":   { "value": "0.75rem",  "type": "fontSize" },
    "sm":   { "value": "0.875rem", "type": "fontSize" },
    "base": { "value": "1rem",     "type": "fontSize" },
    "lg":   { "value": "1.125rem", "type": "fontSize" },
    "xl":   { "value": "1.25rem",  "type": "fontSize" },
    "2xl":  { "value": "1.5rem",   "type": "fontSize" },
    "3xl":  { "value": "1.875rem", "type": "fontSize" },
    "4xl":  { "value": "2.25rem",  "type": "fontSize" },
    "5xl":  { "value": "3rem",     "type": "fontSize" },
    "6xl":  { "value": "3.75rem",  "type": "fontSize" }
  },
  "fontWeight": {
    "normal":   { "value": 400 },
    "medium":   { "value": 500 },
    "semibold": { "value": 600 },
    "bold":     { "value": 700 }
  },
  "lineHeight": {
    "tight":   { "value": 1.2 },
    "normal":  { "value": 1.5 },
    "relaxed": { "value": 1.75 }
  }
}
```

### Spacing
```json
// tokens/spacing.json
{
  "0":   { "value": "0",      "type": "spacing" },
  "1":   { "value": "0.25rem","type": "spacing" },
  "2":   { "value": "0.5rem", "type": "spacing" },
  "3":   { "value": "0.75rem","type": "spacing" },
  "4":   { "value": "1rem",   "type": "spacing" },
  "6":   { "value": "1.5rem", "type": "spacing" },
  "8":   { "value": "2rem",   "type": "spacing" },
  "12":  { "value": "3rem",   "type": "spacing" },
  "16":  { "value": "4rem",   "type": "spacing" },
  "24":  { "value": "6rem",   "type": "spacing" }
}
```

---

## How Person B Exports from Figma

### Option 1: Figma Tokens Plugin (Recommended)
1. Install [Figma Tokens](https://www.figma.com/community/plugin/843461159747178978/Figma-Tokens) plugin
2. Define styles ใน Figma
3. Use plugin to export to JSON
4. Save to `tokens/*.json`
5. Commit + PR

### Option 2: Manual Export
1. Open Figma file
2. Inspect color/text styles
3. Manually update `tokens/*.json`
4. Commit + PR

---

## How Web (Person A) Imports

### `apps/web/tailwind.config.ts`
```ts
import type { Config } from 'tailwindcss';
import { colors, fontFamily, fontSize, spacing } from '@carbonscan/design-tokens';

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors,         // ใช้ได้ทันที: bg-forest-500, text-brand-primary
      fontFamily,
      fontSize,
      spacing,
    },
  },
};

export default config;
```

### Usage
```tsx
<button className="bg-forest-500 text-white font-medium">
  Click me
</button>
```

---

## How Mobile (User) Imports

### `apps/mobile/lib/core/theme/app_theme.dart`
```dart
import 'package:flutter/material.dart';

class AppColors {
  static const forest500 = Color(0xFF2D6A4F);
  static const forest700 = Color(0xFF1B4332);
  static const sky500 = Color(0xFF74C0FC);
  static const neutral50 = Color(0xFFFAFAF8);
  // ... auto-generated from colors.json
}

class AppTypography {
  static const fontThai = 'Sarabun';
  static const fontLatin = 'Inter';

  static const TextStyle h1 = TextStyle(
    fontSize: 48,
    fontWeight: FontWeight.bold,
    fontFamily: fontLatin,
  );
}

class AppSpacing {
  static const double s = 8;
  static const double m = 16;
  static const double l = 24;
}
```

⚠️ Mobile import เป็น **manual** ตอนนี้ (Phase 1 อาจสร้าง build script auto-gen)

---

## Build Script (Generate Outputs)

```bash
# From repo root
pnpm --filter design-tokens build

# Generates:
# - tailwind.config.cjs (auto)
# - flutter_theme.dart (auto)
# - tokens.css (CSS variables)
```

---

## Brand Direction (สำหรับ Person B)

### Theme
**"Sustainable Tech — Trustworthy, Modern, Premium"**

### Color Inspiration
- **Forest Green (#2D6A4F)** — Nature, growth, sustainability
- **Sky Blue (#74C0FC)** — Tech, transparency, clarity
- **Off-white (#FAFAF8)** — Clean, premium
- **Charcoal (#14140F)** — Text, hierarchy

### Avoid
- Neon green (looks "eco" but cheap)
- Pure black (#000000) — use #14140F instead
- Too many colors (max 5)

### Typography Inspiration
- **Sarabun** — Modern Thai, good readability
- **Inter** — Tech industry standard
- **Space Grotesk** — สำหรับ display/heading เท่าๆ

### Style Direction
- Minimalist + Glass morphism
- Subtle gradient (forest → sky)
- Generous whitespace
- Lottie/SVG animations (ไม่ใช่ stock photo)

---

📖 **See also:**
- [docs/design/DESIGN_SYSTEM.md](../../docs/design/DESIGN_SYSTEM.md) — Full design system
- [docs/design/BRAND.md](../../docs/design/BRAND.md) — Brand guidelines
- [apps/web/README.md](../../apps/web/README.md) — Web usage
- [apps/mobile/README.md](../../apps/mobile/README.md) — Mobile usage
