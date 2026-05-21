# 🎨 Design System

> **Owner:** Person B (Design Lead)
> **Implementation:** Person A (Frontend)

---

## Philosophy

**"Sustainable Tech, Trustworthy by Design"**

ทุก design decision ต้องตอบโจทย์:
1. **Trustworthy** — กรรมการ NSC / Auditor / โรงงาน เห็นแล้วเชื่อมั่น
2. **Accessible** — เกษตรกร/ชุมชนใช้ได้ (ปุ่มใหญ่, font ชัด)
3. **Modern** — ทันสมัย แต่ไม่เกินเลย (ไม่ใช่ neon, ไม่ใช่ "เด็ก")
4. **Performant** — เร็ว, ไม่ลื่นไหล

---

## Core Tokens

ดูใน `packages/design-tokens/` (machine-readable)

| Token | Value | Usage |
|---|---|---|
| `brand.primary` | #2D6A4F | Logo, primary buttons, accents |
| `brand.secondary` | #74C0FC | Links, info badges |
| `neutral.50-900` | grayscale | Backgrounds, text |
| `semantic.success` | #52B788 | Success states |
| `semantic.error` | #E63946 | Error states |

---

## Typography Scale

```
H1 (Display)   48px  / 56 lh  / Bold     / Space Grotesk
H2             36px  / 44 lh  / Bold
H3             28px  / 36 lh  / Semibold
H4             24px  / 32 lh  / Semibold
Body Large     18px  / 28 lh  / Regular  / Inter (EN) / Sarabun (TH)
Body           16px  / 24 lh  / Regular
Body Small     14px  / 20 lh  / Regular
Caption        12px  / 16 lh  / Regular
```

---

## Spacing System (8px Grid)

| Token | Pixels | Use |
|---|---|---|
| `space-1` | 4px | Tight (icons inside button) |
| `space-2` | 8px | Default gap |
| `space-3` | 12px | Card padding sm |
| `space-4` | 16px | Default padding |
| `space-6` | 24px | Section spacing sm |
| `space-8` | 32px | Section spacing |
| `space-12` | 48px | Section spacing lg |
| `space-16` | 64px | Page section |

---

## Components

### Buttons
- **Primary** — solid forest green
- **Secondary** — outlined
- **Ghost** — text only
- **Sizes** — sm (32px), md (40px), lg (48px)
- **States** — default, hover, active, disabled, loading

### Cards
- **Border:** 1px solid neutral-200
- **Radius:** 12px
- **Padding:** space-6 (24px)
- **Shadow:** subtle (0 2px 4px rgba(0,0,0,0.05))

### Form Inputs
- **Height:** 40px (md)
- **Border:** 1px solid neutral-300
- **Focus:** forest-500 ring
- **Error:** error-500 border + helper text

### Modal/Dialog
- **Backdrop:** rgba(0,0,0,0.4)
- **Max-width:** 600px (md), 800px (lg)
- **Animation:** fade + scale (200ms)

---

## Iconography

ใช้ **Lucide Icons** (https://lucide.dev/)
- Stroke width: 1.5px
- Size: 16/20/24 px
- Color: inherit

Special icons (custom SVG จาก Person B):
- `tree-icon.svg`
- `carbon-leaf.svg`
- `gps-pin.svg`

---

## Layout Patterns

### Dashboard Layout
```
┌────────────────────────────────────────┐
│ Header (64px, sticky)                  │
├──────┬─────────────────────────────────┤
│      │                                  │
│ Side │  Main content area               │
│ bar  │  (max-width: 1280px, centered)  │
│ 240px│                                  │
│      │                                  │
└──────┴─────────────────────────────────┘
```

### Marketplace Card
```
┌──────────────────┐
│ [Tree Image]     │  16:9 ratio
│                  │
├──────────────────┤
│ Tectona grandis  │  H4
│ ไม้สัก เชียงใหม่   │  Body small
│                  │
│ 137 kgCO2eq      │  H3 forest-500
│ ฿274             │  Body neutral-700
│                  │
│ [ดูรายละเอียด]    │  Button md
└──────────────────┘
```

---

## Accessibility (a11y)

- ✅ Color contrast WCAG AA (4.5:1 text, 3:1 UI)
- ✅ Keyboard navigation (Tab, Esc, Enter)
- ✅ Focus indicators visible
- ✅ Screen reader labels (aria-label)
- ✅ Form validation messages clear
- ✅ Alt text บนทุก image

---

## Responsive Breakpoints

```css
sm:  640px   /* mobile landscape */
md:  768px   /* tablet portrait */
lg:  1024px  /* tablet landscape, small laptop */
xl:  1280px  /* desktop */
2xl: 1536px  /* large desktop */
```

Mobile-first approach.

---

## Animation Principles

- **Duration:** 150ms (micro), 250ms (default), 400ms (large)
- **Easing:** `cubic-bezier(0.4, 0, 0.2, 1)` (ease-out)
- **Lottie:** สำหรับ illustrations เคลื่อนไหว
- **Page transitions:** Subtle fade + slight slide

❌ **Don't:**
- Bouncy springs (looks childish)
- > 500ms animations (slow feeling)
- Excessive auto-play (annoying)

---

## Brand Voice (Copy)

**Tone:**
- เป็นมิตร แต่ไม่กันเอง
- มืออาชีพ แต่ไม่จริงจังเกินไป
- เน้นข้อเท็จจริง

**ตัวอย่าง:**
- ✅ "สแกนต้นไม้ของคุณ — เริ่มต้นในไม่กี่วินาที"
- ❌ "มาช่วยกันลดโลกร้อนนะคะะ!! 🌍"
- ✅ "เราคำนวณคาร์บอนของต้นไม้ด้วย AI + สมการมาตรฐาน TGO"
- ❌ "เทคโนโลยีสุดล้ำ AI ขั้นเทพ"

---

## Logo Usage

### Primary Logo
- minimum size: 32px height
- minimum clear space: 0.5× logo height ทุกด้าน

### Variations
- Full color (default)
- Monochrome (เมื่อ background สี)
- Reverse (สีขาว บน dark background)

❌ **Don't:**
- Stretch
- Recolor
- Add effects (shadow, glow)
- Place on busy background

---

## Print/Export Guidelines

สำหรับ Proposal Document และ Pitch Deck:
- **PDF:** Embedded fonts
- **Margins:** 2.54 cm (1 inch) ทุกด้าน
- **Page numbers:** Bottom-right
- **Header:** Project name + section
- **Footer:** Date + page #

---

📖 **See also:**
- [docs/design/BRAND.md](BRAND.md) — Brand identity guidelines
- [packages/design-tokens/](../../packages/design-tokens/) — Tokens source
- Figma file: (link จาก Person B)
