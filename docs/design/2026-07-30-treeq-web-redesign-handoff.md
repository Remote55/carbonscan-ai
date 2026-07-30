# TreeQ Web Visual Redesign — Implementation Handoff

**วันที่จัดทำ:** 2026-07-30  
**แนวทาง:** Forest Editorial Observatory + Cinematic Field Photography  
**ขอบเขต:** Web UX/UI เท่านั้น  
**สถานะ:** Tasks 1–5 เสร็จและ review ผ่าน; Task 6 implementation เสร็จแต่ final contrast re-review ถูกขัดจังหวะ; Tasks 7–11 ยังไม่เริ่ม

> จุดสำคัญที่สุด: งาน UX/UI อยู่ใน worktree แยก ไม่ได้อยู่ที่ `D:\Project_Carbon` โดยตรง และยังไม่ได้ push/merge

---

## 1. สถานะ Git ปัจจุบัน

### Worktree ที่ต้องเข้าไปทำต่อ

```powershell
Set-Location 'D:\Project_Carbon\.worktrees\web-visual-redesign-impl'
```

- Branch: `codex/web-visual-redesign-impl`
- HEAD: `05e4d71d6d9247d83c30cfbe8e6aee0154f21d59`
- Base: `f0747631100dab21e9b05e921c00621c2e743267`
- สถานะก่อนสร้าง handoff file นี้: clean
- เปลี่ยน implementation ทั้งหมดจาก base: 50 files
- Branch ยังไม่มี upstream แสดงอยู่
- ยังไม่ได้ merge กลับ `codex/web-visual-redesign`
- ยังไม่ได้ push ในรอบ UX/UI นี้

Main checkout:

- Path: `D:\Project_Carbon`
- Branch: `codex/web-visual-redesign`
- HEAD: `f074763`
- ยังไม่มี implementation Tasks 1–6

ห้ามทำ Tasks ถัดไปใน `D:\Project_Carbon` เพราะงานจะขาดจาก implementation ที่ทำมาแล้ว

เอกสารหลัก:

- `docs/superpowers/plans/2026-07-29-treeq-web-visual-redesign.md`
- `docs/superpowers/specs/2026-07-29-treeq-web-visual-redesign-design.md`
- `docs/superpowers/specs/2026-07-29-treeq-figma-state.json`
- `.superpowers/sdd/2026-07-29-treeq-web-visual-redesign/progress.md`
- `.superpowers/sdd/2026-07-29-treeq-web-visual-redesign/task-6-report.md`

ข้อควรระวัง: `.superpowers/` ถูก Git ignore ดังนั้น briefs, reports, review diffs และ ledger ภายในนั้นไม่ได้อยู่ใน commit อย่าลบ worktree ก่อนสำรองไฟล์เหล่านี้

---

## 2. แนวทาง UX/UI ที่เลือก

ชื่อแนวทาง:

**Forest Editorial Observatory + Cinematic Field Photography**

แนวคิดหลัก:

> ธรรมชาติที่วัดและตรวจสอบได้

TreeQ ต้องดูเหมือนระบบสังเกตการณ์ป่าและนิทรรศการธรรมชาติร่วมสมัย ไม่ใช่ generic SaaS dashboard, crypto/carbon marketplace, gaming UI หรือ AI demo ที่เคลมเกินหลักฐาน

ภาษาภาพ:

- ภาพธรรมชาติขนาดใหญ่
- Serif headline ที่สงบและมั่นใจ
- Whitespace ที่มีจังหวะ
- Information panel คล้ายป้ายในนิทรรศการ
- Technical metadata ใช้ monospace เท่าที่จำเป็น
- ตัวเลขใช้ tabular numerals
- Viewer ใช้ Deep Forest
- ผลลัพธ์และ provenance ใช้ Paper/Gallery Ivory
- Amber ใช้กับ limitation, frozen evidence และ excluded tree

### แรงบันดาลใจ

ใช้เป็น reference เฉพาะ composition, hierarchy และความประณีต:

- EcoTech Exhibition Landing Page: `https://dribbble.com/shots/26497016-EcoTech-Exhibition-Landing-Page-Nature-UI-UX-Design`
- Hotel Booking Website: `https://dribbble.com/shots/27262277-Hotel-Booking-Website`

