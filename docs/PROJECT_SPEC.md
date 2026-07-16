# TreeQ Carbon Platform — Master Project Spec

> **จุดประสงค์ของเอกสารนี้:** เป็น "context ก้อนเดียวจบ" สำหรับเปิด session ใหม่ (Claude หรือคนใหม่ในทีม)
> อ่านจบแล้วต้องเข้าใจว่า **เรากำลังทำอะไร, ทำถึงไหน, ตัดสินใจอะไรไปแล้ว, และเหลืออะไร**
> อัปเดตล่าสุด: **2026-07-16** · เขียนโดย AI จากการอ่านโค้ด/เอกสารจริงในโปรเจกต์
> ⚠️ ตัวเลข/สถานะในเอกสารนี้เป็น ณ วันที่เขียน — ก่อนอ้างอิงให้ verify กับโค้ดปัจจุบันอีกครั้ง

---

<!-- TREEQ_TRUTH_START -->
### Verified truth snapshot (generated)

- Baseline: `tlsep` — **Implemented**.
- PointNet++: **Experimental**, not promoted; no verified independent final-test gate.
- Wan 2021 held-out: Wood IoU `0.418`, Leaf IoU `0.808`, Mean IoU `0.613`, accuracy `0.831`. The held-out loader was also used for best-epoch selection.
- Demol isolated-tree validation (65 trees): DBH MAE `1.1673846154 cm`; Volume MAPE `18.7650916186%`. This is not an eight-stage or carbon validation.
- Deterministic core demo: `3` trees, `1320.39 kg C`, `4841.48 kg CO2e`; analyzed commit `9d7b43c3a29a` with a clean worktree.
- Species classification: **Stub**. Carbon stock/CO2e estimates are not certified credits.
<!-- TREEQ_TRUTH_END -->

## 0. วิธีใช้เอกสารนี้ (สำหรับ session ใหม่)

1. อ่าน §1 (TL;DR) + §17 (สถานะ) ก่อน จะเห็นภาพรวมเร็วสุด
2. งานโค้ด → ดู §7 (โครงสร้าง repo) + §9–16 (แต่ละส่วน)
3. งานวิทยาศาสตร์/คาร์บอน → §10–11
4. อย่าเพิ่งเชื่อทุกอย่าง — ไฟล์จริงคือ source of truth เสมอ (เอกสารบางส่วนเขียนเป็น "target" ไม่ใช่ "สิ่งที่ทำเสร็จ" — §17 บอกความจริง)

---

## 1. TL;DR (Elevator Pitch)

**TreeQ Carbon Platform** = แพลตฟอร์มประเมิน **คาร์บอนชีวมวลต้นไม้** จาก **3D point cloud** ด้วย AI
แล้วต่อยอดเป็น **B2B carbon offset matchmaking**

Pipeline หัวใจ: รับ point cloud (LiDAR `.las/.laz` หรือจากภาพถ่ายมือถือผ่าน photogrammetry)
→ AI แยก **ลำต้น (wood) ออกจากใบ (leaf)** → วัด **DBH + ความสูง** → คำนวณ **ชีวมวล → คาร์บอน → CO₂e**
ด้วยสมการมาตรฐาน (TGO / Chave 2014 / IPCC) แบบ **โปร่งใส ตรวจสอบได้ทุกจุด**

**จุดขายต่อกรรมการ NSC:** Deep Tech (point cloud + deep learning) + Visual storytelling (3D viewer)
+ ความ "ซื่อสัตย์เชิงวิศวกรรม" (รายงานตัวเลขจริงพร้อมข้อจำกัด ไม่เคลม overselling)

---

## 2. บริบทการแข่งขัน (NSC 2026)

| หัวข้อ | รายละเอียด |
|---|---|
| งาน | **NSC 2026** (National Software Contest ครั้งที่ 28) |
| หมวด | **หมวด 14** — โปรแกรมเพื่องานการพัฒนาด้านวิทยาศาสตร์และเทคโนโลยี |
| ระดับ | อุดมศึกษา (ปริญญาตรี) |
| Deadline | Proposal: **29 พ.ค. 2569** · Final Report: **17 ก.ค. 2569** |
| กติกาเสี่ยง | ระบบปิดอัตโนมัติ 17:00 น. — ห้ามเลท · ต้องเดินลายเซ็นที่ปรึกษา + คณบดี (ใช้เวลา 2–3 วัน) |

