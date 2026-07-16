# Session Handoff — CarbonScan AI / NSC 2026

> [!CAUTION]
> **Archived session handoff — superseded 2026-07-16.** เนื้อหาด้านล่างเป็นบันทึกตามเวลาและอาจมีชื่อเดิม
> ตัวเลขปัด หรือ target architecture; ไม่ใช่ implementation truth ปัจจุบัน ให้ยึด
> `docs/evidence/core_demo_manifest.json`, `docs/PROJECT_SPEC.md` และ `docs/CAPABILITY_MATRIX.md`.
> Current gate: `tlsep` default; PointNet++ Experimental/not promoted; Species = Stub;
> async progress = polling; production RunPod, WebSocket, GIS และ Marketplace = Planned.

> **อัปเดต:** 2026-05-25 (4 วันก่อน Deadline Proposal)
> **เอกสารนี้ใช้เพื่อ:** ส่งต่อ context ให้ Chat Session ใหม่ (Claude / AI assistant อื่น) ให้รับงานต่อได้ทันทีโดยไม่ต้องอ่าน transcript เก่าทั้งหมด
> **ผู้อ่านเป้าหมาย:** AI assistant ที่จะมาช่วยทำงานต่อ + User ที่กลับมาดูเอง

---

## 0. TL;DR (อ่าน 30 วินาทีนี้พอ ถ้าเร่ง)

- **โปรเจกต์:** CarbonScan AI — แพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้ด้วย **LiDAR Point Cloud + AI Wood-Leaf Segmentation + B2B Carbon Credit Marketplace**
- **การประกวด:** NSC 2026 หมวด 14 (วิทยาศาสตร์/เทคโนโลยี) ระดับอุดมศึกษา
- **Deadline ใกล้สุด:** **29 พ.ค. 2569 (4 วัน) — ส่ง Proposal ใน SIMs ก่อน 17:00 น.**
- **ทีม:** 3 คน — User (Lead, ML/Mobile/Backend), Person A (Web), Person B (UI/UX+Design)
- **สถานะ Git:** อยู่ branch `feat/proposal-nsc-template` (commit `005111f`), PR #13 **เปิดรอ merge**
- **งานล่าสุด:** เพิ่ง rewrite `proposal/outline.md` ตาม NSC 2026 Booklet Section 7 template (974 บรรทัด)
- **Validation จริง:** Belgium dataset (Demol 2021, n=65) — **DBH MAE 1.17 cm / Height MAE 0.54 m** ✅
- **Pivot สำคัญ:** "Mobile-first" → **"LiDAR-primary, mobile as smallholder onboarding"** (ตาม advisor feedback)

---

## 1. โปรเจกต์ภาพรวม

### 1.1 Problem Statement
ตลาดคาร์บอนเครดิตไทย (T-VER) มีปัญหา 3 อย่าง:
1. **Verification ช้า** — Audit แบบ manual ต้องวัด DBH ทีละต้น (~3-6 เดือนต่อโครงการ)
2. **ต้นทุนสูง** — Auditor field cost ~50,000-200,000 บาท/โครงการ
3. **ตลาด matchmaking ไม่มี** — ผู้ขายเจอผู้ซื้อยาก (CBAM ทำให้ Demand โตเร็ว)

### 1.2 Solution (Value Proposition v2 — หลัง pivot)

| Layer | Component | Tech |
|---|---|---|
| **Input** | (1) LiDAR `.las/.laz/.ply` upload | TLS/ALS scanners, public datasets |
| | (2) Mobile photogrammetry (Smallholder farmers) | Flutter + COLMAP/OpenMVS → point cloud |
| **Processing** | 8-step ML pipeline (ดู §6) | Python 3.11, NumPy, SciPy, scikit-image, Open3D, PyTorch |
| **Output** | (a) 3D viewer + parity plots → Auditor | Next.js + Three.js (R3F) + Leaflet |
| | (b) Carbon report PDF + T-VER metadata | FastAPI + PostGIS |
| | (c) B2B Marketplace matching buyers (CBAM-compliant) | PostgreSQL queries |

### 1.3 Target Users (3 กลุ่ม)
1. **Carbon Auditor** (DNV, TÜV, SGS) — อัปโหลด LiDAR scan → ระบบสร้าง verification report
2. **Smallholder Farmer** — ใช้ Mobile App ถ่ายต้นไม้ → estimate carbon (low-rigor, แต่ access ง่าย)
3. **Industrial Buyer (CBAM)** — Browse marketplace → ซื้อ verified credit จาก Auditor pipeline

---