ไม่ได้คัดลอกรูปภาพ, component เฉพาะ, layout แบบหนึ่งต่อหนึ่ง, source code หรือ asset จาก Dribbble

รูป Wallhaven ที่ผู้ใช้ส่งมาใช้เพื่อคุยเรื่อง mood เท่านั้น ไม่ถูกใส่ใน repo และไม่ได้ป้อนเป็น reference ให้ image generator

---

## 3. Figma

Figma file:

`https://www.figma.com/design/54IMkjTG5teh8P1ZHairlo`

File key:

```text
54IMkjTG5teh8P1ZHairlo
```

สถานะ Figma:

- Phase 4: PASS
- Design frames: 13
- Verification frames: 3
- Missing fonts: 0
- Zero-size nodes: 0
- Missing truth claims: 0
- Forbidden stale claims: 0
- Variable count: 86
- Components: 32
- Component sets: 5
- Button variants: 12
- ModeBadge variants: 3
- UploadDropzone variants: 4

### Pages

| Page | Node |
|---|---|
| 00 Foundations | `0:1` |
| 01 Components | `12:2` |
| 02 Landing | `12:3` |
| 03 Judge Demo | `12:4` |
| 04 Results + Viewer | `12:5` |
| 05 Auth | `12:6` |
| 06 Dashboard | `12:7` |

### Screen frames

| Screen | Node |
|---|---|
| Landing 1440×900 | `32:2` |
| Landing 1366×768 | `42:21` |
| Judge Demo 1440×900 | `33:2` |
| Judge Demo 1366×768 | `43:28` |
| Results 3D 1440×900 | `35:2` |
| Results 1366×768 | `45:145` |
| Results Table | `36:43` |
| Provenance | `36:123` |
| Auth | `37:2` |
| Dashboard | `39:2` |

### Reusable components

| Component | Node |
|---|---|
| BrandMark | `17:2` |
| Button | `21:2` |
| ModeBadge | `23:2` |
| EvidenceMetric | `23:3` |
| UploadDropzone | `25:2` |
| StatusState | `25:3` |
| AppHeader | `28:2` |
| CompactWorkspaceHeader | `28:15` |
| ViewerLegend | `28:20` |
| ResultRail | `29:9` |
| TreeResultTable | `29:34` |
| ProvenancePanel | `30:9` |
| AuthPanel | `30:38` |

Code Connect ยังไม่ได้ทำ ต้องรอ Task 11 หลัง source components ครบ

---

## 4. ที่มาของรูปและฟอนต์

### Production photography

มี 4 รูป:

- `landing-mist.webp`
- `judge-road.webp`
- `auth-lake.webp`
- `dashboard-road.webp`

ทั้งหมด:

- สร้างใหม่ด้วย OpenAI image generation วันที่ 2026-07-29
- ไม่ใช้ input/reference image
- ไม่ใช้ Wallhaven เป็น generator input
- ไม่ดาวน์โหลดภาพจาก Dribbble
- Export เป็น WebP 1920×1080 quality 82
- มี SHA-256 และ prompt บันทึกไว้
- Rights ระบุเป็น `generated`

รายละเอียดเต็มอยู่ที่ `apps/web/public/visual/forest-observatory/ASSETS.md`

| Asset | Size |
|---|---:|
| landing-mist.webp | 90,468 bytes |
| judge-road.webp | 236,012 bytes |
| auth-lake.webp | 236,554 bytes |
| dashboard-road.webp | 345,368 bytes |

### Self-hosted fonts

- Noto Serif Thai variable
- IBM Plex Sans Thai Regular
- IBM Plex Sans Thai Medium
- IBM Plex Sans Thai SemiBold
- JetBrains Mono variable

ดาวน์โหลดจาก official upstream และเก็บ OFL license ครบ เพื่อให้ production/offline build ไม่พึ่ง font CDN

---

## 5. Visual system

### Colors