---

## 3. ทีม

| Role | ผู้รับผิดชอบ | โฟกัส |
|---|---|---|
| **Lead / Core** | User (เจ้าของ repo) | AI/ML, Mobile (Flutter), Backend (FastAPI), Team Lead, Proposal |
| **Frontend** | Person A | Next.js Web Dashboard, 3D Viewer, GIS Map |
| **Design** | Person B | UI/UX (Figma), Branding, Video, Slides |

> ทีมเป็นนักศึกษา — ไม่มีงบซื้อ hardware แพง, ไม่มี iPhone LiDAR, ไม่มี GPU แรง → ทุก decision ต้องดู "นักศึกษาจ่ายไหวไหม"

---

## 4. ตัวโปรดักต์ (ปัญหา → ทางแก้ → คุณค่า)

**ปัญหา:** การประเมินคาร์บอนป่าไม้แบบเดิมต้องใช้ผู้เชี่ยวชาญเดินวัดต้นไม้ทีละต้น (DBH ด้วยสายวัด, ความสูงด้วย clinometer)
→ แพง, ช้า, สเกลไม่ได้, ตรวจสอบย้อนหลังยาก

**ทางแก้ (3 เสาหลัก):**
1. **LiDAR/Point-cloud carbon assessment** — สแกน/ถ่ายภาพ → วัดต้นไม้อัตโนมัติทั้งแปลง
2. **AI Wood-Leaf Segmentation** — deep learning แยกลำต้น-ใบ ให้วัดปริมาตรไม้ได้แม่นขึ้น
3. **B2B Carbon Offset Matchmaking** — จับคู่ป่า/เจ้าของที่ดินกับองค์กรที่ต้องชดเชยคาร์บอน

**คุณค่า:** ลดต้นทุนการประเมิน ~**100 เท่า** · โปร่งใส (เปิดดู 3D + พิกัด GPS ได้ทุกต้น) · เข้ามาตรฐาน TGO/IPCC

---

## 5. Branding ⚠️ (เปลี่ยนชื่อแล้ว)

- **ชื่อปัจจุบัน: `TreeQ Carbon Platform`** (ทีมตัดสินใจ 2026-07-16)
- **ชื่อเดิม `CarbonScan AI` = เลิกใช้** — แต่ยังหลงเหลือในหลายไฟล์ (~157 จุด / 76 ไฟล์)
- rebrand เสร็จแล้วเฉพาะ **apps/web** (nav/footer/metadata/หน้า auth+dashboard) — commit `aa1ea85`
- **ยังไม่ rebrand:** mobile app (`apps/mobile`), เอกสาร (`docs/`, `proposal/`), README, brand assets, Android app label, GitHub repo name (`carbonscan-ai`)
- Logo bug: `apps/web/public/logo.png` เป็นโลโก้เดิม — ยังไม่เปลี่ยน

---

## 6. Tech Stack

| ชั้น | เทคโนโลยี |
|---|---|
| **Web** | Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui + React Three Fiber/Three.js (3D viewer) + Leaflet (map) |
| **Mobile** | Flutter (Android+iOS) + Riverpod + go_router + dio + camera/geolocator + Supabase + (TFLite — deferred) |
| **Backend** | FastAPI (Python) + SQLAlchemy 2.0 async + asyncpg + Pydantic v2 + Alembic + PostgreSQL/PostGIS + Supabase |
| **AI/ML** | PyTorch + PointNet++ + Open3D + laspy + PDAL + scikit-image + COLMAP/OpenMVS (photogrammetry) |
| **Cloud** | Vercel (web) + Railway/RunPod (API+GPU, ตอน demo ใช้ Cloudflare tunnel ฟรี) + Supabase (auth+DB+storage) |

---

## 7. โครงสร้าง Monorepo