## 2. Timeline & Deadlines

### 2.1 NSC 2026 Critical Dates

| วันที่ | งาน | สถานะ |
|---|---|---|
| **26 พ.ค.** | ส่ง Proposal v2 ให้อาจารย์ review รอบ 2 | ⏳ User ต้องทำ |
| **26-28 พ.ค.** | เดินขอลายเซ็นที่ปรึกษา + คณบดี/ผอ. | ⏳ User ต้องทำ (ใช้เวลา 2-3 วัน) |
| **29 พ.ค. 17:00** | **Upload Proposal ใน SIMs (Deadline เดี้ยขาด)** | ⏳ User ต้องทำ |
| 17 ก.ค. | ส่ง Final Report | ห่างไกล |

### 2.2 Sprint Roadmap (หลัง Proposal)

- **Sprint 1 (30 พ.ค. – 13 มิ.ย.):** Wood-Leaf Segmentation (PCA eigenvalue + PointNet++ training prep)
- **Sprint 2 (14 มิ.ย. – 28 มิ.ย.):** 3D viewer (Three.js) + GIS map integration
- **Sprint 3 (29 มิ.ย. – 13 ก.ค.):** B2B Marketplace MVP + Carbon Report PDF generator

---

## 3. Git State (รายละเอียด)

### 3.1 Current State
```
Branch:        feat/proposal-nsc-template
Local HEAD:    005111f docs(proposal): rewrite outline.md to NSC 2026 Section 7 template
Remote main:   b68d0e4 (PR #14 merged 2026-05-25T07:43:25Z)
PR #13:        OPEN — waiting for review/merge
```

### 3.2 PR History (ที่ผ่านมา)

| PR | Title | Status | Note |
|---|---|---|---|
| **#13** | docs(proposal): rewrite outline.md to NSC Section 7 | OPEN | งานล่าสุด — รอ merge |
| #14 | (recent) | MERGED | 2026-05-25 |
| #12 | Sprint 0 foundations | MERGED | E2E notebook + Belgium + figures |
| #11 | Sprint 0 commit fixes | MERGED | Kotlin/AGP/TFLite fixes |
| #10 | Manual testing playbook | MERGED | docs only |
| #9 | RLS policies + handoff docs | MERGED | DB security |

### 3.3 ก่อน merge PR #13 — เช็คอะไร
```bash
gh pr view 13                     # ดู review status
gh pr checks 13                   # CI green ไหม
git log origin/main..HEAD --oneline  # ดูว่าอันนี้ behind/ahead เท่าไหร่
```

### 3.4 ถ้า PR #13 merge ไม่ได้ (เคยเจอ)
- **เคยเกิด:** PR #12 squash-merged ทำให้ history ตรงนี้แยกจาก main
- **วิธีแก้:** cherry-pick commit ของเราไปบน main สะอาด แล้ว push branch ใหม่:
  ```bash
  git fetch origin
  git checkout -b feat/proposal-nsc-template-v2 origin/main
  git cherry-pick 005111f
  git push -u origin feat/proposal-nsc-template-v2
  gh pr create --title "..." --body "..."
  ```

---

## 4. งานที่ทำเสร็จไปแล้ว (ช่วง 24-25 พ.ค.)

### 4.1 ✅ Mobile App Build Fixes
- **Kotlin 2.3.20 incremental cache bug (Windows):** เพิ่ม `kotlin.incremental=false` + `kotlin.compiler.execution.strategy=in-process` ใน `apps/mobile/android/gradle.properties`
- **TFLite namespace collision (AGP 9):** Comment out `tflite_flutter` ใน `apps/mobile/pubspec.yaml` (Phase 2)
- **AndroidManifest merger conflict:** ใส่ `tools:replace="android:maxSdkVersion"` ที่ `WRITE_EXTERNAL_STORAGE`
- **Flutter 3.27+ migration:** `withOpacity` → `withValues(alpha:)`, `CardTheme` → `CardThemeData`

### 4.2 ✅ ML Pipeline (8 ขั้น) — เสร็จ Phase 1
ดู §6 รายละเอียดแต่ละขั้น ทุกขั้นมี unit test 25 ตัว pass ทั้งหมด

### 4.3 ✅ Synthetic Validation (in-house)
- Generator: `services/ml/pipeline/synthetic.py` (262 บรรทัด)
- Test pipeline: `services/ml/tests/test_synthetic_pipeline.py` (9 smoke tests)
- รัน E2E ได้ <10 วินาที บน CI