| Token | Hex | Usage |
|---|---:|---|
| Forest Ink | `#152019` | ข้อความหลัก |
| Deep Forest | `#0E2A1D` | Viewer/พื้นที่เข้ม |
| Canopy | `#214E35` | Navigation/ข้อความเล็ก contrast สูง |
| Moss | `#789B3B` | CTA/accent |
| Lichen | `#C7D6A1` | Selected/highlight |
| Gallery Ivory | `#F4F1E8` | พื้นหน้าหลัก |
| Paper | `#FCFBF7` | Card/form |
| Mist | `#D9DED5` | Disabled/section |
| Evidence Amber | `#B28A40` | Frozen/limitation/excluded |
| Clay | `#A65F46` | Error |
| Hairline | `#D6D7CF` | Border |

### Typography

- Heading: Noto Serif Thai
- UI/body: IBM Plex Sans Thai
- Commit/hash/metadata: JetBrains Mono
- Numeric reporting: tabular numerals

---

## 6. Tasks ที่ทำแล้ว

### Task 1 — Visual assets และ offline fonts

สถานะ: เสร็จและ review ผ่าน

Commits:

- `52553d5 feat(web): add licensed forest visual foundation`
- `38f76dd test(web): strengthen visual asset contract`

งาน:

- เพิ่ม production images 4 รูป
- เพิ่ม `VISUAL_ASSETS`
- บันทึก rights/source/hash
- เพิ่ม self-hosted fonts และ OFL files
- ลบ external font dependency จาก judge path
- เพิ่ม exact asset-contract tests
- Offline production build ผ่าน

### Task 2 — Design system และ shared components

สถานะ: เสร็จและ review ผ่าน

Commits:

- `0b93190 feat(web): add forest editorial design system`
- `8f64b2a test(web): cover complete editorial header navigation`
- `bd1f99b test(web): isolate editorial header navigation contract`
- `6fa589b fix(web): make semantic color opacity build-safe`

งาน:

- Tailwind tokens ตาม Figma
- BrandMark
- AppHeader
- CompactWorkspaceHeader
- EditorialSection
- EvidenceMetric
- StatusState
- Editorial Button variants
- Local font wiring
- Focus-ring และ scrollbar styles
- แก้ invalid Tailwind opacity utilities ด้วย `color-mix()`

Deferred Minor:

- Design-system test ยังไม่ตรวจ editorial semantic styling และ legacy Button variant แบบอิสระครบทุกกรณี

### Task 3 — Landing

สถานะ: เสร็จ, review ผ่าน, build ผ่าน

Commits:

- `7123817 feat(web): rebuild evidence-led landing`
- `74a3190 test(web): harden landing evidence contract`

Figma: `32:2`, รองรับ `42:21`

งาน:

- Split editorial hero
- ใช้ `landing-mist.webp`
- CTA `ทดลอง Demo Dataset` → `/demo`
- CTA `อัปโหลด Point Cloud` → `/demo`
- Server component + Tailwind เท่านั้น
- ไม่มี styled-jsx/Canvas 3D
- เนื้อหา Problem → Measurement → 3D Evidence → Validation
- ใช้ evidence จริงจาก generated evidence source
- CTA tests ผูก label กับ href จริง

ค่าที่ใช้:

- Wood IoU `0.418`
- Leaf IoU `0.808`
- DBH MAE `1.1673846154 cm`
- `tlsep = Default`
- `PointNet++ = Experimental`
- species stage = `Stub`

### Task 4 — Judge Demo Journey

สถานะ: เสร็จและ review ผ่าน

Commits:

- `2809893 fix(web): preserve frozen evidence diagnostics`
- `cb15791 feat(web): refine reliable judge demo journey`
- `481f546 fix(web): enforce frozen evidence reconciliation`

Figma: `33:2`, `43:28`

งาน UX:

- Compact Judge Demo header
- Journey: INPUT → VALIDATE → PIPELINE → RESULT → PROVENANCE
- Frozen Sample เป็นเส้นทางหลัก
- Live Upload เป็นเส้นทางรอง
- แสดง `FROZEN EVIDENCE — NOT A LIVE RUN`
- UploadDropzone contract `.ply · 100 MB · 2,000,000 จุด`
- ไม่อ้าง `.las/.laz`
- Selected filename คงอยู่ระหว่าง processing
- มี `aria-live`
- Disable input ระหว่าง upload/processing
- Evidence verification fail แล้วไม่แสดง carbon/count totals