```
D:\Project_Carbon\
├── apps/
│   ├── web/                    Next.js — เว็บ dashboard + landing + 3D viewer
│   │   └── src/
│   │       ├── app/            (App Router) page.tsx=landing, layout.tsx, (auth)/ (dashboard)/
│   │       ├── components/     viewer/point-cloud-viewer.tsx ฯลฯ
│   │       ├── lib/            api.ts (API client), supabase.ts, utils.ts
│   │       └── middleware.ts   Supabase session refresh + guard
│   └── mobile/                 Flutter — สแกน/ถ่ายภาพ → คาร์บอน
│       └── lib/                main.dart, app.dart, core/, features/(camera,tree_scan,results,species_id), shared/
├── services/
│   ├── api/                    FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py         entrypoint (lifespan, CORS)
│   │   │   ├── api/v1/         router.py, health.py, auth.py, trees.py, upload.py, jobs.py
│   │   │   ├── api/deps.py     DI (get_job_store, CurrentUser)
│   │   │   ├── models/         user.py, tree.py, job.py (SQLAlchemy ORM)
│   │   │   ├── schemas/        Pydantic: auth, tree, analyze, job
│   │   │   ├── services/       pipeline_runner.py, job_store.py, job_input.py,
│   │   │   │                   upload_validation.py, supabase.py
│   │   │   ├── worker.py       async job worker (python -m app.worker)
│   │   │   └── core/           config.py, database.py, security.py, exceptions.py
│   │   └── alembic/            migrations (0001_initial_schema, 0002_job_result_json)
│   └── ml/                     PyTorch pipeline (heavy deps)
│       ├── pipeline/           8-step pipeline (ดู §9) + main.py orchestrator + allometric.py
│       ├── training/           woodleaf_dataset.py, realdata_dataset.py, train_woodleaf.py
│       ├── data/               species_db.csv (source of truth ค่า allometric)
│       ├── tests/              pytest (allometric 15+, realdata, ฯลฯ)
│       └── notebooks/          Colab notebooks (fine-tune, diagrams, e2e)
├── docs/                       เอกสารทั้งหมด (ml/, learning/, decisions/, proposal/, superpowers/)
├── proposal/                   NSC proposal (outline.md, advisor_email.md)
├── memory/                     project memory (context/, projects/, glossary)
├── assets/brand/               โลโก้/แบรนด์
└── CLAUDE.md                   working memory (โหลดเข้า context อัตโนมัติ)
```

---

## 8. สถาปัตยกรรมระบบ

### Dual-Input Pipeline (decision 0004)
รับ input ได้ 2 ทาง แล้วรวมเป็น point cloud เดียวก่อนเข้า pipeline:
1. **`.las/.laz` upload** — จาก public dataset / auditor ที่มีเครื่อง LiDAR (อ่านตรงด้วย `laspy` ไม่ต้องแปลง)
2. **Photogrammetry** — ถ่ายภาพมือถือ 30–50 รูปรอบต้น → COLMAP/OpenMVS → point cloud
   (เพราะทีมไม่มี iPhone LiDAR — decision 0002)

### Data Flow (async job — Phase 2, ทำเสร็จแล้ว)
```
Web/Mobile → POST /api/v1/jobs/analyze (อัปโหลดไฟล์)
          → API สร้าง job (status=queued) → 202 + job_id
Worker (python -m app.worker) → หยิบ job (FOR UPDATE SKIP LOCKED)
          → รัน ML pipeline (subprocess ผ่าน pipeline_runner)
          → เขียนผล carbon ลง result_json → status=completed
Web/Mobile → GET /api/v1/jobs/{id} (poll) → ได้ผลเมื่อ completed
```
> มี **sync endpoint** `POST /api/v1/upload/analyze` ด้วย (รันทันที รอผล) — ใช้ตอน demo ผ่าน tunnel เพราะยังไม่มี worker ที่ deploy จริง

---

## 9. ML Pipeline — 8 ขั้นตอน (หัวใจโปรดักต์)