### 4.4 ✅ Belgium Validation (real-world dataset)
- **Dataset:** Demol et al. 2021 — Destructive harvest of 65 trees in Belgium (4 species)
- **Source:** Zenodo DOI [10.5281/zenodo.4557401](https://doi.org/10.5281/zenodo.4557401)
- **Script:** `services/ml/notebooks/validate_belgium.py` (318 บรรทัด)
- **Outputs:** `docs/proposal/figures/fig11_dbh_parity.png`, `fig12_height_parity.png`, `fig13_volume_parity.png`, `belgium_validation.csv`

**Results (สำคัญสำหรับ proposal):**

| Metric | MAE | RMSE | R² | n |
|---|---|---|---|---|
| **DBH** | **1.17 cm** | 1.54 cm | 0.94 | 65 |
| **Height** | **0.54 m** | 0.78 m | 0.96 | 65 |
| Volume | 0.058 m³ | 0.082 m³ | 0.88 | 65 |

→ research-grade accuracy, แข่งขันได้กับ commercial software เช่น TreeQSM/SimpleForest

### 4.5 ✅ Proposal v2 (LiDAR-primary positioning)
- File: `proposal/outline.md` — 974 บรรทัด, structure ตาม NSC 2026 Booklet §7
- Sections:
  - **7.1** Story Board (10-step user journey with annotations)
  - **7.2** Techniques used (LiDAR processing, allometric, GIS, ML segmentation)
  - **7.3** Tools (Python ecosystem, Next.js, Flutter, FastAPI)
  - **7.4** Software specification (functional/non-functional, interfaces)
  - **7.5** Scope of work (timeline, deliverables, evaluation criteria)

### 4.6 ✅ Figures (สำหรับ Proposal)
ทุกรูปอยู่ที่ `docs/proposal/figures/`:
- `fig01_synthetic_plot.png` — Top-down view of synthetic plot
- `fig02_synthetic_3d.png` — 3D synthetic
- `fig03_classified_ground.png` — Ground classification
- `fig04_normalized_heights.png` — Height normalization
- `fig05_chm.png` — Canopy Height Model
- `fig06_segmentation.png` — Tree segmentation (watershed)
- `fig07_wood_leaf.png` — Wood-leaf separation
- `fig08_qsm_dbh.png` — DBH measurement
- `fig09_architecture.png` — System architecture diagram (Tahoma font ภาษาไทย)
- `fig10_user_flow.png` — End-to-end user journey
- `fig11_dbh_parity.png` — Belgium DBH parity plot ⭐
- `fig12_height_parity.png` — Belgium Height parity plot ⭐
- `fig13_volume_parity.png` — Belgium Volume parity plot ⭐

### 4.7 ✅ Learning Guide (Thai, tutorial-level)
- Folder: `docs/learning/`
- 22 files: 1 README + chapters 01-21
- ภาษาไทย + ศัพท์เทคนิค EN
- Template สม่ำเสมอ: ปัญหา → หลักการ → สูตร → โค้ดของเรา → libraries → citation → ข้อจำกัด → คำถามตรวจ
- ใช้สำหรับ: ตอบกรรมการ + สอน Person A/B + base ทำ pitch deck

---

## 5. งานที่ค้างต้องทำ (Pending Tasks)

### 5.1 🔴 Critical (ก่อน 29 พ.ค.)

| # | งาน | Owner | Deadline | สถานะ |
|---|---|---|---|---|
| 11 | ตอบอาจารย์ Wannipa เรื่อง "ground truth 5 ต้น" (Messenger) — มี Version 2+Bonus ใน draft แล้ว | User | ASAP | in_progress |
| 12 | รับ 2 PDFs จากอาจารย์ (NSC2026.pdf + รูปตัวอย่างงาน.pdf) | User | ASAP | waiting on advisor |
| 13 | **Merge PR #13** (`feat/proposal-nsc-template`) เข้า main | User/AI | 26 พ.ค. | OPEN |
| 17 | ส่ง Proposal v2 ให้อาจารย์ review รอบ 2 | User | 26 พ.ค. | pending |
| 18 | เดินขอลายเซ็น (ที่ปรึกษา + คณบดี/ผอ.) | User | 26-28 พ.ค. | pending |
| 19 | **Upload Proposal ใน SIMs** | User | **29 พ.ค. 17:00** | pending |
| 20 | ถ่าย screenshots (4 mobile + 5 web) ส่งให้ Thanapa (Person B) | User | 27 พ.ค. | pending |

### 5.2 🟡 Sprint 1 (เริ่มหลัง 30 พ.ค.)

- **Wood-Leaf Segmentation** Phase 2: ใช้ PointNet++ (Qi et al. 2017) แทน PCA eigenvalue heuristic
- เตรียม training data: DALES, Semantic3D, หรือ in-house labeled
- Train + export TFLite model
- Integrate กับ pipeline ขั้นที่ 5

### 5.3 🟢 Backlog (Sprint 2+)

- 3D Viewer (Three.js + R3F) + Leaflet GIS overlay
- 3D Viewer Web (Next.js page)
- B2B Marketplace MVP (listing + bid + matching)
- Carbon Report PDF generator (T-VER metadata)
- TGO 5 species expansion → 20+ species

---

## 6. ML Pipeline 8 ขั้น (สรุปสั้น — ละเอียดดูที่ `docs/learning/04-12-*.md`)

### Pipeline Flow
```
.las/.ply/.laz Input
       ↓
[1] Ground Classification    → CSF or grid percentile heuristic
       ↓
[2] Height Normalization     → KD-tree + IDW, z_norm = z - DTM(x,y)
       ↓
[3] Canopy Height Model      → Max-Z rasterization + grey-closing (Phase 2: pit-free)
       ↓
[4] Tree Segmentation        → Watershed (scikit-image), local maxima → flood-fill
       ↓
[5] Wood-Leaf Separation     → PCA eigenvalue (linearity/planarity) — Phase 2: PointNet++
       ↓
[6] QSM (DBH + Height + Vol) → RANSAC circle fit @ z=1.3m + taper equation V=π/4·D²·H·f
       ↓
[7] Species Classification   → ResNet-50 (Phase 2) — currently default to scope species
       ↓
[8] Allometric Carbon        → AGB → BGB → Carbon → CO₂eq
```

### Per-Step File Map

| Step | File | Phase 1 Approach | Phase 2 Plan |
|---|---|---|---|
| 1 | `services/ml/pipeline/ground_classification.py` | Grid percentile heuristic | Cloth Simulation Filter (Zhang 2016) |
| 2 | `services/ml/pipeline/height_normalization.py` | KD-tree + IDW | (Phase 1 sufficient) |
| 3 | `services/ml/pipeline/canopy_height_model.py` | Max-Z + grey-closing | Pit-free (Khosravipour 2014) |
| 4 | `services/ml/pipeline/tree_segmentation.py` | Watershed + local maxima | Marker-controlled watershed |
| 5 | `services/ml/pipeline/wood_leaf_separation.py` | Batched PCA eigenvalue | PointNet++ trained model |
| 6 | `services/ml/pipeline/qsm.py` | RANSAC circle + taper eq. | TreeQSM full cylinder model (Raumonen 2013) |
| 7 | (TBD) `species_classifier.py` | Default scope species | ResNet-50 transfer learning + TFLite |
| 8 | `services/ml/pipeline/allometric.py` | TGO + Chave 2014 | (Phase 1 sufficient) |

### Critical Formulas (จำให้แม่น)

```
[Allometric — สูตรหลัก]
  AGB = a × DBH^b × H^c             # species-specific (TGO 2017)

[Allometric — fallback ถ้าไม่รู้ species]
  AGB = 0.0673 × (ρ × DBH² × H)^0.976   # Chave et al. 2014 pantropical

[Below-ground biomass]
  BGB = AGB × 0.24                  # IPCC 2006 default for tropical forests

[Carbon stock]
  C   = (AGB + BGB) × 0.47          # 47% carbon fraction (IPCC 2006)

[CO₂ equivalent]
  CO₂eq = C × 44/12 = C × 3.667

[Stem volume — taper equation]
  V_stem = (π/4) × DBH² × H × form_factor
  form_factor ≈ 0.50  (tropical hardwood, FAO 2003)
```

---

## 7. โครงสร้างไฟล์สำคัญ (ที่ AI/User ต้องรู้)

### 7.1 Repository Root
```
D:\Project_Carbon\
├── apps\
│   ├── web\              # Next.js 14 + TypeScript + Tailwind + shadcn
│   └── mobile\           # Flutter 3.44 + Riverpod + (TFLite phase 2)
├── services\
│   ├── api\              # FastAPI + SQLAlchemy 2.0 async + asyncpg
│   └── ml\               # ⭐ ML pipeline — โฟกัสหลัก
│       ├── pipeline\         # 8 modules (ground, height, chm, segm, woodleaf, qsm, allometric, synthetic)
│       ├── tests\            # 25 tests total (16 allometric + 9 e2e)
│       ├── notebooks\        # validate_belgium.py, make_diagrams.py, e2e_validation.ipynb
│       └── data\             # species_db.csv (5 species)
├── docs\
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT_PLAN.md       # ~1500 บรรทัด, sprint-by-sprint
│   ├── SESSION_HANDOFF.md        # ⭐ ไฟล์นี้
│   ├── learning\                 # 22 chapters Thai tutorial
│   │   ├── README.md             # Master index
│   │   ├── 01-overview.md
│   │   ├── 02-core-concepts.md
│   │   ├── ...
│   │   ├── 12-ml-step8-allometric.md   # บทสำคัญที่สุด (สูตรคาร์บอน)
│   │   └── 21-references-glossary.md
│   ├── ml\
│   │   ├── PIPELINE.md           # 385 บรรทัด, ML pipeline reference
│   │   ├── ALLOMETRIC.md         # สูตรหลัก
│   │   └── DATASETS.md
│   ├── proposal\
│   │   ├── SYSTEM_OVERVIEW.md    # v2 LiDAR-primary positioning
│   │   └── figures\              # 13 figures + 2 CSVs
│   ├── decisions\                # 6 ADRs (0001-0006)
│   └── superpowers\plans\        # Implementation plans
├── proposal\
│   └── outline.md                # ⭐ 974 บรรทัด, NSC Section 7 template
├── packages\                     # Monorepo shared (pnpm + Turborepo)
├── CLAUDE.md                     # Project instructions
└── README.md
```

### 7.2 ไฟล์ที่ AI ใหม่ควรอ่านก่อน (เรียงตามลำดับ)

1. **`CLAUDE.md`** (root) — Project context + glossary + preferences
2. **`docs/SESSION_HANDOFF.md`** (ไฟล์นี้) — สถานะปัจจุบัน
3. **`proposal/outline.md`** — Proposal v2 (NSC Section 7 template)
4. **`docs/learning/README.md`** — Master index ของ learning guide
5. **`docs/learning/12-ml-step8-allometric.md`** — สูตรคาร์บอนทั้งหมด (บทสำคัญสุด)
6. **`docs/proposal/SYSTEM_OVERVIEW.md`** — v2 positioning + Belgium results
7. **`services/ml/pipeline/*.py`** — Code ของ pipeline (อ่าน docstrings เป็นหลัก)
8. **`docs/DEVELOPMENT_PLAN.md`** — Sprint-by-sprint blueprint

### 7.3 ไฟล์ห้ามแตะถ้าไม่จำเป็น

- `apps/mobile/android/gradle.properties` — มี workaround ของ Kotlin 2.3 อยู่
- `apps/mobile/android/app/src/main/AndroidManifest.xml` — มี tools:replace workaround
- `apps/mobile/pubspec.yaml` — tflite_flutter ถูก comment ไว้จงใจ (Phase 2)
- `services/ml/pipeline/canopy_height_model.py` — มี fix `-np.inf` init เพื่อแก้ bug

---

## 8. Tech Stack & Tools

### 8.1 Stack สรุป

| Layer | Tech |
|---|---|
| **Web Frontend** | Next.js 14 (App Router, RSC) + TypeScript + Tailwind + shadcn/ui + Three.js + React Three Fiber + Leaflet + tus-js-client |
| **Mobile** | Flutter 3.44 + Riverpod + go_router + camera + geolocator + image_picker (TFLite Phase 2) |
| **API** | FastAPI (Python 3.11) + SQLAlchemy 2.0 async + asyncpg + Pydantic v2 + Supabase Auth (JWT) |
| **DB** | PostgreSQL 16 + PostGIS 3.4 (GIST index, ST_DWithin) |
| **ML** | NumPy + SciPy + scikit-image + scikit-learn + Open3D + laspy + PyTorch 2.3 (Phase 2: PointNet++) |
| **Infra** | Vercel (Web) + Railway (API) + Supabase (DB+Auth+Storage) + RunPod Serverless GPU (Phase 2) |
| **CI/CD** | GitHub Actions (5 workflows) + Ruff + ESLint + Flutter analyze + pytest |

### 8.2 Why Each Choice (สำหรับตอบกรรมการ)
- **Next.js 14:** RSC ลด client bundle, App Router ดี SEO
- **Flutter cross-platform:** 1 codebase → Android + iOS (ทีมไม่มี iOS dev เฉพาะ)
- **FastAPI async:** Python ecosystem + async I/O ดีสำหรับ large file upload (tus protocol)
- **PostGIS:** Spatial query `ST_DWithin` หา ต้นไม้ใกล้ๆ จุดที่ user click บน map
- **Supabase:** Auth + Storage + Realtime — ลดเวลา dev (ไม่ต้องเขียน Auth เอง)
- **RunPod Serverless GPU:** Pay-per-use (A10G ~$0.39/hr, RTX 4090 ~$0.74/hr) — เหมาะกับนักศึกษา

---

## 9. 5 Species ใน Scope (Phase 1)

ที่ `services/ml/data/species_db.csv`:

| Common (TH) | Scientific | Allometric (a, b, c) | Wood ρ (g/cm³) |
|---|---|---|---|
| สัก | *Tectona grandis* | 0.0673, 2.34, 0.65 | 0.66 |
| ยางนา | *Dipterocarpus alatus* | 0.0673, 2.34, 0.65 | 0.74 |
| ไผ่ | *Bambusa spp.* | (custom — Phase 2) | 0.40 |
| ยางพารา | *Hevea brasiliensis* | 0.0673, 2.34, 0.65 | 0.58 |
| มะค่าโมง | *Afzelia xylocarpa* | 0.0673, 2.34, 0.65 | 0.85 |

> **หมายเหตุ:** ค่า a/b/c ปัจจุบันใช้ Chave 2014 pantropical สำหรับทุก species (ยกเว้น species-specific table จาก TGO 2017). Phase 2 จะ refine ตาม T-VER methodology

---

## 10. แหล่งข้อมูล / Citations หลัก

### 10.1 Allometric & Biomass
- **Chave et al. 2014** — Improved allometric models for tropical forest trees. *Global Change Biology*, 20(10). DOI: 10.1111/gcb.12629
- **TGO 2017** — Thailand Greenhouse Gas Management Organization, T-VER methodology
- **IPCC 2006** — Guidelines for National Greenhouse Gas Inventories, Volume 4 (AFOLU), Chapter 4 (Forest Land)
- **Tsutsumi et al. 1983** — Studies on the structure and functions of bamboo forests

### 10.2 LiDAR Processing
- **Zhang et al. 2016** — An Easy-to-Use Airborne LiDAR Data Filtering Method Based on Cloth Simulation. *Remote Sensing*, 8(6)
- **Khosravipour et al. 2014** — Generating Pit-free Canopy Height Models from Airborne Lidar. *PE&RS*, 80(9)
- **Roussel et al. 2020** — lidR: An R package for analysis of Airborne Laser Scanning. *Remote Sensing of Environment*, 251

### 10.3 ML
- **Qi et al. 2017** — PointNet++: Deep Hierarchical Feature Learning on Point Sets. *NeurIPS 2017*
- **Raumonen et al. 2013** — Fast Automatic Precision Tree Models from Terrestrial Laser Scanner Data (TreeQSM). *Remote Sensing*, 5(2)

### 10.4 Datasets
- **Demol et al. 2021** — Establishing tree biomass through destructive sampling for forest inventory in Belgium. Zenodo DOI: 10.5281/zenodo.4557401 ⭐ (n=65, ที่เราใช้ validate)
- **NEON LiDAR** — National Ecological Observatory Network (USA) — Phase 2 plan

### 10.5 Compliance
- **CBAM** — EU Carbon Border Adjustment Mechanism (Regulation 2023/956)
- **T-VER** — Thailand Voluntary Emission Reduction Programme

---

## 11. Common Commands (Cheat Sheet)

### 11.1 Git
```bash
git status --short
git log --oneline -10
gh pr view 13                     # PR ปัจจุบัน
gh pr checks 13                   # CI status
gh pr list --state open           # PR ที่ open ทั้งหมด
git fetch origin && git log origin/main..HEAD --oneline  # ดู ahead/behind
```

### 11.2 ML Pipeline Testing
```bash
# จาก D:\Project_Carbon\services\ml
pytest                            # รัน tests ทั้งหมด (25 tests)
pytest tests/test_synthetic_pipeline.py -v   # E2E smoke
pytest tests/test_allometric.py -v           # สูตรคาร์บอน

# รัน Belgium validation (ใช้เวลา ~30 วินาที)
python notebooks/validate_belgium.py

# สร้าง diagrams ใหม่
python notebooks/make_diagrams.py
```

### 11.3 Web (Next.js)
```bash
# จาก D:\Project_Carbon\apps\web
pnpm dev                          # localhost:3000
pnpm build && pnpm start          # production preview
pnpm lint                         # ESLint
```

### 11.4 Mobile (Flutter)
```bash
# จาก D:\Project_Carbon\apps\mobile
flutter doctor -v                 # check setup
flutter pub get                   # install deps
flutter run                       # debug build → device
flutter analyze                   # lint
flutter build apk --release       # release APK
```

### 11.5 API (FastAPI)
```bash
# จาก D:\Project_Carbon\services\api
uvicorn app.main:app --reload     # localhost:8000
pytest                            # API tests
ruff check . --fix                # lint + auto-fix
```

### 11.6 Database (Supabase local)
```bash
supabase start                    # local stack (Postgres + Auth + Storage)
supabase db reset                 # ลบ + apply migrations ใหม่
supabase migration new <name>     # สร้าง migration ใหม่
```

---

## 12. Known Issues / Gotchas

### 12.1 Kotlin 2.3.20 + Windows
- **ปัญหา:** Incremental compilation cache corruption on Windows
- **แก้แล้ว:** `apps/mobile/android/gradle.properties` มี:
  ```
  kotlin.incremental=false
  kotlin.compiler.execution.strategy=in-process
  ```
- **อย่าลบ** ทั้งสองบรรทัดนี้ จนกว่า Kotlin 2.4+ จะ fix bug

### 12.2 NumPy 2.0 Breaking Changes
- `.ptp()` method ถูกลบ → ใช้ `np.ptp(arr)` แทน
- `np.float_`, `np.int_` ถูก deprecate → ใช้ `np.float64`, `np.int64`

### 12.3 CHM `np.maximum.at` with NaN
- **อย่า** initialize CHM array เป็น `np.nan` ก่อน `np.maximum.at` — มันจะ corrupted
- **ทำ:** init เป็น `-np.inf`, ทำ reduction, แล้วค่อยแปลง `-inf` → `NaN` หลังเสร็จ

### 12.4 QSM DBH Over-segmentation
- ถ้า Watershed segment "ต้นเดียว" เป็นหลายต้น, RANSAC จะ fit circle ที่ใหญ่ผิดปกติ
- **แก้แล้ว:** ใส่ `max_radius_m=0.6` cap + median-cluster filter ใน `qsm.py`

### 12.5 Allometric with DBH=0
- ถ้า QSM ล้มเหลว (n=0 points in slice), DBH=0 → allometric จะคำนวณคาร์บอนเป็น 0
- **Pattern:** Filter `if res.dbh_cm < 2.0: continue` ก่อนส่งเข้า allometric

### 12.6 matplotlib + Thai font
- **ปัญหา:** ภาษาไทยขึ้นเป็น `□□□` (tofu)
- **แก้:** `plt.rcParams['font.family'] = 'Tahoma'` (Windows-bundled) — อย่าใช้ emoji glyph

### 12.7 GH API + Backticks ใน body
- **ปัญหา:** Bash interpret backticks ใน `gh api -f body="..."` → command injection
- **วิธี:** ใช้ heredoc + escape backticks หรือ post + PATCH ทีหลัง

### 12.8 PR Squash Merge Conflict
- เมื่อ main ถูก squash-merge, history แยกออกจาก feature branch
- ถ้า rebase ไม่สะอาด → abort + cherry-pick onto clean main แทน (ดู §3.4)

---

## 13. Glossary (จาก CLAUDE.md + เพิ่มเติม)

| Term | Meaning |
|---|---|
| **AGB** | Above-Ground Biomass — มวลชีวภาพเหนือพื้นดิน (kg) |
| **BGB** | Below-Ground Biomass — มวลรากใต้ดิน (≈ AGB × 0.24) |
| **Allometric** | สมการแอลโลเมตริก — แปลง dimension (DBH, H) → biomass |
| **CBAM** | Carbon Border Adjustment Mechanism (EU import carbon tax) |
| **CHM** | Canopy Height Model — raster ความสูงเรือนยอด |
| **CSF** | Cloth Simulation Filter (Zhang 2016) — ground classification |
| **DBH** | Diameter at Breast Height — เส้นผ่านศูนย์กลางลำต้นที่ 1.3 m |
| **IDW** | Inverse Distance Weighting — interpolation method |
| **ITD** | Individual Tree Detection |
| **MVS** | Multi-View Stereo (photogrammetry) |
| **NEON** | National Ecological Observatory Network (US public LiDAR) |
| **PCA** | Principal Component Analysis (eigenvalue-based geometry) |
| **PointNet++** | Hierarchical deep learning on point sets (Qi 2017) |
| **QSM** | Quantitative Structure Model — cylinder volume estimation |
| **RANSAC** | Random Sample Consensus — robust circle fit |
| **RSC** | React Server Components |
| **SfM** | Structure from Motion (photogrammetry) |
| **TGO** | Thailand Greenhouse Gas Management Organization (อบก.) |
| **TLS** | Terrestrial Laser Scanning (ground-based LiDAR) |
| **T-VER** | Thailand Voluntary Emission Reduction Programme |
| **Watershed** | Image segmentation algorithm (flood-fill from local maxima) |

---

## 14. แผนที่นัย Recommended Next Actions

### ถ้า AI Session ใหม่เปิดมาวันที่ 26 พ.ค.
1. อ่าน `CLAUDE.md` + ไฟล์นี้
2. Check PR #13 — ถ้ายังเปิดอยู่ → merge ก่อนทำอื่น
3. Pull main: `git checkout main && git pull origin main`
4. User เข้าวันนี้ → ช่วยส่ง Proposal ให้อาจารย์ review (#17)

### ถ้าเปิดมาวันที่ 27-28 พ.ค.
- User น่าจะอยู่ระหว่างเดินขอลายเซ็น
- ระหว่างนั้น AI ช่วย:
  - ถ่าย screenshots ของ Web/Mobile (#20)
  - เตรียม pitch deck draft (Person B จะใช้ Figma)
  - Review proposal ครั้งสุดท้ายว่า format ตรง NSC template

### ถ้าเปิดมาวันที่ 29 พ.ค. (D-Day)
- **Priority 1:** Upload ใน SIMs ก่อน 17:00 (#19)
- AI ช่วย: convert outline.md → DOCX/PDF format ตามที่ SIMs ต้องการ
- AI เตือน user เรื่อง deadline ทุก 2 ชั่วโมง

### ถ้าเปิดมาวันที่ 30 พ.ค.+ (หลัง Proposal)
- เริ่ม Sprint 1: Wood-Leaf Segmentation Phase 2
- เตรียม training data PointNet++
- Setup RunPod account + cost monitoring

---

## 15. การติดต่อ + Links

- **GitHub Repo:** https://github.com/Remote55/carbonscan-ai
- **PR #13 (รอ merge):** https://github.com/Remote55/carbonscan-ai/pull/13
- **NSC 2026 SIMs:** https://www.nsc.or.th/sims/ (Upload deadline 29 พ.ค. 17:00)
- **Zenodo Belgium dataset:** https://doi.org/10.5281/zenodo.4557401
- **TGO T-VER:** https://ghgreduction.tgo.or.th/th/tver.html

---

## 16. Final Notes for AI Assistant ใหม่

### Preferences (จาก CLAUDE.md)
- **ตอบเป็นภาษาไทย** — Technical terms ใช้ EN ได้
- **โฟกัส:** "ทำให้กรรมการ NSC ว้าว" — Deep Tech + Visual storytelling
- **หลีกเลี่ยง:** Over-engineering — Prototype ที่เสร็จ > Vision สมบูรณ์แต่ไม่เสร็จ
- **งบ:** นักศึกษา — ทุก decision พิจารณา "จ่ายไหวไหม"

### Working Style ที่ User ชอบ
- ละเอียดแบบมืออาชีพ (ไม่ใช่แค่ขั้นตอน — ต้องเข้าใจ "ทำไม")
- ใช้ tables / diagrams เยอะ
- ทำงานเป็น atomic commits + PR แยกตาม feature
- Test ทุก step ที่เขียน (ใช้ pytest, flutter test, jest)

### สิ่งที่ User ไม่ชอบ
- Reply สั้นๆ แบบ "ผมจะทำให้" โดยไม่ explain
- เปลี่ยน decision เก่าโดยไม่ถาม (เช่น undo workaround Kotlin 2.3)
- Over-engineer แบบ "ทำ feature ที่ scope ไม่มี"
- ใช้ emoji เกินจำเป็น (ใส่นิด ๆ ในตารางได้ แต่ไม่เต็มข้อความ)

### Skills ที่ User ใช้บ่อย
- `/superpowers:brainstorming` — สำหรับ design discussion
- `/superpowers:writing-plans` — สำหรับ implementation plan
- `/superpowers:using-git-worktrees` — สำหรับ git operations
- `/superpowers:writing-skills` — สำหรับ documentation

---

**สรุปสั้นสุดสำหรับ AI ใหม่:**
> โปรเจกต์ NSC 2026 ใกล้ deadline 29 พ.ค. ระบบ ML pipeline เสร็จแล้ว validate กับ Belgium dataset ได้ research-grade. งานที่เหลือคือ proposal submission + signature workflow. PR #13 รอ merge — handle ก่อนทำอื่น

> สำหรับงาน ML/Code — ทุกอย่างใน `services/ml/` มี test pass หมด ห้ามแก้โดยไม่รัน pytest ก่อน