User-approved parser scope expansion:

- Modern diagnostics ต้อง all-or-none
- `detected = measured + excluded`
- `measured = total_trees`
- `measured = trees.length`
- `excluded = excluded_segments.length`
- ยอมรับ `wood_leaf + WOOD_EMPTY`
- ยอมรับ `qsm + QSM_INVALID`
- Excluded IDs ห้ามซ้ำ
- Excluded IDs ห้ามชน measured IDs
- Legacy artifact ที่ไม่มี diagnostics ทั้งหมดต้องยังอ่านได้

Protected behavior:

- Demo controller/reducers
- Runtime handoff
- API behavior

Deferred Minor:

- Mode selector ยังใช้ `aria-current="page"` บน `span`; ควรแก้เป็น labelled tab/pressed-control semantics ใน Task 9

### Task 5 — Results Workspace / 3D Viewer

สถานะ: เสร็จครบ specification และ code-quality reviews

Commits:

- `2f0af54 feat(web): build evidence-focused results workspace`
- `bcc5667 fix(web): harden results workspace semantics`
- `d6a17f4 test(web): guard results workspace truth semantics`
- `d185571 test(web): stabilize live analysis truth guard`

Figma: `35:2`, `45:145`

งาน:

- Results Workspace แบบ 8/4 grid
- ViewerStage สี Deep Forest
- ResultRail สี Paper
- ใช้ Three.js Canvas จริง
- ไม่ใช้ fake Figma dot-cloud แทนผลจริง
- Legend wood/leaf/ground
- Rotate/zoom/pan guidance
- ไม่มี PLY จริงต้องแสดง synthetic view
- ResultRail แสดง CO₂e, carbon, calculated/detected/excluded
- Artifact เก่าไม่มี diagnostics ต้องแสดง unavailable และไม่แต่งตัวเลข
- Rail/table ใช้ `resultView` เดียวกัน
- Exact disclaimer: `ค่าประมาณชีวมวล ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง`
- แสดง QSM unavailable
- แสดง viewer/provenance identity warning
- Live badge ใช้ neutral `LIVE ANALYSIS`
- ไม่ hard-code local-live/endpoint/token/credentials

Quality fixes:

- Valid `<dl>/<dt>/<dd>` semantics
- Disclosure text contrast ผ่าน AA
- Wood legend boundary ชัด
- Tests ตรวจ visible `<dt>/<dd>` จริง
- Runtime badge guard เป็น behavioral/component test

Protected viewer behavior:

- `point-cloud-viewer.tsx`
- `ply-loader.ts`
- API parsing/errors
- sRGB → linear
- Z-up
- Orbit controls
- Callback region `loadFile` ถึง `runAnalysis`

Final Task 5 gates:

- Full tests: 104/104
- Type-check: PASS
- Lint: PASS
- Production build: PASS
- Generated pages: 10/10

### Task 6 — Tree Results และ Provenance

สถานะ: implementation เสร็จ; final contrast re-review ถูกขัดจังหวะ

Commits:

- `73c1dba feat(web): clarify tree exclusions and provenance`
- `532f487 fix(web): retain PointNet++ promotion boundary`
- `05e4d71 fix(web): improve provenance text contrast`

Figma: `36:43`, `36:123`

Tree table:

- รวม measured/excluded rows
- เรียง IDs `1,2,3,4,5`
- ต้น 1/4 เป็น `EXCLUDED` พร้อม pipeline reason
- Measured rows เป็น `READY`
- Tabular numerals
- Excluded rowsไม่รวม carbon total
- Caption + `scope="col"`/`scope="row"`
- Container มี own horizontal scrolling
- Table มี `min-w-[44rem]`

Provenance groups:

- Run identity
- Input/artifact hashes
- Pipeline/backend
- Git commit
- Species status
- Allometric source
- Limitations

Truth constraints:

- Run-specific values จาก `FrozenDemoManifest`
- ไม่ใช้ Figma fixture literals
- Full SHA แสดงครบและ `break-all`
- ไม่อ้าง allometric path ถ้า manifest ไม่ยืนยัน
- Dataset เป็น deterministic fixture ไม่ใช่ accuracy/carbon validation
- PointNet++: `Experimental · ยังไม่ถูกเลื่อนเป็นค่าตั้งต้น`
- Current run backend แสดงแยกจาก PointNet++
- Non-certification sentence ยังคงอยู่

Contrast fix:

- Moss/Paper เดิม `3.10:1` → Canopy/Paper `9.19:1`
- Moss/Gallery Ivory เดิม `2.84:1` → Canopy/Gallery Ivory `8.43:1`
- ครอบ provenance eyebrows, artifact labels, READY status

Final implementation gates:

- Full tests: 111/111
- Type-check: PASS
- Lint: PASS
- Production build: PASS
- Static pages: 10/10

Task 6 ที่ค้าง:

- Fresh re-review ของ `05e4d71` ถูก interrupt
- Review diff: `.superpowers/sdd/2026-07-29-treeq-web-visual-redesign/review-532f487..05e4d71.diff`
- ต้องตรวจ contrast >=4.5 บนพื้นจริง, tests อ่าน CSS variables จริง และไม่มี truth/layout regression
- ถ้าผ่าน ให้บันทึก Task 6 complete ใน `progress.md`

Deferred Minors:

- Provenance test ยังไม่มี sentinel manifest เพื่อป้องกัน hard-coded fixture
- Table test ยังไม่ตรวจ `tabular-nums` ทุก measurement cell

---

## 7. Truth boundaries ที่ต้องรักษา

### Validation metrics

Source: `apps/web/src/generated/core-demo-evidence.ts`

- Wood IoU: `0.418`
- Leaf IoU: `0.808`
- DBH MAE: `1.1673846154 cm`

### Frozen Judge result

Source: `apps/web/public/demo/result.json`

- Detected: 5
- Calculated: 3
- Excluded: 2
- Carbon: `1,289.74 kg`
- CO₂e: `4,729.06 kg`

Validation metrics กับ Frozen Judge result เป็นคนละ evidence scope ห้ามนำมารวมเป็นผลเดียวกัน

คำที่ต้องรักษา:

- `ต้นไม้ที่คำนวณสำเร็จ`
- `ต้นไม้ที่ตรวจพบ`
- `ไม่รวมผล`
- `PointNet++ = Experimental`
- `ยังไม่ถูกเลื่อนเป็นค่าตั้งต้น`
- species = `Stub`
- `FROZEN EVIDENCE — NOT A LIVE RUN`
- `ค่าประมาณชีวมวล ไม่ใช่คาร์บอนเครดิตที่ผ่านการรับรอง`

ห้าม:

- ใช้ `จำนวนต้นไม้` แบบกำกวม
- แสดง `93.135 tCO₂e`
- แสดง `25,400.58 kg`
- Promote PointNet++ เป็น default
- อ้าง certified carbon credit
- อ้าง upload `.las/.laz`
- ซ่อน Frozen/Live status
- แสดงผลเมื่อ frozen verification fail
- สร้าง segmented/QSM visual ทดแทนเมื่อไม่มี artifact จริง

---

## 8. งานค้าง Tasks 7–11

### ขั้นแรก — ปิด Task 6 review

```powershell
Set-Location 'D:\Project_Carbon\.worktrees\web-visual-redesign-impl'
git status --short
git log --oneline -5
```

Expected HEAD: `05e4d71`

ให้ fresh reviewer อ่าน Task 6 brief/report และ diff `532f487..05e4d71` ถ้าผ่านให้ append Task 6 completion ลง ledger แล้วเริ่ม Task 7

### Task 7 — Login/Signup

Figma: `37:2`

Files:

- Create `apps/web/src/components/auth/auth-panel.tsx`
- Create `auth-panel.test.tsx`
- Modify auth layout/login/login-form/signup

Requirements:

- Editorial split screen
- ใช้ `auth-lake.webp`
- Paper form surface เดียว ไม่ซ้อน card
- ต่ำกว่า `lg` ซ่อนภาพแต่คง BrandMark/form
- Prototype/non-certification note
- Labels, focus, error semantics
- `aria-busy` และ disabled loading state