Input: `.las/.laz/.ply` point cloud → pre-process (filter outliers, voxel downsample) → 8 ขั้น → JSON ต่อต้น
โค้ด orchestrator: `services/ml/pipeline/main.py` · แต่ละขั้นเป็นไฟล์แยกใน `services/ml/pipeline/`

| # | ขั้นตอน | ไฟล์ | Algorithm / Lib | สถานะจริง |
|---|---|---|---|---|
| 1 | Ground Classification | `ground_classification.py` | Cloth Simulation Filter (PDAL) | ✅ |
| 2 | Height Normalization | `height_normalization.py` | DTM subtraction (TIN) | ✅ |
| 3 | Canopy Height Model | `canopy_height_model.py` | Pit-free CHM (Khosravipour 2014) | ✅ |
| 4 | Tree Segmentation (ITD) | `tree_segmentation.py` | Watershed (scikit-image) | ✅ |
| 5 | **Wood-Leaf Segmentation** ⭐ | `wood_leaf_separation.py` | PointNet++ (DL) **หรือ** PCA heuristic (`tlsep`) | ✅ 2 โหมด (ดู §11) |
| 6 | QSM (ปริมาตรไม้) | `qsm.py` | RANSAC circle + stacked cylinders | ✅ |
| 7 | **Species Classification** ⭐ | `species_classifier.py` | (target: ResNet-50 บน RGB) | ⚠️ **STUB** — คืนค่า default; ยังไม่เทรนจริง |
| 8 | Allometric → Carbon | `allometric.py` | TGO/Chave/IPCC (ดู §10) | ✅ 15+ tests ผ่าน |

- **Class codes:** `0 = wood`, `1 = leaf`, `2 = ground`
- **synthetic.py** = ตัว generate ต้นไม้สังเคราะห์ (ใช้เทรน/augment wood-leaf)
- **ply_export.py** = export point cloud + class ต่อจุด (ให้ 3D viewer / ให้อาจารย์เปิด)
- **realdata_eval.py / field_eval.py** = ประเมินผลบนข้อมูลจริง
- Output JSON: `{tree_id, dbh_cm, height_m, volume_m3, biomass_kg, carbon_kg, co2eq_kg, wood_leaf_iou, ...}` + `summary`
- เวลา target ~10 นาที/แปลง (30–50 ต้น)

---

## 10. คณิตศาสตร์คาร์บอน (Allometric)

**สมการหลัก (species-specific, Tier 2/3):**
```
AGB = a × DBH^b × H^c        (kg)     — DBH เป็น cm, H เป็น m
```
**Fallback (unknown species, Tier 1 — Chave 2014 pantropical):**
```
AGB = 0.0673 × (ρ × DBH² × H)^0.976   — ρ = wood density g/cm³
```
**ต่อยอด:**
```
BGB     = AGB × 0.24         (root:shoot ratio, IPCC 2006; ไผ่ใช้ 0.20)
Biomass = AGB + BGB
Carbon  = Biomass × 0.47     (carbon fraction, IPCC)
CO₂eq   = Carbon × 44/12
```
- **Source of truth ค่า a,b,c,ρ:** `services/ml/data/species_db.csv` (โหลดผ่าน `load_species_db()`)
- **5 ชนิด pilot:** สัก (Tectona), ยางนา (Dipterocarpus), ไผ่ (Bambusa), ยางพารา (Hevea), มะค่าโมง (Afzelia)
- **Cross-validation:** คำนวณ 2 วิธีคู่กัน (allometric DBH-H **vs** V×ρ จาก QSM) — ต่างกัน >30% → flag manual review
- **ตัวอย่าง verified:** ไม้สัก DBH 30cm สูง 18m → **1.233 tCO₂eq** (≈ ฿2,466 @ ฿2/kg)
- ⚠️ **Action ค้าง:** verify ค่าสัมประสิทธิ์กับ **TGO Forestry Guideline 2017** ตัวจริง (มะค่าโมงตอนนี้ใช้ค่า Chave adjusted เพราะขาดงานวิจัยไทย)

---

## 11. Wood-Leaf Model — สถานะจริง + ตัวเลขที่ต้องรายงานอย่างซื่อสัตย์

