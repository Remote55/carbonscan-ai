# TreeQ Forest Editorial Observatory Web Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** นำ Figma “Forest Editorial Observatory” มาปรับใช้กับ Web ทุกหน้าที่อยู่ในขอบเขต โดยรักษา state machine, API contract, evidence และตัวเลขจริงของระบบไว้ครบถ้วน

**Architecture:** แยก visual system เป็น server-compatible primitives, state-aware demo components และ client-only 3D viewer จากนั้นประกอบหน้า Landing, Judge Demo, Results, Auth และ Dashboard ด้วยข้อมูลจาก source of truth เดิม ห้ามคัดลอกตัวเลข frozen result ไปเขียนซ้ำใน JSX; validation metrics อ่านจาก `CORE_DEMO_EVIDENCE` ส่วนผล Judge Demo อ่านจาก artifact `/public/demo/result.json` ผ่าน adapter เดิม

**Tech Stack:** Next.js 14 App Router, React 18, TypeScript strict, Tailwind CSS 3, shadcn/Base UI, Three.js + React Three Fiber, Vitest, React DOM server renderer, Playwright

**Figma:** [TreeQ — Forest Editorial Observatory](https://www.figma.com/design/54IMkjTG5teh8P1ZHairlo)

## Global Constraints

- Web เท่านั้น; ห้ามแก้ Flutter, ML, API schema, worker, allometric formula หรือ evidence generation
- Landing ต้องเป็น Tailwind server component; ห้ามเพิ่ม `'use client'`, styled-jsx หรือ canvas 3D
- `tlsep` เป็น default; PointNet++ เป็น `Experimental`; species stage 7 เป็น `Stub`
- Validation metrics ต้องอ่านจาก `CORE_DEMO_EVIDENCE`: Wood IoU `0.418`, Leaf IoU `0.808`, DBH MAE `1.1673846154 cm`
- Judge frozen artifact ปัจจุบันต้องอ่านจากไฟล์จริง: detected `5`, calculated `3`, excluded `2`, carbon `1,289.74 kg`, CO₂e `4,729.06 kg` หรือ `4.729 tCO₂e`
- Demo upload รับเฉพาะ `.ply`, สูงสุด `100 MB`, สูงสุด `2,000,000` points; ห้ามเสนอ `.las` หรือ `.laz` บน judge path
- ห้ามเปลี่ยน Frozen Evidence เป็น Live ถ้า readiness ไม่ผ่าน และห้ามแสดงผลรวมเมื่อ hash verification ล้มเหลว
- ใช้คำว่า `ต้นไม้ที่คำนวณสำเร็จ` สำหรับ `total_trees`; แสดง detected/measured/excluded แยกกันเมื่อ diagnostics reconcile เท่านั้น
- ห้ามอ้างว่าเป็น certified carbon credit, marketplace หรือการรับรองอย่างเป็นทางการ
- ภาพจาก Wallhaven ใน Figma เป็น visual-direction reference เท่านั้น; production ใช้ภาพที่ทีมเป็นเจ้าของ, สร้างขึ้นใหม่ หรือมีสิทธิ์ใช้งานชัดเจนพร้อม source/license record
- ฟอนต์ judge path ต้อง self-host และ build ได้โดยไม่ต้องดึง font CDN
- Critical content ต้องไม่ถูกตัดที่ `1440×900` และ `1366×768`; ต่ำกว่า `640px` ห้ามเกิด horizontal page scroll
- ทุก interaction ต้องใช้ keyboard ได้, focus ring มองเห็น, contrast ผ่าน WCAG AA และรองรับ `prefers-reduced-motion`

---

## File Map

| Responsibility | Files |
|---|---|
| Fonts and legal visual assets | `src/lib/fonts.ts`, `src/lib/visual-assets.ts`, `src/lib/visual-assets.test.ts`, `src/assets/fonts/*`, `public/visual/forest-observatory/*` |
| Tokens and shared shells | `src/app/globals.css`, `tailwind.config.ts`, `src/components/brand/brand-mark.tsx`, `src/components/layout/*`, `src/components/editorial/*`, `src/components/evidence/*`, `src/components/ui/button.tsx` |
| Landing | `src/app/page.tsx`, `src/app/page.test.tsx` |
| Judge Demo | `src/components/demo/demo-shell.tsx`, `upload-panel.tsx`, `upload-dropzone.tsx`, `mode-badge.tsx`, `status-state.tsx`, existing demo tests |
| Results and Viewer | `src/app/(dashboard)/dashboard/viewer/page.tsx`, `src/components/viewer/viewer-stage.tsx`, `point-cloud-viewer.tsx`, `point-cloud-legend.tsx`, `src/components/demo/result-rail.tsx` |
| Table and provenance | `src/components/demo/tree-result-table.tsx`, `provenance-panel.tsx`, their tests |
| Auth | `src/app/(auth)/layout.tsx`, login/signup files, `src/components/auth/auth-panel.tsx`, tests |
| Dashboard | `src/app/(dashboard)/layout.tsx`, dashboard page, `src/components/dashboard/dashboard-overview.tsx`, `src/lib/frozen-demo-static.ts`, tests |
| Browser and visual gates | `playwright.config.ts`, `e2e/judge-journey.spec.ts` |

---

### Task 1: Freeze baseline and establish legal, offline visual assets

**Files:**
- Create: `apps/web/src/lib/visual-assets.ts`
- Create: `apps/web/src/lib/visual-assets.test.ts`
- Create: `apps/web/public/visual/forest-observatory/ASSETS.md`
- Create: `apps/web/public/visual/forest-observatory/landing-mist.webp`
- Create: `apps/web/public/visual/forest-observatory/judge-road.webp`
- Create: `apps/web/public/visual/forest-observatory/auth-lake.webp`
- Create: `apps/web/public/visual/forest-observatory/dashboard-road.webp`
- Create: `apps/web/src/assets/fonts/OFL-Noto-Serif-Thai.txt`
- Create: `apps/web/src/assets/fonts/OFL-IBM-Plex-Sans-Thai.txt`
- Create: `apps/web/src/assets/fonts/OFL-JetBrains-Mono.txt`
- Create: `apps/web/src/assets/fonts/NotoSerifThai-Variable.ttf`
- Create: `apps/web/src/assets/fonts/IBMPlexSansThai-Regular.ttf`
- Create: `apps/web/src/assets/fonts/IBMPlexSansThai-Medium.ttf`
- Create: `apps/web/src/assets/fonts/IBMPlexSansThai-SemiBold.ttf`
- Create: `apps/web/src/assets/fonts/JetBrainsMono-Variable.ttf`
- Create: `apps/web/src/lib/fonts.ts`
- Modify: `apps/web/src/app/layout.tsx:1`

**Interfaces:**
- Produces: `VISUAL_ASSETS`, `notoSerifThai`, `ibmPlexSansThai`, `jetBrainsMono`
- Consumes: official OFL font files and four newly generated/team-owned forest photographs

- [ ] **Step 1: Capture the pre-redesign baseline**

Run:

```powershell
cd apps/web
npm test -- --run
npm run type-check
npm run build
```

Expected: existing tests, typecheck and build pass before visual work. Record any pre-existing failure in the task log; do not mask it with redesign changes.

- [ ] **Step 2: Write the failing asset-contract test**

```ts
// apps/web/src/lib/visual-assets.test.ts
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { VISUAL_ASSETS } from './visual-assets';

describe('Forest Observatory visual assets', () => {
  it('keeps every production image local and rights-documented', () => {
    for (const asset of Object.values(VISUAL_ASSETS)) {
      expect(asset.src.startsWith('/visual/forest-observatory/')).toBe(true);
      expect(['team-owned', 'generated', 'CC0', 'explicit-license']).toContain(asset.rights);
      expect(existsSync(join(process.cwd(), 'public', asset.src.slice(1)))).toBe(true);
    }
  });
});
```

- [ ] **Step 3: Run the focused test and verify that the missing module fails**

Run: `npm test -- src/lib/visual-assets.test.ts --run`

Expected: FAIL because `./visual-assets` does not exist.

- [ ] **Step 4: Create four original photographic assets with fixed compositions**

Generate one image per prompt; do not include people, logos, text, buildings, measurement lines or point-cloud overlays:

```text
landing-mist.webp: misty evergreen and tropical highland forest at dawn, calm editorial documentary photography, negative space on the left for Thai headline, deep forest green and warm ivory atmosphere, realistic optics, 16:9
judge-road.webp: symmetrical wet road entering a dense forest, centered vanishing point, restrained cinematic contrast, negative space in the upper left, realistic field photography, 16:9
auth-lake.webp: quiet dark-green forest lake with layered trees and gentle reflections, left-side detail and calm negative space, premium editorial nature photography, 16:9
dashboard-road.webp: forest road seen slightly above eye level, center line leading forward, dark canopy with readable midtones, operational field-observatory mood, realistic photography, 16:9
```

Export each to WebP, longest edge `1920px`, quality `82`, and keep each file below `650 KB`. Do not copy the Wallhaven images into the repository.

- [ ] **Step 5: Create the typed asset registry**

```ts
// apps/web/src/lib/visual-assets.ts
type VisualRights = 'team-owned' | 'generated' | 'CC0' | 'explicit-license';

export const VISUAL_ASSETS = {
  landing: { src: '/visual/forest-observatory/landing-mist.webp', rights: 'generated' },
  judge: { src: '/visual/forest-observatory/judge-road.webp', rights: 'generated' },
  auth: { src: '/visual/forest-observatory/auth-lake.webp', rights: 'generated' },
  dashboard: { src: '/visual/forest-observatory/dashboard-road.webp', rights: 'generated' },
} as const satisfies Record<string, { src: string; rights: VisualRights }>;
```

- [ ] **Step 6: Record source, generation date and SHA-256**

Run:

```powershell
Get-FileHash public/visual/forest-observatory/*.webp -Algorithm SHA256
```

Write the returned hashes, the four prompts, generation tool, date and rights basis into `ASSETS.md`. The file must explicitly state that the Wallhaven references are not production assets.

- [ ] **Step 7: Self-host the three font families**

Download the official OFL releases for Noto Serif Thai, IBM Plex Sans Thai and JetBrains Mono, copy their license texts beside the font files, and create:

```ts
// apps/web/src/lib/fonts.ts
import localFont from 'next/font/local';

export const notoSerifThai = localFont({
  src: '../assets/fonts/NotoSerifThai-Variable.ttf',
  variable: '--font-editorial',
  display: 'swap',
});

export const ibmPlexSansThai = localFont({
  src: [
    { path: '../assets/fonts/IBMPlexSansThai-Regular.ttf', weight: '400' },
    { path: '../assets/fonts/IBMPlexSansThai-Medium.ttf', weight: '500' },
    { path: '../assets/fonts/IBMPlexSansThai-SemiBold.ttf', weight: '600' },
  ],
  variable: '--font-ui',
  display: 'swap',
});

export const jetBrainsMono = localFont({
  src: '../assets/fonts/JetBrainsMono-Variable.ttf',
  variable: '--font-technical',
  display: 'swap',
});
```

Replace the Google font imports in `layout.tsx` with these exports. Preserve `<html lang="th">`, metadata behavior and `suppressHydrationWarning`.

- [ ] **Step 8: Prove the route no longer depends on a font CDN**

Run:

```powershell
rg -n "next/font/google|fonts.googleapis.com|fonts.gstatic.com" src
npm test -- src/lib/visual-assets.test.ts --run
npm run type-check
```

Expected: `rg` returns no matches; test and typecheck pass.

- [ ] **Step 9: Commit the asset and font foundation**

```powershell
git add apps/web/src/lib/fonts.ts apps/web/src/lib/visual-assets.ts apps/web/src/lib/visual-assets.test.ts apps/web/src/app/layout.tsx apps/web/src/assets/fonts apps/web/public/visual/forest-observatory
git commit -m "feat(web): add licensed forest visual foundation"
```

---

### Task 2: Implement design tokens and shared editorial components

**Files:**
- Modify: `apps/web/src/app/globals.css:1`
- Modify: `apps/web/tailwind.config.ts:17`
- Modify: `apps/web/src/components/ui/button.tsx:1`
- Create: `apps/web/src/components/brand/brand-mark.tsx`
- Create: `apps/web/src/components/layout/app-header.tsx`
- Create: `apps/web/src/components/layout/compact-workspace-header.tsx`
- Create: `apps/web/src/components/editorial/editorial-section.tsx`
- Create: `apps/web/src/components/evidence/evidence-metric.tsx`
- Create: `apps/web/src/components/evidence/status-state.tsx`
- Create: `apps/web/src/components/editorial/design-system.test.tsx`

**Interfaces:**
- Produces: `BrandMark`, `AppHeader`, `CompactWorkspaceHeader`, `EditorialSection`, `EvidenceMetric`, `StatusState`
- `EvidenceMetricProps = { label: string; value: string; note?: string; tone?: 'paper' | 'dark' | 'lichen' }`
- `StatusStateProps = { label: string; value: string; note?: string; tone: 'ready' | 'warning' | 'unavailable' }`

- [ ] **Step 1: Write the failing shared-component test**

```tsx
// apps/web/src/components/editorial/design-system.test.tsx
import { renderToStaticMarkup } from 'react-dom/server';
import { expect, it } from 'vitest';
import { BrandMark } from '../brand/brand-mark';
import { EvidenceMetric } from '../evidence/evidence-metric';

describe('TreeQ editorial primitives', () => {
  it('renders an accessible brand and explicit evidence labels', () => {
    const markup = renderToStaticMarkup(
      <><BrandMark /><EvidenceMetric label="Wood IoU" value="0.418" note="Wan held-out" /></>,
    );
    expect(markup).toContain('TreeQ Carbon');
    expect(markup).toContain('Wood IoU');
    expect(markup).toContain('0.418');
    expect(markup).toContain('Wan held-out');
  });
});
```

- [ ] **Step 2: Verify the component imports fail**

Run: `npm test -- src/components/editorial/design-system.test.tsx --run`

Expected: FAIL because the shared component files do not exist.

- [ ] **Step 3: Replace global colors with the approved semantic tokens**

Define these variables in `:root` and map Tailwind colors to them:

```css
--forest-ink: #152019;
--deep-forest: #0e2a1d;
--canopy: #214e35;
--moss: #789b3b;
--lichen: #c7d6a1;
--gallery-ivory: #f4f1e8;
--paper: #fcfbf7;
--mist: #d9ded5;
--evidence-amber: #b28a40;
--clay: #a65f46;
--hairline: #d6d7cf;
--radius: 1.25rem;
```

Set `font-sans` to `var(--font-ui)`, `font-display` to `var(--font-editorial)` and `font-mono` to `var(--font-technical)`. Add `.tabular-nums`, `.editorial-eyebrow`, `.focus-ring` and reduced-motion rules; remove the duplicate base blocks and the old glass helpers that are no longer used.

- [ ] **Step 4: Implement shared components with server-safe markup**

Use named exports and no browser hooks. `AppHeader` accepts `tone: 'paper' | 'transparent'` and renders links to `/`, `/#tech`, `/#how`, `/#proof`, `/dashboard/viewer`, `/login` and `/demo`. `CompactWorkspaceHeader` accepts `title`, `mode` and `backHref`. `BrandMark` uses an inline leaf SVG with an accessible text label, not `/logo.png`.

```tsx
export interface EvidenceMetricProps {
  label: string;
  value: string;
  note?: string;
  tone?: 'paper' | 'dark' | 'lichen';
}

export function EvidenceMetric({ label, value, note, tone = 'paper' }: EvidenceMetricProps) {
  return (
    <article data-tone={tone} className="rounded-[1.25rem] border border-hairline p-5">
      <p className="editorial-eyebrow">{label}</p>
      <p className="mt-3 font-display text-3xl tabular-nums">{value}</p>
      {note ? <p className="mt-2 font-mono text-[0.6875rem]">{note}</p> : null}
    </article>
  );
}
```

- [ ] **Step 5: Align Button variants with the Figma library**

Keep the existing Base UI wrapper and add `editorial`, `editorialOutline` and `quiet` variants plus `xl` size. Every variant must retain `focus-visible:ring`, disabled opacity and a minimum height of `44px` for primary judge actions.

- [ ] **Step 6: Run component, type and lint gates**

Run:

```powershell
npm test -- src/components/editorial/design-system.test.tsx --run
npm run type-check
npm run lint
```

Expected: all pass.

- [ ] **Step 7: Commit the shared visual system**

```powershell
git add apps/web/src/app/globals.css apps/web/tailwind.config.ts apps/web/src/components/ui/button.tsx apps/web/src/components/brand apps/web/src/components/layout apps/web/src/components/editorial apps/web/src/components/evidence
git commit -m "feat(web): add forest editorial design system"
```

---

### Task 3: Rebuild Landing as the evidence-led editorial entry

**Files:**
- Modify: `apps/web/src/app/page.tsx:1`
- Create: `apps/web/src/app/page.test.tsx`

**Interfaces:**
- Consumes: `AppHeader`, `EditorialSection`, `EvidenceMetric`, `VISUAL_ASSETS`, `CORE_DEMO_EVIDENCE`
- Produces: server-rendered `/` route with `/demo` as the primary CTA

- [ ] **Step 1: Write the failing Landing truth test**

```tsx
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import HomePage from './page';

describe('Landing evidence contract', () => {
  it('leads to the judge demo and reports validation without rounding', () => {
    const markup = renderToStaticMarkup(<HomePage />);
    expect(markup).toContain('href="/demo"');
    expect(markup).toContain('0.418');
    expect(markup).toContain('0.808');
    expect(markup).toContain('1.1673846154');
    expect(markup).toContain('PointNet++');
    expect(markup).toContain('Experimental');
    expect(markup).toContain('species');
    expect(markup).not.toContain('93.135');
  });
});
```

- [ ] **Step 2: Run the test and confirm the old Landing fails the new composition contract**

Run: `npm test -- src/app/page.test.tsx --run`

Expected: FAIL on the exact new evidence copy or composition labels.

- [ ] **Step 3: Implement the `1440×900` first viewport from Figma node `32:2`**

Use a two-column hero, `next/image` with `VISUAL_ASSETS.landing.src`, `priority`, `sizes="(min-width: 1024px) 48vw, 100vw"`, an ivory background and a dark tonal wash over the image. Keep the primary action `ทดลอง Demo Dataset` linked to `/demo`; keep `อัปโหลด Point Cloud` as a secondary link to `/demo` rather than opening a separate workflow.

```tsx
<section className="grid min-h-[calc(100svh-5rem)] grid-cols-1 gap-8 px-6 py-8 lg:grid-cols-12 lg:px-16">
  <div className="flex flex-col justify-center lg:col-span-6">
    <h1 className="font-display text-5xl leading-[1.12] lg:text-7xl">อ่านคาร์บอนจากโครงสร้างจริงของต้นไม้</h1>
    <div className="mt-8 flex flex-wrap gap-3">
      <Button render={<Link href="/demo" />} variant="editorial" size="xl">ทดลอง Demo Dataset</Button>
      <Button render={<Link href="/demo" />} variant="editorialOutline" size="xl">อัปโหลด Point Cloud</Button>
    </div>
  </div>
  <div className="relative min-h-[24rem] overflow-hidden rounded-[1.75rem] lg:col-span-6">
    <Image src={VISUAL_ASSETS.landing.src} alt="ป่าปกคลุมด้วยหมอก" fill priority sizes="(min-width: 1024px) 48vw, 100vw" className="object-cover" />
    <div className="absolute inset-0 bg-deep-forest/25" />
  </div>
</section>
```

- [ ] **Step 4: Build the evidence strip from generated metrics**

Read `wanHeldOut.woodIoU`, `wanHeldOut.leafIoU` and `demol65.dbhMaeCm` directly from `CORE_DEMO_EVIDENCE`. Render the DBH value in full in the detailed strip; an abbreviated display may appear only if the full value and scope are visible in the same viewport.

- [ ] **Step 5: Recompose lower sections without adding product scope**

Keep exactly four beats: problem, measurement journey, 3D evidence, validation. Describe certification, marketplace, photogrammetry and species classification only as limitations or excluded scope. Remove the Pacifico script accent and the generic equal-weight card grid.

- [ ] **Step 6: Verify server rendering and critical copy**

Run:

```powershell
npm test -- src/app/page.test.tsx --run
rg -n "use client|styled-jsx|<Canvas" src/app/page.tsx
npm run type-check
```

Expected: test and typecheck pass; `rg` returns no matches.

- [ ] **Step 7: Commit Landing**

```powershell
git add apps/web/src/app/page.tsx apps/web/src/app/page.test.tsx
git commit -m "feat(web): rebuild evidence-led landing"
```

---

### Task 4: Restyle Judge Demo without changing its reliability state machine

**Files:**
- Modify: `apps/web/src/components/demo/demo-shell.tsx:150`
- Modify: `apps/web/src/components/demo/upload-panel.tsx:21`
- Modify: `apps/web/src/components/demo/mode-badge.tsx:1`
- Create: `apps/web/src/components/demo/upload-dropzone.tsx`
- Create: `apps/web/src/components/demo/judge-demo-header.tsx`
- Modify: `apps/web/src/components/demo/demo-shell.test.tsx:1`
- Modify: `apps/web/src/components/demo/live-workspace.test.tsx:1`

**Interfaces:**
- Consumes unchanged: `DemoModeState`, `UploadState`, `resolveFrozenDemoLoad`, `uploadErrorMessageTh`
- Produces: `UploadDropzone({ state, onSelect })` and a visual shell matching Figma nodes `33:2` and `43:28`

- [ ] **Step 1: Extend tests before changing markup**

Add assertions that frozen mode contains `FROZEN EVIDENCE — NOT A LIVE RUN`, live mode exposes `.ply` only, the selected file name remains visible while processing, and failed frozen verification renders neither `ต้นไม้ที่คำนวณสำเร็จ` nor carbon totals.

```tsx
expect(frozenMarkup).toContain('FROZEN EVIDENCE — NOT A LIVE RUN');
expect(liveMarkup).toContain('.ply');
expect(liveMarkup).not.toContain('.las');
expect(liveMarkup).not.toContain('.laz');
expect(processingMarkup).toContain('plot.ply');
expect(failedMarkup).not.toContain('ต้นไม้ที่คำนวณสำเร็จ');
expect(failedMarkup).not.toContain('Carbon stock estimate');
```

- [ ] **Step 2: Run focused tests and confirm at least one new assertion fails**

Run:

```powershell
npm test -- src/components/demo/demo-shell.test.tsx src/components/demo/live-workspace.test.tsx --run
```

Expected: FAIL on the new editorial/guidance labels before implementation.

- [ ] **Step 3: Preserve controller and reducer logic byte-for-byte**

Do not modify `DemoShellController`, `demoModeReducer`, `uploadReducer`, `consumeRuntimeHandoff` or API calls. Refactor only rendered markup below `DemoShell` and presentational children.

- [ ] **Step 4: Implement the guided demo header and mode selection**

Render the five-step journey `INPUT → VALIDATE → PIPELINE → RESULT → PROVENANCE`. Frozen Sample is visually primary. Live Upload is a secondary tab only for `production-live` and `local-live`; in frozen fallback, show why live is unavailable and keep the frozen route usable.

- [ ] **Step 5: Extract `UploadDropzone` from `UploadPanel`**

The component must receive the existing `UploadState`, forward the real `File`, preserve `aria-live="polite"`, disable input during upload/processing and print this exact contract from constants: `.ply · 100 MB · 2,000,000 จุด`.

- [ ] **Step 6: Render the current frozen artifact rather than design literals**

The UI must derive `5 detected / 3 calculated / 2 excluded`, `1,289.74 kg C` and `4,729.06 kg CO₂e` through `toResultViewModel(frozenLoad.bundle.result)`. Do not type these numbers directly into `demo-shell.tsx`.

- [ ] **Step 7: Run all demo state tests**

Run:

```powershell
npm test -- src/components/demo src/lib/demo-mode.test.ts src/lib/demo-upload.test.ts src/lib/frozen-demo.test.ts --run
npm run type-check
```

Expected: all pass.

- [ ] **Step 8: Commit Judge Demo**

```powershell
git add apps/web/src/components/demo
git commit -m "feat(web): refine reliable judge demo journey"
```

---

### Task 5: Build the Results Workspace and correct the Viewer result semantics

**Files:**
- Create: `apps/web/src/components/demo/result-rail.tsx`
- Create: `apps/web/src/components/demo/result-rail.test.tsx`
- Create: `apps/web/src/components/viewer/viewer-stage.tsx`
- Modify: `apps/web/src/components/viewer/point-cloud-viewer.tsx:70`
- Modify: `apps/web/src/components/viewer/point-cloud-legend.tsx:9`
- Modify: `apps/web/src/app/(dashboard)/dashboard/viewer/page.tsx:20`

**Interfaces:**
- `ResultRailProps = { view: ResultViewModel; modeLabel: string }`
- `ViewerStageProps = PointCloudViewerProps & { title: string; evidenceLabel: string; children?: ReactNode }`
- Consumes: `toResultViewModel(analysis)` and existing Three.js arrays

- [ ] **Step 1: Write a failing result-rail semantics test**

```tsx
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { toResultViewModel } from '../../lib/result-view-model';
import { ResultRail } from './result-rail';

it('labels measured trees and explains exclusions', () => {
  const view = toResultViewModel({
    summary: { total_trees: 3, measured_trees: 3, detected_trees: 5, excluded_trees: 2, total_carbon_kg: 1289.74, total_co2eq_kg: 4729.06 },
    diagnostics: { excluded_segments: [
      { tree_id: 1, stage: 'qsm', reason_code: 'QSM_INVALID' },
      { tree_id: 4, stage: 'qsm', reason_code: 'QSM_INVALID' },
    ] },
  });
  const markup = renderToStaticMarkup(<ResultRail view={view} modeLabel="Frozen Evidence" />);
  expect(markup).toContain('ต้นไม้ที่คำนวณสำเร็จ');
  expect(markup).toContain('3');
  expect(markup).toContain('5');
  expect(markup).toContain('2');
  expect(markup).not.toContain('จำนวนต้นไม้');
});
```

- [ ] **Step 2: Run the focused test and verify the component is missing**

Run: `npm test -- src/components/demo/result-rail.test.tsx --run`

Expected: FAIL because `result-rail.tsx` does not exist.

- [ ] **Step 3: Implement `ResultRail` from `ResultViewModel` only**

Display CO₂e, carbon, measured count, detected count and excluded count. If `diagnosticsStatus === 'unavailable'`, render `diagnostics unavailable` and omit detected/excluded numbers. Include `ค่าประมาณชีวมวล ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง` in the rail.

- [ ] **Step 4: Wrap the existing Canvas in `ViewerStage`**

Keep `PointCloudViewer` client-only, keep `LINEAR_CLASS_COLORS`, Z-up rotation, orbit/zoom/pan and the existing `CLASS_COLORS`. Add presentation around the Canvas: dark stage, filename/run label, legend, visible controls description and clear `synthetic` label when `loaded === null`.

- [ ] **Step 5: Recompose Viewer page as an 8/4 grid**

For `analysis !== null`, compute `const resultView = toResultViewModel(analysis)` and pass it to both `ResultRail` and `TreeResultTable`. Replace the existing label `จำนวนต้นไม้` with `resultView.countsLabel.measured`. Do not modify file parsing, decimation, API request or error behavior.

- [ ] **Step 6: Keep artifact boundaries visible**

When QSM is absent, print `QSM artifact unavailable`. When the displayed browser PLY hash is not normalized through the backend path, keep the existing warning that the viewer file and provenance input have not been proven identical.

- [ ] **Step 7: Run viewer and view-model tests**

Run:

```powershell
npm test -- src/components/demo/result-rail.test.tsx src/lib/result-view-model.test.ts src/lib/demo-pointcloud.test.ts src/lib/ply-loader.test.ts --run
npm run type-check
```

Expected: all pass.

- [ ] **Step 8: Commit Results Workspace**

```powershell
git add apps/web/src/components/demo/result-rail.tsx apps/web/src/components/demo/result-rail.test.tsx apps/web/src/components/viewer "apps/web/src/app/(dashboard)/dashboard/viewer/page.tsx"
git commit -m "feat(web): build evidence-focused results workspace"
```

---

### Task 6: Restyle Tree Results and Provenance while retaining every limitation

**Files:**
- Modify: `apps/web/src/components/demo/tree-result-table.tsx:16`
- Modify: `apps/web/src/components/demo/provenance-panel.tsx:11`
- Create: `apps/web/src/components/demo/tree-result-table.test.tsx`
- Create: `apps/web/src/components/demo/provenance-panel.test.tsx`

**Interfaces:**
- Consumes unchanged: `ResultViewModel`, `FrozenDemoManifest`
- Produces: unified measured/excluded table and provenance sections matching Figma nodes `36:43` and `36:123`

- [ ] **Step 1: Write table and provenance regression tests**

The table test must assert rows are ordered `1,2,3,4,5`, rows `1` and `4` contain `ไม่รวมผล`, and measured values remain tabular. The provenance test must assert commit, pipeline version, backend, species `stub`, PointNet++ `Experimental`, dataset scope and the non-certification sentence are visible.

```tsx
const view: ResultViewModel = {
  counts: { detected: 5, measured: 3, excluded: 2 },
  countsLabel: { detected: 'ต้นไม้ที่ตรวจพบ', measured: 'ต้นไม้ที่คำนวณสำเร็จ', excluded: 'ไม่รวมผล' },
  diagnosticsStatus: 'available',
  measuredRows: [
    { treeId: 2, dbhCm: 33.62, heightM: 21.35, carbonKg: 484.15, co2eqKg: 1775.21 },
    { treeId: 3, dbhCm: 23.83, heightM: 17.04, carbonKg: 197.3, co2eqKg: 723.44 },
    { treeId: 5, dbhCm: 40.52, heightM: 16.67, carbonKg: 608.29, co2eqKg: 2230.41 },
  ],
  excludedRows: [
    { treeId: 1, stage: 'qsm', reasonCode: 'QSM_INVALID', reasonTh: 'วัดค่า DBH หรือความสูงไม่สำเร็จ' },
    { treeId: 4, stage: 'qsm', reasonCode: 'QSM_INVALID', reasonTh: 'วัดค่า DBH หรือความสูงไม่สำเร็จ' },
  ],
  totalCarbonKg: 1289.74,
  totalCo2eqKg: 4729.06,
  isCertifiedCredit: false,
};
const tableMarkup = renderToStaticMarkup(<TreeResultTable view={view} />);
expect(tableMarkup).toContain('EXCLUDED');
expect(tableMarkup).toContain('1,775.21');
expect(tableMarkup.indexOf('>1<')).toBeLessThan(tableMarkup.indexOf('>2<'));

const provenanceMarkup = renderToStaticMarkup(
  <ProvenancePanel manifest={manifestJson as FrozenDemoManifest} />,
);
expect(provenanceMarkup).toContain('9aaf68d4f65c');
expect(provenanceMarkup).toContain('tlsep');
expect(provenanceMarkup).toContain('stub');
expect(provenanceMarkup).toContain('Experimental');
expect(provenanceMarkup).toContain('ไม่ใช่คาร์บอนเครดิต');
```

- [ ] **Step 2: Run focused tests and verify the missing test surface fails**

Run:

```powershell
npm test -- src/components/demo/tree-result-table.test.tsx src/components/demo/provenance-panel.test.tsx --run
```

Expected: FAIL before the new grouped provenance sections and status column exist.

- [ ] **Step 3: Add a Status column without changing row construction**

Keep the current merge-and-sort algorithm. Render `READY` for measured rows and `EXCLUDED` plus `reasonTh` for excluded rows. At widths below `640px`, keep `min-w-[44rem]` on the table and `overflow-x-auto` on its own container; the page itself must not scroll horizontally.

- [ ] **Step 4: Group provenance into auditable sections**

Render Run identity, input/artifact hashes, pipeline/backend, Git commit, species status, allometric source and limitations. Values must come from `FrozenDemoManifest`; only the static evidence-boundary sentences may be literal copy.

- [ ] **Step 5: Run the focused suite**

Run:

```powershell
npm test -- src/components/demo/tree-result-table.test.tsx src/components/demo/provenance-panel.test.tsx src/components/demo/demo-shell.test.tsx --run
npm run type-check
```

Expected: all pass.

- [ ] **Step 6: Commit table and provenance**

```powershell
git add apps/web/src/components/demo/tree-result-table.tsx apps/web/src/components/demo/tree-result-table.test.tsx apps/web/src/components/demo/provenance-panel.tsx apps/web/src/components/demo/provenance-panel.test.tsx
git commit -m "feat(web): clarify tree exclusions and provenance"
```

---

### Task 7: Apply the editorial split layout to Login and Signup

**Files:**
- Create: `apps/web/src/components/auth/auth-panel.tsx`
- Create: `apps/web/src/components/auth/auth-panel.test.tsx`
- Modify: `apps/web/src/app/(auth)/layout.tsx:4`
- Modify: `apps/web/src/app/(auth)/login/page.tsx:11`
- Modify: `apps/web/src/app/(auth)/login/login-form.tsx:34`
- Modify: `apps/web/src/app/(auth)/signup/page.tsx:55`

**Interfaces:**
- `AuthPanelProps = { eyebrow: string; title: string; description: string; children: ReactNode; footer: ReactNode }`
- Consumes: `VISUAL_ASSETS.auth`, existing `signIn`, `signUp`, `useSearchParams`, redirects and form validation

- [ ] **Step 1: Write the failing presentational AuthPanel test**

Assert the component renders a heading association, children form region, footer and prototype/non-certification note without embedding any authentication behavior.

```tsx
const markup = renderToStaticMarkup(
  <AuthPanel
    eyebrow="TREEQ / SECURE WORKSPACE"
    title="เข้าสู่ระบบเพื่อเก็บหลักฐาน"
    description="ใช้บัญชีเดียวสำหรับงานวิเคราะห์และ provenance"
    footer={<a href="/signup">สมัครสมาชิก</a>}
  >
    <form aria-label="เข้าสู่ระบบ"><label htmlFor="email">อีเมล</label><input id="email" /></form>
  </AuthPanel>,
);
expect(markup).toContain('TREEQ / SECURE WORKSPACE');
expect(markup).toContain('aria-label="เข้าสู่ระบบ"');
expect(markup).toContain('href="/signup"');
expect(markup).toContain('อยู่นอกขอบเขต');
```

- [ ] **Step 2: Run the test and verify the component is missing**

Run: `npm test -- src/components/auth/auth-panel.test.tsx --run`

Expected: FAIL because `auth-panel.tsx` does not exist.

- [ ] **Step 3: Implement the split Auth layout from Figma node `37:2`**

Use `next/image` with the local auth image on the left at `lg` and above. Keep the form side on `Paper`, one form surface, no nested card stack. Below `lg`, hide the photograph and keep BrandMark plus form.

- [ ] **Step 4: Preserve Login and Signup behavior**

Do not change calls to `signIn` or `signUp`, redirect query handling, `router.refresh`, success state or role values. Replace raw inputs with the same semantic `label`, `id`, `required`, `autoComplete`, `minLength` and `role="alert"` attributes styled through shared tokens.

- [ ] **Step 5: Add visible focus and loading semantics**

Apply the shared focus ring to input, select and button. Add `aria-busy={loading}` to each form and preserve disabled submission while loading.

- [ ] **Step 6: Run Auth and type gates**

Run:

```powershell
npm test -- src/components/auth/auth-panel.test.tsx --run
npm run type-check
npm run lint
```

Expected: all pass.

- [ ] **Step 7: Commit Auth**

```powershell
git add apps/web/src/components/auth "apps/web/src/app/(auth)"
git commit -m "feat(web): redesign authentication experience"
```

---

### Task 8: Build the Observatory Dashboard without inventing project data

**Files:**
- Create: `apps/web/src/lib/frozen-demo-static.ts`
- Create: `apps/web/src/components/dashboard/dashboard-overview.tsx`
- Create: `apps/web/src/components/dashboard/dashboard-overview.test.tsx`
- Modify: `apps/web/src/app/(dashboard)/layout.tsx:4`
- Modify: `apps/web/src/app/(dashboard)/dashboard/page.tsx:5`

**Interfaces:**
- `FROZEN_DEMO_RESULT: ResultForView`
- `DashboardOverviewProps = { displayName: string; role: string; demoView: ResultViewModel }`
- Consumes: Supabase user lookup, `toResultViewModel(FROZEN_DEMO_RESULT)`, `VISUAL_ASSETS.dashboard`

- [ ] **Step 1: Create a static typed adapter for the committed artifact**

```ts
// apps/web/src/lib/frozen-demo-static.ts
import result from '../../public/demo/result.json';
import type { ResultForView } from './result-view-model';

export const FROZEN_DEMO_RESULT = result satisfies ResultForView;
```

- [ ] **Step 2: Write the failing DashboardOverview test**

Render `DashboardOverview` with `toResultViewModel(FROZEN_DEMO_RESULT)` and assert `3`, `5 detected / 2 excluded`, `4.729`, `tlsep`, `PointNet++ experimental`, links to `/demo` and `/dashboard/viewer`, and absence of `93.135`.

```tsx
const markup = renderToStaticMarkup(
  <DashboardOverview
    displayName="Judge"
    role="community"
    demoView={toResultViewModel(FROZEN_DEMO_RESULT)}
  />,
);
expect(markup).toContain('3');
expect(markup).toContain('5 detected / 2 excluded');
expect(markup).toContain('4.729');
expect(markup).toContain('tlsep');
expect(markup).toContain('PointNet++ experimental');
expect(markup).toContain('href="/demo"');
expect(markup).toContain('href="/dashboard/viewer"');
expect(markup).not.toContain('93.135');
```

- [ ] **Step 3: Run the test and verify the presentational component is missing**

Run: `npm test -- src/components/dashboard/dashboard-overview.test.tsx --run`

Expected: FAIL because `dashboard-overview.tsx` does not exist.

- [ ] **Step 4: Implement the dashboard from Figma node `39:2`**

Use a restrained photographic banner, one primary Judge Demo action, a three-metric strip explicitly labeled `Frozen Judge Sample`, a recent-analysis list and reliability panel. Do not present the Wan segmentation evaluation as a completed carbon run; label it `Experimental · segmentation only`.

- [ ] **Step 5: Keep authentication in the route wrapper**

Preserve `createClient()`, `supabase.auth.getUser()` and `redirect('/login')` in the server page. Compute `const demoView = toResultViewModel(FROZEN_DEMO_RESULT)` and pass only display data into `DashboardOverview`.

- [ ] **Step 6: Replace duplicate Dashboard navigation with `AppHeader`**

Keep the layout server-rendered. Mark Dashboard and 3D Viewer as navigation links; do not add marketplace, certificate or mobile routes.

- [ ] **Step 7: Run Dashboard and type gates**

Run:

```powershell
npm test -- src/components/dashboard/dashboard-overview.test.tsx src/lib/result-view-model.test.ts --run
npm run type-check
```

Expected: all pass.

- [ ] **Step 8: Commit Dashboard**

```powershell
git add apps/web/src/lib/frozen-demo-static.ts apps/web/src/components/dashboard "apps/web/src/app/(dashboard)"
git commit -m "feat(web): build observatory dashboard"
```

---

### Task 9: Add responsive, motion and accessibility guarantees

**Files:**
- Modify: `apps/web/src/app/globals.css`
- Modify: all page and component files changed in Tasks 2–8
- Create: `apps/web/src/components/editorial/accessibility-contract.test.tsx`

**Interfaces:**
- Consumes: shared components from Tasks 2–8
- Produces: consistent focus, motion and overflow behavior across every route

- [ ] **Step 1: Write accessibility contract tests**

Render AppHeader, ModeBadge, UploadDropzone, ResultRail and AuthPanel. Assert landmark elements exist, buttons retain `type`, form fields retain labels, status copy is textual rather than color-only, and images have meaningful or empty alt text according to purpose.

```tsx
const markup = renderToStaticMarkup(
  <>
    <AppHeader tone="paper" />
    <StatusState label="API" value="พร้อมใช้งาน" note="health check passed" tone="ready" />
    <AuthPanel eyebrow="TREEQ" title="เข้าสู่ระบบ" description="Secure workspace" footer={<span>Prototype</span>}>
      <form aria-label="เข้าสู่ระบบ"><button type="submit">เข้าสู่ระบบ</button></form>
    </AuthPanel>
  </>,
);
expect(markup).toContain('<nav');
expect(markup).toContain('พร้อมใช้งาน');
expect(markup).toContain('health check passed');
expect(markup).toContain('type="submit"');
expect(markup).toContain('aria-label="เข้าสู่ระบบ"');
```

- [ ] **Step 2: Run the focused test and capture failures**

Run: `npm test -- src/components/editorial/accessibility-contract.test.tsx --run`

Expected: FAIL on any missing landmark, label or textual status.

- [ ] **Step 3: Apply viewport-specific layout rules**

At `1366×768`, keep Landing CTA/evidence, Demo mode/upload/health, and Results viewer/summary visible without clipping. Below `1024px`, stack Viewer then ResultRail. Below `640px`, use smaller outer padding and internal table scrolling.

- [ ] **Step 4: Apply motion policy**

Use `180–220ms` for hover/focus, `240–320ms` for section entry and viewer panel transitions. Under `@media (prefers-reduced-motion: reduce)`, set animation duration to `0.01ms`, one iteration, and disable smooth scrolling and transform-based reveals.

- [ ] **Step 5: Run unit, type and lint gates**

Run:

```powershell
npm test -- --run
npm run type-check
npm run lint
```

Expected: all pass.

- [ ] **Step 6: Commit responsive and accessibility work**

```powershell
git add apps/web/src
git commit -m "fix(web): harden responsive and accessible presentation"
```

---

### Task 10: Add browser journey and visual regression gates

**Files:**
- Create: `apps/web/playwright.config.ts`
- Create: `apps/web/e2e/judge-journey.spec.ts`
- Create after review: `apps/web/e2e/judge-journey.spec.ts-snapshots/*`

**Interfaces:**
- Consumes: public routes `/`, `/demo`, `/login`, `/signup`, `/dashboard/viewer`
- Produces: deterministic desktop screenshot baselines at `1440×900` and `1366×768`

- [ ] **Step 1: Add Playwright configuration**

```ts
// apps/web/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: 'http://127.0.0.1:3000',
    trace: 'retain-on-failure',
    ...devices['Desktop Chrome'],
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://127.0.0.1:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

- [ ] **Step 2: Write the judge journey test**

For both viewports, test:

```ts
for (const viewport of [{ width: 1440, height: 900 }, { width: 1366, height: 768 }]) {
  test(`judge path ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto('/');
    await expect(page.getByRole('link', { name: /Demo Dataset|Judge Demo/ })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.getByRole('link', { name: /Demo Dataset|Judge Demo/ }).first().click();
    await expect(page.getByText(/FROZEN EVIDENCE/)).toBeVisible();
    await expect(page.getByText('ต้นไม้ที่คำนวณสำเร็จ')).toBeVisible();
    await expect(page.getByText(/ไม่ใช่คาร์บอนเครดิต/)).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}
```

Add route checks for Login, Signup and Viewer; in Viewer assert the synthetic label is visible before upload.

- [ ] **Step 3: Run functional browser tests first**

Run: `npx playwright test --project=chromium`

Expected: all functional checks pass.

- [ ] **Step 4: Capture and approve screenshot baselines**

Add `expect(page).toHaveScreenshot(...)` only after comparing each route with the matching Figma frame. Run:

```powershell
npx playwright test --project=chromium --update-snapshots
npx playwright test --project=chromium
```

Expected: the second run passes without updating files.

- [ ] **Step 5: Manually inspect keyboard and reduced-motion behavior**

Tab through every actionable element in order; confirm focus is always visible. Emulate `prefers-reduced-motion: reduce`; confirm no continuous or transform-based reveal remains. Test a `600px` viewport and confirm the document width equals the viewport width.

- [ ] **Step 6: Commit browser gates**

```powershell
git add apps/web/playwright.config.ts apps/web/e2e
git commit -m "test(web): gate judge journey visuals"
```

---

### Task 11: Run the truth, production-build and design-sync freeze gate

**Files:**
- Modify: `docs/superpowers/specs/2026-07-29-treeq-web-visual-redesign-design.md`
- Modify: `docs/superpowers/specs/2026-07-29-treeq-figma-state.json`
- Create: `docs/design/treeq-forest-observatory-implementation.md`

**Interfaces:**
- Consumes: all implementation tasks, Figma component IDs and source component paths
- Produces: final verification record and Code Connect mappings

- [ ] **Step 1: Run the complete Web gate from a clean process**

```powershell
cd apps/web
npm test -- --run
npm run type-check
npm run lint
npm run build
npx playwright test --project=chromium
```

Expected: every command passes.

- [ ] **Step 2: Scan for forbidden or stale claims**

```powershell
rg -n "93\.135|25,400\.58|18 calculated|20 detected|จำนวนต้นไม้|PointNet\+\+.*default|certified carbon credit|รองรับ \.las|รองรับ \.laz" src
```

Expected: no stale frozen totals, ambiguous measured-count label, promotion claim or unsupported upload format. A non-certification disclaimer may contain the words `carbon credit` only when clearly negated.

- [ ] **Step 3: Check the committed asset boundary**

```powershell
git ls-files apps/web/public/visual apps/web/src/assets/fonts
rg -n "wallhaven|dribbble" apps/web/src apps/web/public
```

Expected: only rights-documented local images and OFL fonts are committed; no Dribbble or Wallhaven URL is loaded by production code.

- [ ] **Step 4: Visually compare implementation against Figma**

Compare these nodes at both desktop sizes:

| Screen | 1440×900 | 1366×768 |
|---|---|---|
| Landing | `32:2` | `42:21` |
| Judge Demo | `33:2` | `43:28` |
| Results | `35:2` | `45:145` |
| Results table | `36:43` | responsive implementation |
| Provenance | `36:123` | responsive implementation |
| Auth | `37:2` | responsive implementation |
| Dashboard | `39:2` | responsive implementation |

Record every accepted deviation and its reason in `docs/design/treeq-forest-observatory-implementation.md`.

- [ ] **Step 5: Add Code Connect only after source components exist**

Map the approved Figma components to these exact source files:

| Figma node | Component | Source |
|---|---|---|
| `17:2` | `BrandMark` | `apps/web/src/components/brand/brand-mark.tsx` |
| `21:2` | `Button` | `apps/web/src/components/ui/button.tsx` |
| `23:2` | `ModeBadge` | `apps/web/src/components/demo/mode-badge.tsx` |
| `23:3` | `EvidenceMetric` | `apps/web/src/components/evidence/evidence-metric.tsx` |
| `25:2` | `UploadDropzone` | `apps/web/src/components/demo/upload-dropzone.tsx` |
| `25:3` | `StatusState` | `apps/web/src/components/evidence/status-state.tsx` |
| `28:2` | `AppHeader` | `apps/web/src/components/layout/app-header.tsx` |
| `28:15` | `CompactWorkspaceHeader` | `apps/web/src/components/layout/compact-workspace-header.tsx` |
| `28:20` | `PointCloudLegend` | `apps/web/src/components/viewer/point-cloud-legend.tsx` |
| `29:9` | `ResultRail` | `apps/web/src/components/demo/result-rail.tsx` |
| `29:34` | `TreeResultTable` | `apps/web/src/components/demo/tree-result-table.tsx` |
| `30:9` | `ProvenancePanel` | `apps/web/src/components/demo/provenance-panel.tsx` |
| `30:38` | `AuthPanel` | `apps/web/src/components/auth/auth-panel.tsx` |

- [ ] **Step 6: Freeze the implementation record**

Update the design spec status to `Implemented and verified`, add the implementation commit SHA, build result, test counts, Playwright result and screenshot review date to the state ledger.

- [ ] **Step 7: Commit the final design sync**

```powershell
git add docs/superpowers/specs/2026-07-29-treeq-web-visual-redesign-design.md docs/superpowers/specs/2026-07-29-treeq-figma-state.json docs/design/treeq-forest-observatory-implementation.md
git commit -m "docs: freeze forest observatory implementation evidence"
```

---

## Self-Review Record

- Spec coverage: Landing, Judge Demo, Results/3D, tree table, provenance, Login, Signup, Dashboard, shared tokens, typography, motion, responsive behavior, accessibility, asset rights and Code Connect each map to a task above.
- Truth boundary: validation metrics and Judge frozen result are intentionally separate; the plan contains no stale `93.135 tCO₂e` demo claim.
- Behavior boundary: demo reducer/controller, API calls, auth calls, Three.js color conversion and result adapter remain source-of-truth logic.
- Scope boundary: no mobile, ML, marketplace, certification, species training or PointNet++ promotion work is included.
- Dependency boundary: no new runtime UI framework is added; Playwright and Vitest already exist in `package.json`.
