# Brand Assets — CarbonScan AI

> Official brand assets for the CarbonScan AI project (NSC 2026 หมวด 14)
>
> **Owner:** Person B (Designer) — primary author of the logo + brand identity

---

## Files

| File | Purpose | Format |
|---|---|---|
| `logo.png` | Master logo (full color) | PNG, 1024×1024 (approx) |

Web-deployed copy:
| Location | Purpose |
|---|---|
| `apps/web/public/logo.png` | Used as favicon, OG image, header/footer mark on Web |

---

## Logo Concept

The logo represents the **complete CarbonScan AI value proposition** in a single illustration:

| Visual Element | Meaning |
|---|---|
| 🌳 **Tree** (center) | The subject we measure — economic forest species in Thailand |
| 🤲 **Cupped hands** (cradling the tree) | Community stewardship — เกษตรกร/ชุมชนปลูกและดูแลต้นไม้ |
| 🌍 **Earth/globe** (background sphere) | Global climate impact + Sustainability goal |
| 💨 **CO₂ bubbles** (with arrows) | Carbon sequestration — what the tree absorbs |
| 📈 **Bar chart + magnifying glass** (right) | Data analytics + AI measurement — our technology layer |
| 🟢 **Green-to-blue gradient** (outer ring) | Nature → Technology (the bridge our platform builds) |

This single image communicates: **"Community trees + AI measurement = Verified carbon credit"** — the exact narrative we tell in the NSC Proposal.

---

## Color Palette (from logo)

- **Forest greens** — multiple shades for tree foliage depth
- **Sky blue** — gradient + earth background
- **CO₂ teal/dark green** — bubbles
- **Brown** — tree trunk

These align with the brand tokens defined in [`packages/design-tokens/`](../../packages/design-tokens/):
- `forest-500: #2D6A4F`
- `sky-500: #74C0FC`
- `forest-900: #0D2E1F` (trunk-like dark)

---

## Where the Logo Appears

### Web Dashboard (`apps/web/`)
- **Browser tab favicon** — via `metadata.icons.icon` in `src/app/layout.tsx`
- **Header logo** (size: 36×36 px) — `src/app/page.tsx` header `<Link href="/">`
- **Footer logo** (size: 28×28 px) — `src/app/page.tsx` footer
- **Social share preview** (OG image) — via `metadata.openGraph.images` and `metadata.twitter.images`

### Mobile App (`apps/mobile/`)
- TODO Phase 1: copy to `apps/mobile/assets/icons/app_icon.png`
- Used for Android launcher icon + iOS app icon + splash screen

### Proposal Document (`proposal/`)
- Cover page (full size)
- Section header watermark (small, top-right)

### Pitch Deck (Phase 4)
- Title slide (large)
- Footer of every slide (small)

---

## Variants Needed (Phase 1 — Person B to produce)

The single PNG works for Web/Mobile but Phase 1 will need:

| Variant | Purpose | Format |
|---|---|---|
| **SVG** version | Scalable for any size (favicons, print) | SVG |
| **Monochrome** (single color, Forest Green) | For watermarks, low-color print, letterheads | PNG + SVG |
| **Reversed** (white on dark) | For dark mode UI, dark slide backgrounds | PNG + SVG |
| **Wordmark** (logo + "CarbonScan AI" text) | For wide layouts, headers | PNG + SVG |
| **Mark only** (no background) | For tight contexts where the circle frame is too much | PNG + SVG |
| **Favicon ICO** (multi-res 16/32/48 px) | Legacy browser tabs | ICO |
| **App icon PNG** (1024×1024 + 512×512 + 180×180) | iOS App Store, Android Play | PNG |

> 📝 The current `logo.png` is the "rich illustration" master.
> When at very small sizes (16-32px favicon), it may lose detail.
> A simplified "mark only" SVG variant would render cleaner at favicon size — TODO Phase 1.

---

## Logo Usage Rules

### Clear Space
Maintain clear space equal to **0.5× the logo's height** on all sides — no other elements should crowd inside this padding.

### Minimum Size
- Digital: **24px** (smallest readable)
- Print: **15mm** wide

### Do NOT
- ❌ Stretch or distort proportions
- ❌ Change the colors (use approved variants only)
- ❌ Add drop shadow, glow, or filters
- ❌ Place on busy photographic backgrounds (use a solid color or subtle overlay)
- ❌ Crop the logo
- ❌ Rotate

### Do
- ✅ Use the provided color variants
- ✅ Place on clean backgrounds (white, sand, dark)
- ✅ Scale uniformly (hold Shift in design tools)
- ✅ Use SVG when scaling is needed

---

## File Management

### When updating the logo
1. Person B uploads new version to `assets/brand/logo.png` (and new variants when available)
2. Person B copies the same `logo.png` to `apps/web/public/logo.png` (or uses a build script)
3. Bump version in this README's changelog (below)
4. Open PR with title `design(brand): update logo to vX.Y`

### Changelog

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-05-21 | Initial logo from Person B (PNG, 1024×1024) — circular composition with tree + hands + CO₂ + analytics |

---

📖 **See also:**
- [docs/design/BRAND.md](../../docs/design/BRAND.md) — Brand voice, tone, broader identity guidelines
- [docs/design/DESIGN_SYSTEM.md](../../docs/design/DESIGN_SYSTEM.md) — UI component design system
- [packages/design-tokens/](../../packages/design-tokens/) — Machine-readable color/typography tokens