**2 โหมดใน `wood_leaf_separation.py`:**
- `tlsep` = PCA/geometric heuristic (ไม่ต้องเทรน — ใช้เป็น baseline/fallback)
- `pointnet` = PointNet++ (deep learning — ตัวหลัก)

**ผลจริง (`docs/ml/WOODLEAF_RESULTS.md`):**
| ชุดทดสอบ | ผล |
|---|---|
| Synthetic test (in-distribution) | mean IoU **0.978** |
| Real TLS zero-shot (synthetic→real) | mean IoU ~**0.33** (wood ~0.19) |
| **Real TLS (Wan 2021) เทรน same-environment + synthetic augment** | **mean IoU 0.61 / wood IoU 0.42** ⭐ best variant |

- **Honest arc (ใช้ในเล่ม):** synthetic 0.978 → zero-shot real 0.33 → train-on-real 0.61 → (roadmap) เพิ่ม dataset ปิด gap
- **Geometry validation:** DBH MAE **1.17 cm**, ความสูง MAE **0.54 m** (เทียบไม้โค่นจริง)
- ตัวเลขพวกนี้ = จุดขาย "ซื่อสัตย์" ห้ามปัดเป็นเลขสวยเกินจริง

---

## 12. Dataset Strategy ⚠️ (เปลี่ยนทิศตามอาจารย์ 2026-07-15)

**คำสั่งอาจารย์:** **ไม่ต้องเก็บ/สแกนข้อมูลต้นไม้ไทยเอง** — ใช้ **open dataset ดีๆ** มาเทรน wood-leaf แทน
(ตัดเฉพาะ "การเก็บ training data ไทย" — **ไม่แตะ** ฟีเจอร์ photogrammetry/มือถือ ที่เป็น product input)

**Loader contract (`services/ml/training/realdata_dataset.py`) — สำคัญมากถ้าจะเพิ่ม dataset:**
- รับ per-point `(x, y, z, label)` โดย `label: 0=wood, 1=leaf`
- โค้ด generic (`tile_samples`, `spatial_split`, `build`) reuse ได้ — ที่ผูกกับ Wan มีแค่ `load_wan_plot()`
- **เพิ่ม dataset ใหม่ = เขียน `load_<ชุด>_plot()` เล็กๆ ~20-40 บรรทัด** ไม่ต้องรื้อ pipeline
- ถ้า label เป็น stem/branch/foliage → map: ลำต้น+กิ่ง→0, ใบ→1

**Dataset ปัจจุบัน + candidate:**
| ชุด | label wood/leaf ต่อจุด? | สถานะ |
|---|---|---|
| **Wan et al. 2021** (Dryad `10.5061/dryad.rfj6q5799`, CC-BY, 73 trees/3 species) | ✅ | ใช้แล้ว = แกนหลัก (0.61) |
| TLSeparation (6 trees) | ✅ | มีในเอกสาร ใช้ validate ข้ามชุด |
| **LeWoS / Wang 2020**, **FOR-instance** | ✅ / semantic (ต้อง verify) | candidate เพิ่ม → ดัน wood IoU |
| NEON Veg Structure | ❌ (มี DBH/H วัดจริง) | ใช้ validate allometric ไม่ใช่ wood-leaf |

> **งานค้างที่อาจารย์ให้ทิศมา:** research + verify open dataset ที่มี label wood/leaf ต่อจุด (LeWoS เป็นตัวหลัก) แล้ว wire เข้า loader → retrain เพื่อดัน wood IoU (0.42→สูงขึ้น)

---

## 13. Backend (FastAPI) — async-job architecture (ทำเสร็จแล้ว)

**Branch:** `feat/async-job-pipeline` (34 tests ผ่าน / 2 skip) — ยังไม่ merge เข้า main

**Endpoints (`app/api/v1/`):**
- `POST /api/v1/upload/analyze` — sync, รันทันที (ใช้ตอน demo tunnel)
- `POST /api/v1/jobs/analyze` — async, 202 + job_id (owner auth ผ่าน Supabase)
- `GET /api/v1/jobs/{id}` — poll สถานะ + ผล
- `GET /api/v1/jobs` — list jobs ของ user
- `GET /api/v1/health`, `/api/v1/auth/*`, `/api/v1/trees/*`