ห้ามเปลี่ยน:

- `signIn`, `signUp`
- Redirect query
- `router.refresh`
- Success state/role values
- Validation, `required`, `autoComplete`, `minLength`, `role="alert"`

Commit: `feat(web): redesign authentication experience`

### Task 8 — Observatory Dashboard

Figma: `39:2`

Files:

- Create `frozen-demo-static.ts`
- Create `dashboard-overview.tsx` และ test
- Modify dashboard layout/page

Requirements:

- Typed import ของ committed result JSON
- ใช้ `dashboard-road.webp`
- Restrained banner
- Primary Judge Demo CTA
- Metrics ติดป้าย `Frozen Judge Sample`
- Recent-analysis list + reliability panel
- Links `/demo`, `/dashboard/viewer`
- Wan result ต้องเป็น `Experimental · segmentation only`
- ห้ามสร้าง project/recent-analysis data ปลอม
- คง Supabase auth lookup + redirect ใน server wrapper

Commit: `feat(web): build observatory dashboard`

### Task 9 — Responsive, accessibility, motion

Requirements:

- 1440×900 critical content visible
- 1366×768 critical contentไม่ถูกตัด
- ต่ำกว่า 1024 Results stack Viewer ก่อน Rail
- ต่ำกว่า 640 ลด padding/table internal scroll/no page overflow
- Landmarks/labels/button types/status text/alt/focus ครบ
- แก้ Task 4 mode control semantics
- พิจารณาเพิ่ม deferred sentinel/tabular/Button tests
- Hover/focus 180–220ms
- Section/viewer transitions 240–320ms
- `prefers-reduced-motion` ปิด smooth scroll และ transform reveal

Commit: `fix(web): harden responsive and accessible presentation`

### Task 10 — Playwright/browser visual gates

Create:

- `apps/web/playwright.config.ts`
- `apps/web/e2e/judge-journey.spec.ts`
- Approved screenshot baselines

Routes:

- `/`
- `/demo`
- `/login`
- `/signup`
- `/dashboard/viewer`

Viewports:

- 1440×900
- 1366×768
- Manual 600px overflow check

ทำ functional tests ก่อน screenshot; ตรวจ Frozen copy, calculated label, non-certification, synthetic viewer label และ document width

Commit: `test(web): gate judge journey visuals`

### Task 11 — Final freeze gate

Full gate:

```powershell
Set-Location 'D:\Project_Carbon\.worktrees\web-visual-redesign-impl\apps\web'
npm.cmd test -- --run
npm.cmd run type-check
npm.cmd run lint
npm.cmd run build
npx playwright test --project=chromium
```

Run commands sequentiallyบน Windows ห้ามเปิด npm/pnpm gates พร้อมกัน

Forbidden-claim scan:

```powershell
rg -n "93\.135|25,400\.58|18 calculated|20 detected|จำนวนต้นไม้|PointNet\+\+.*default|certified carbon credit|รองรับ \.las|รองรับ \.laz" src
```

Asset scan:

```powershell
git ls-files apps/web/public/visual apps/web/src/assets/fonts
rg -n "wallhaven|dribbble" apps/web/src apps/web/public
```

Visual compare กับ Figma ทุก node, บันทึก accepted deviations ที่ `docs/design/treeq-forest-observatory-implementation.md`, ทำ Code Connect หลัง source components ครบ และอัปเดต design spec/Figma state เป็น `Implemented and verified`

Commit: `docs: freeze forest observatory implementation evidence`

---

## 9. Workflow ที่ใช้ต่อ

Subagent-Driven Development ต่อ task:

1. Generate task brief
2. Fresh implementer
3. TDD RED
4. GREEN focused tests
5. Full tests/type/lint/build
6. Commit
7. Fresh specification reviewer
8. Fix Important/Critical โดย implementer เดิม
9. Fresh scoped re-reviewer
10. Fresh code-quality reviewer
11. Defer Minor ลง ledger
12. Update plan แล้วเริ่ม task ถัดไป

Task brief script:

```powershell
& 'C:\Program Files\Git\bin\bash.exe' -lc "'C:/Users/Acer/.codex/plugins/cache/superpowers-marketplace/superpowers/6.2.0/skills/subagent-driven-development/scripts/task-brief' 'docs/superpowers/plans/2026-07-29-treeq-web-visual-redesign.md' '7'"
```

Review package:

```powershell
& 'C:\Program Files\Git\bin\bash.exe' -lc "'C:/Users/Acer/.codex/plugins/cache/superpowers-marketplace/superpowers/6.2.0/skills/subagent-driven-development/scripts/review-package' 'docs/superpowers/plans/2026-07-29-treeq-web-visual-redesign.md' '<BASE_SHA>' '<HEAD_SHA>'"
```

ทุก screen task ต้องอ่าน Figma `get_design_context` ก่อนเขียนโค้ด

---

## 10. UX/UI commit history

```text
52553d5 feat(web): add licensed forest visual foundation
38f76dd test(web): strengthen visual asset contract
0b93190 feat(web): add forest editorial design system
8f64b2a test(web): cover complete editorial header navigation
bd1f99b test(web): isolate editorial header navigation contract
7123817 feat(web): rebuild evidence-led landing
74a3190 test(web): harden landing evidence contract
6fa589b fix(web): make semantic color opacity build-safe
2809893 fix(web): preserve frozen evidence diagnostics
cb15791 feat(web): refine reliable judge demo journey
481f546 fix(web): enforce frozen evidence reconciliation
2f0af54 feat(web): build evidence-focused results workspace
bcc5667 fix(web): harden results workspace semantics
d6a17f4 test(web): guard results workspace truth semantics
d185571 test(web): stabilize live analysis truth guard
73c1dba feat(web): clarify tree exclusions and provenance
532f487 fix(web): retain PointNet++ promotion boundary
05e4d71 fix(web): improve provenance text contrast
```

---

## 11. Separate Reliability branch

Worktree:

```text
D:\Project_Carbon\.worktrees\judge-demo-sprint-impl
```

Branch: `codex/judge-demo-sprint-impl`  
HEAD: `107d10e fix(demo): harden launcher integrity and lifecycle`

ยังมี Important finding:

- Frozen standalone verifier ยังตรวจ server-side dependencies ที่ `page.js.nft.json` อ้างถึงไม่ครบ เช่น `server/chunks/*.js` และ `server/webpack-runtime.js`
- Local-live/Auto-public ยังไม่ถูกพิสูจน์จริงเพราะ repository venv เดิมชี้ Python 3.11 ที่ถูกลบ

อย่า merge reliability branch กับ UX branch แบบไม่ review เพราะทั้งสองแตะ Judge Demo/frozen evidence/demo shell/parser

---

## 12. Prompt สำหรับ agent ถัดไป

```text
ทำต่อใน D:\Project_Carbon\.worktrees\web-visual-redesign-impl เท่านั้น
Branch codex/web-visual-redesign-impl, expected implementation HEAD 05e4d71

อ่าน AGENTS.md, docs/PROJECT_SPEC.md, implementation plan, design spec,
Figma state, SDD progress ledger และ task-6-report.md ก่อนทำงาน

งานแรก: fresh re-review Task 6 Fix Round 2 จาก review-532f487..05e4d71.diff
ตรวจ small-text contrast ของ provenance labels, artifact labels และ READY
ต้อง >=4.5:1 บน Paper/Gallery Ivory และ tests ต้องอ่าน CSS variables จริง
ห้ามแก้โค้ดระหว่าง review

ถ้าผ่าน ให้บันทึก Task 6 complete และเริ่ม Task 7 Auth ด้วย fresh implementer
เรียก Figma get_design_context node 37:2 ก่อน coding
ใช้ TDD และ review specification/code quality สองชั้น
ทำต่อ Tasks 7–11 ตาม plan

Web only; ห้ามแตะ ML/API/mobile
ห้ามเปลี่ยน auth behavior, API, viewer, reducers หรือ evidence truth
รัน npm/pnpm sequential บน Windows
ยังไม่ push/merge จน final freeze gate ผ่าน
```