**ชิ้นส่วนสำคัญ:**
- `models/job.py` — Job ORM + `JobStatus`(queued/processing/completed/failed/cancelled) + `JobType`
- `services/job_store.py` — `JobStore` Protocol + `InMemoryJobStore`(tests) + `DbJobStore`(prod, `FOR UPDATE SKIP LOCKED`)
- `services/job_input.py` — เซฟไฟล์ที่อัปโหลด
- `services/pipeline_runner.py` — เรียก ML CLI แบบ subprocess
- `services/upload_validation.py` — ตรวจนามสกุล (`ANALYZE_EXTENSIONS`)
- `worker.py` — `process_one()` + `run_forever()` (รัน `python -m app.worker`)
- Migration `0002` เพิ่ม `result_json` JSONB
- Runbook: `services/api/docs/WORKER_RUNBOOK.md`
- Spec เต็ม: `docs/superpowers/plans/2026-07-10-async-job-pipeline.md`

**⚠️ Windows gotcha (แก้แล้ว):** emoji ใน `print()` ของ lifespan ทำ uvicorn crash บน cp874 console → เอา emoji ออกหมด (commit `6ca8693`)

---

## 14. Web (Next.js) — landing + viewer + auth

**Landing (`apps/web/src/app/page.tsx`) — rebuild ล่าสุด:**
- ธีม **nature-template** (ป่ายามเย็นวาดด้วย SVG + ฟอนต์สคริปต์ Pacifico + palette เขียว forest)
- **server component + Tailwind ล้วน** (ไม่มี canvas/3D, ไม่มี styled-jsx)
- Sections: Hero → Technology → Pipeline(4 ขั้น) → Validation(ตัวเลขจริง) → CTA → Footer
- ⚠️ **บทเรียนสำคัญ:** เวอร์ชันก่อนใช้ **canvas 3D + styled-jsx → เรนเดอร์ unstyled บน production**
  (styled-jsx ไม่ SSR ใน App Router ถ้าไม่มี style registry) → **ห้ามใช้ styled-jsx/canvas ในหน้า marketing อีก ใช้ Tailwind**

**ส่วนอื่น:**
- `components/viewer/point-cloud-viewer.tsx` — 3D viewer (React Three Fiber) แสดง wood/leaf
  ⚠️ เคยมีบั๊กสี three.js: vertex color เป็น linear-space แต่ canvas output sRGB → ต้องแปลง sRGB→linear ด้วย `THREE.Color`
- `lib/api.ts` — API client (`IS_API_CONFIGURED`, `getAccessToken`, `submitAnalyzeJob`, `getJob`, `pollJobUntilDone`)
- `middleware.ts` — refresh Supabase session + **guard**: ถ้าไม่มี Supabase env → ข้าม (ไม่ crash) [ให้ local dev เปิดได้]
- Auth: Supabase (`NEXT_PUBLIC_SUPABASE_URL` + `ANON_KEY`)

**Deploy:** Vercel → production alias **`treeqcarbon.vercel.app`**
- deploy ผ่าน `npx vercel --prod --archive=tgz --yes` (จาก `apps/web`)
- ⚠️ **vercel env gotcha:** ตั้ง env var ต้องใช้ `vercel env add NAME production --value "<v>" --no-sensitive --force --yes`
  (pipe/stdin ใช้ไม่ได้เมื่อรันโดย agent — จะได้ค่าว่าง!) · `--no-sensitive` ให้ pull กลับมา verify ได้

---

## 15. Mobile (Flutter)

- `apps/mobile` — `carbonscan_mobile` (ชื่อ package ยังไม่ rebrand), Flutter 3.22+, Dart 3.4+
- Stack: Riverpod + go_router + dio + camera + geolocator + permission_handler + Supabase
- Features: `camera/`, `tree_scan/`, `results/`, `species_id/`
- **run (Windows):** `cd apps/mobile && flutter pub get && .\scripts\run-dev.ps1` (อ่าน `.env` → `--dart-define`)
  - ต้องมี Android emulator/เครื่องจริงก่อน · `main.dart` **ยังไม่ init Supabase** (TODO) → รันได้แม้ไม่มี key
  - API URL: emulator ใช้ `http://10.0.2.2:8000` (default) · เครื่องจริงใช้ IP LAN + uvicorn `--host 0.0.0.0`
- ⚠️ **TFLite (on-device species) ถูก defer** — `tflite_flutter` ชน namespace `org.tensorflow.lite` กับ AGP 9.x (ดู `docs/decisions/0007`)

---

## 16. Deployment & Ops

| ส่วน | Prod | Demo (ตอนนี้) |
|---|---|---|
| Web | Vercel `treeqcarbon.vercel.app` | เหมือนกัน |
| API + ML | (target: Railway/RunPod GPU) | **Cloudflare quick tunnel ฟรี** → local API (`*.trycloudflare.com`) |
| DB/Auth/Storage | Supabase | เหมือนกัน |

- **สคริปต์เปิด backend สำหรับ demo:** `C:\Users\Acer\OneDrive\Desktop\CarbonScrip\start_backend.bat` (+ `.ps1`)
  → kill tunnel เก่า → เปิด API (uvicorn) → เปิด cloudflared → ดึง URL → `vercel env add` → redeploy
- Tunnel URL เปลี่ยนทุกครั้งที่ restart → สคริปต์อัปเดต Vercel env อัตโนมัติ (named tunnel ต้องมี domain เสียเงิน)

---

## 17. สถานะปัจจุบัน (ความจริง ณ 2026-07-16)

**✅ เสร็จ/ใช้งานได้:**
- ML pipeline 8 ขั้น (ยกเว้น species = stub) + allometric (15+ tests)
- Wood-leaf model เทรนบน Wan 2021 → mean IoU 0.61 / wood 0.42
- Backend async-job (branch `feat/async-job-pipeline`, 34 tests) + sync endpoint
- Web landing ใหม่ (nature-template Tailwind) — live บน `treeqcarbon.vercel.app`
- 3D viewer แสดง wood/leaf point cloud ได้
- E2E ผ่าน tunnel: POST point cloud → ได้คาร์บอนจริง (เช่น 1 ต้น → 207 kg C / 760 kg CO₂e)
- Report เล่ม NSC (เพิ่ม geometry MAE, allometric, roadmap, honesty caveats แล้ว — ไฟล์ใหม่ใน Downloads)

**⚠️ กำลังทำ / ค้าง:**
- Rebrand `CarbonScan AI → TreeQ Carbon Platform`: **เสร็จเฉพาะ web** · เหลือ mobile/docs/proposal/README/GitHub repo
- Species classifier (ขั้น 7): ยังเป็น stub — ต้องเทรน ResNet จริง (หลัง proposal)
- Dataset: research + verify open dataset (LeWoS) เพิ่ม → retrain ดัน wood IoU (ตามอาจารย์)
- Deploy API+worker จริง (RunPod/Railway) — ตอนนี้ยังใช้ tunnel
- verify allometric coefficients กับ TGO Guideline 2017 ตัวจริง

**📌 Git:** branch `feat/async-job-pipeline` — commit ล่าสุดชุด web (`68f168b`, `aa1ea85`) **ยังไม่ push GitHub / ยังไม่ merge main**

---

## 18. Decisions & Constraints หลัก

1. **Dual-input** (`.las` upload + photogrammetry) — decision 0004
2. **ไม่ใช้ iPhone LiDAR** (ทีมไม่มี → COLMAP/OpenMVS) — decision 0002
3. **Cloud GPU on-demand** แทนซื้อ workstation — decision 0005
4. **Open-source first** · **Lock scope prototype = 5 ชนิดไม้**
5. **Honesty ethos** — รายงานตัวเลขจริง + ข้อจำกัด (bamboo caveat, stock-vs-credit) ไม่ oversell
6. **Landing = Tailwind server-component** เท่านั้น (ไม่ 3D/styled-jsx — พังบน prod)
7. **ไม่เก็บข้อมูลไม้ไทยเอง** — ใช้ open dataset (อาจารย์สั่ง 2026-07-15)

---

## 19. Known Issues / Gotchas (บทเรียนที่เจ็บมาแล้ว)

| ปัญหา | สาเหตุ | ทางแก้ |
|---|---|---|
| Web landing unstyled บน prod | styled-jsx ไม่ SSR ใน App Router | ใช้ Tailwind (มี CSS `<link>` จริง) |
| Vercel env var ได้ค่าว่าง | pipe/stdin ไม่ทำงานตอน agent รัน CLI | `vercel env add ... --value "<v>" --no-sensitive --force --yes` |
| uvicorn crash บน Windows | emoji ใน print → cp874 UnicodeEncodeError | เอา emoji ออก / `PYTHONIOENCODING=utf-8` |
| 3D viewer สีเพี้ยน (tan) | three.js sRGB/linear vertex color mismatch | แปลง sRGB→linear ด้วย `THREE.Color` |
| MIDDLEWARE_INVOCATION_FAILED | ขาด `NEXT_PUBLIC_SUPABASE_URL/ANON_KEY` | ตั้ง env + guard ใน middleware |
| .bat เด้งปิดทันที | Thai filename ใน path handoff | ใช้ชื่อไฟล์อังกฤษ + `pause` |
| `ndarray.ptp()` error | ถูกถอดใน numpy 2.x | ใช้ `np.ptp()` |

---

## 20. Roadmap (หลัง Proposal)

1. เทรน species classifier จริง (ResNet-50 → TFLite on-device)
2. เพิ่ม open dataset wood-leaf → ดัน wood IoU สู่ target 0.70
3. Deploy API+worker บน RunPod/Railway (เลิกพึ่ง tunnel)
4. B2B matchmaking module (marketplace)
5. 4D carbon (track ต้นเดียวข้ามปี — re-identification)
6. ขยาย species DB → 50+ ชนิด + TGO certification จริง

---

## 21. Glossary

| Term | ความหมาย |
|---|---|
| **DBH** | Diameter at Breast Height — เส้นผ่านศูนย์กลางลำต้นที่ 1.3 ม. |
| **QSM** | Quantitative Structure Model — โมเดลทรงกระบอกคำนวณปริมาตรไม้ |
| **CHM** | Canopy Height Model |
| **ITD** | Individual Tree Detection |
| **TLS** | Terrestrial Laser Scanning |
| **AGB/BGB** | Above/Below-Ground Biomass |
| **Allometric** | สมการแปลง dimension ต้นไม้ → biomass |
| **IoU** | Intersection over Union (วัดความแม่น segmentation) |
| **TGO** | องค์การบริหารจัดการก๊าซเรือนกระจก |
| **SfM/MVS** | Structure from Motion / Multi-View Stereo (photogrammetry) |
| **CSF** | Cloth Simulation Filter (ground classification) |

---

## 22. Reference Files

- `CLAUDE.md` — working memory (โหลดอัตโนมัติ)
- `docs/ml/PIPELINE.md` — 8 ขั้นละเอียด
- `docs/ml/ALLOMETRIC.md` — สมการ + species DB + references
- `docs/ml/WOODLEAF_RESULTS.md` — ผลทดลอง wood-leaf ทุก variant
- `docs/ml/DATASETS.md` · `docs/ml/FINETUNE_REALDATA.md` — ข้อมูล + วิธี fine-tune
- `docs/superpowers/plans/2026-07-10-async-job-pipeline.md` — spec backend async
- `services/ml/data/species_db.csv` — source of truth ค่า allometric
- `services/api/docs/WORKER_RUNBOOK.md` — วิธีรัน worker
- Memory: `C:\Users\Acer\.claude\projects\D--Project-Carbon\memory\` (MEMORY.md + ไฟล์ย่อย)

---

_จบ Master Spec — ถ้าตัวเลข/สถานะไม่ตรงกับโค้ดปัจจุบัน ให้เชื่อโค้ดและอัปเดตเอกสารนี้_
