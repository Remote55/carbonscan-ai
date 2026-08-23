# CarbonScan AI — Task List

> [!CAUTION]
> **Historical — the plan this tracked ended on 23 August 2026.** ทุก phase ในไฟล์นี้
> สร้างรอบไทม์ไลน์ NSC 2026 ซึ่ง**ไม่ผ่าน** และทีมสามคนที่ตอนนี้เหลือคนเดียว
> Phase 3 เป็นงาน Flutter ที่ถูกลบทิ้งไปแล้วตาม [ADR 0007](docs/decisions/0007-drop-the-photo-path.md)
>
> เก็บไว้เพื่อ trace ว่าอะไรถูกวางแผนและอะไรทำจริง — **ห้ามใช้เป็นรายการงานปัจจุบัน**
> งานที่ทำอยู่จริงดูที่หัวข้อ "งานถัดไป" ใน [`README.md`](README.md)

**บริบทเดิม ณ เวลาที่เขียน:**

> **Project:** CarbonScan AI — NSC 2026 (หมวด 14 อุดมศึกษา)
> **Deadline ใกล้สุด:** 29 พ.ค. 2569 17:00 น. — **เหลือ 7 วัน**
> **ทีม:** User (Core/Lead), Person A (Web), Person B (Design)

---

## 📊 Progress Snapshot

| Phase | Status | Completion |
|---|---|---|
| **Phase 0 — Proposal Sprint** (20-29 พ.ค.) | 🟡 In progress | 60% — เหลือ User actions |
| **Phase 1 — Foundation** (12-30 มิ.ย.) | 🟢 Ahead of schedule | 50% — scaffold done in Phase 0 |
| **Phase 2 — Core AI** (1-14 ก.ค.) | ⚪ Not started | 0% (allometric core ทำแล้ว 1/8 steps) |
| **Phase 3 — Mobile + Submit** (15-17 ก.ค.) | ⚪ Not started | 0% (mobile scaffold done) |
| **Phase 4 — Pitching** (7-21 ส.ค.) | ⚪ Not started | 0% |

---

## ✅ Completed (5 PRs Merged — 2026-05-20 → 22)

### Infrastructure (PRs #1-2)
- [x] Monorepo scaffold (54 files, 12,481 lines) — apps/, services/, packages/, docs/, proposal/, .github/
- [x] Root config: README, .gitignore, .editorconfig, LICENSE, CONTRIBUTING, package.json, pnpm-workspace, turbo.json
- [x] Documentation hub (15 files): ONBOARDING, ARCHITECTURE, ROADMAP, DEVELOPMENT, API, DATA_MODEL, DEPLOYMENT, SUPABASE_SETUP
- [x] ADRs (6): monorepo, no-iphone-lidar, tech-stack, dual-input, cloud-gpu, team-ownership
- [x] App/Service READMEs + PERSON_A_GUIDE
- [x] GitHub: PR template, bug/feature issue templates, CODEOWNERS, branch protection (linear history, no force push, code-owner reviews)
- [x] 5 CI Workflows: Web (Vitest+Build), API (Ruff+Pytest+PostGIS), ML (Pytest+coverage), Mobile (analyze+test), CodeQL
- [x] Setup scripts (setup.sh + setup.ps1)
- [x] **GitHub repo published**: https://github.com/Remote55/carbonscan-ai

### Web (PR #1 → integrated with PR #4)
- [x] Next.js 14 boilerplate (TypeScript, Tailwind, shadcn/ui-ready, Three.js + Leaflet + Supabase deps)
- [x] Landing page (hero + features + stats + footer with team logo)
- [x] Tailwind config with forest/sky brand palette + shadcn CSS vars
- [x] Layout.tsx with 4 Google Fonts + SEO + OG/Twitter metadata
- [x] cn() helper + formatCarbon/formatTHB/formatGPS utils
- [x] API client (typed fetch wrapper + ApiError + upload helper)
- [x] Supabase browser client

### Mobile (PR #1 + PR #5 prep)
- [x] Flutter 3.22+ scaffold (22 files)
- [x] Riverpod + go_router + Material 3 with brand theme
- [x] Core: AppConfig (dart-define env), routes, theme, Dio client, permissions helper
- [x] 5 screens: Home, TreeScan checklist, Camera multi-shot, Results pipeline, SpeciesClassifier stub
- [x] AppButton widget + 2 widget smoke tests
- [x] **NEW**: `.env.example` + `scripts/run-dev.sh`/`.ps1` helpers (read .env → dart-defines)

### Backend (PR #5)
- [x] FastAPI 0.111 + async SQLAlchemy 2.0 + GeoAlchemy2
- [x] JWT auth + bcrypt + 8 typed exceptions
- [x] V1 endpoint stubs (auth, upload, jobs, trees, health)
- [x] ORM models (User, Tree with PostGIS POINT)
- [x] Pydantic schemas (GpsPoint validation)
- [x] **NEW**: Alembic initial migration — 6 tables + indexes + triggers ready
- [x] **NEW**: `setup_supabase.sql` (extensions) + `seed_species_db.sql` (5 species)

### ML (PRs #3 + #5)
- [x] PyTorch + Open3D + laspy + COLMAP scaffold (8-step pipeline structure)
- [x] **Allometric calculator FULLY IMPLEMENTED** — 16/16 pytest passing locally
- [x] species_db.csv (5 species verified against literature)
- [x] Worked example verified: ไม้สัก DBH=30/H=18 = 1.233 tCO₂eq
- [x] 5-species comparison table in ALLOMETRIC.md
- [x] RunPod handler stub + COLMAP/OpenMVS wrappers

### Design (PR #4)
- [x] Official team logo v1.0 (illustrated tree + hands + CO₂ + analytics)
- [x] Wired up to Web (favicon, OG image, header, footer)
- [x] BRAND.md updated with official concept + element breakdown
- [x] assets/brand/README.md (usage rules, do/don't, changelog)

### Proposal (PRs #1 + #3)
- [x] outline.md expanded to 8-10 page document with all sections
- [x] 5-questions-answers.md ready to paste into Proposal
- [x] references.md with 20+ academic citations

---

## 🔥 PHASE 0: Proposal Sprint — Remaining 7 Days

### 🔴 CRITICAL Path (User Actions Required)

| Days | Owner | Task | Status |
|---|---|---|---|
| **22 พ.ค. (TODAY)** | User | Copy `proposal/outline.md` → Word template + format | [ ] |
| **22 พ.ค.** | User | ติดต่อที่ปรึกษา → นัดส่ง Proposal v1 อ่าน 23-24 พ.ค. | [ ] |
| **22 พ.ค.** | User | ลงทะเบียน SIMs (https://www.nstda.or.th/sims) | [ ] |
| **23 พ.ค.** | User | ส่ง Proposal v1 ให้ที่ปรึกษา (Line/Email) | [ ] |
| **23-24 พ.ค.** | All | ตั้งกลุ่ม Line/Discord ทีม + share repo + roles | [ ] |
| **24 พ.ค.** | User | แก้ Proposal v2 ตาม feedback ที่ปรึกษา | [ ] |
| **24 พ.ค.** | User | Lock ชนิดต้นไม้ Prototype (5 ชนิด — ตามที่อยู่ใน species_db.csv) | [x] ✓ ทำแล้ว |
| **25 พ.ค.** ⚠️ | User | **เริ่มเดินขอลายเซ็น** ที่ปรึกษา (จริง) | [ ] |
| **25 พ.ค.** | User | ส่งเอกสารเข้าระบบสถาบัน → ขอลายเซ็นคณบดี/ผอ. | [ ] |
| **26 พ.ค.** | User | Buffer day — ตามเรื่องลายเซ็น | [ ] |
| **27 พ.ค.** | All | Final check Proposal + เอกสารแนบ | [ ] |
| **27 พ.ค.** | User | แปลง Proposal → PDF (รวมลายเซ็น) | [ ] |
| **28 พ.ค.** ⚠️ | User | อัปโหลดเข้า SIMs (1 day buffer) | [ ] |
| **29 พ.ค. < 17:00** | User | Verify submission status | [ ] |

### 🟠 Person B Tasks (Parallel, ใน Phase 0)

- [ ] **[Person B]** Layout Cover Page (ใช้ logo + project title)
- [ ] **[Person B]** Section dividers + Page numbers
- [ ] **[Person B]** Architecture diagram (1200×800 PNG)
- [ ] **[Person B]** Infographic: Pipeline LiDAR → AI → Carbon (สำหรับ section 6)
- [ ] **[Person B]** Infographic: Anti-Fraud Mechanism (4 layers)

### 🟡 Person A Tasks (Parallel — ไม่ block Proposal)

- [x] Setup Next.js 14 boilerplate ✓
- [x] Tailwind + shadcn/ui ✓
- [ ] **[Person A]** Run `pnpm dev` → verify localhost:3000 ทำงาน
- [ ] **[Person A]** Implement Login page UI (no auth backend yet)
- [ ] **[Person A]** Read PERSON_A_GUIDE.md ทั้งหมด

### 🚀 Optional User Tasks (Phase 1 head-start)

- [ ] **O — Setup Supabase project จริง** (15 min, ดู `docs/SUPABASE_SETUP.md`)
- [ ] **R — Generate favicons multi-res จาก logo.png** (10 min, realfavicongenerator.net)
- [ ] **S — Setup Vercel deploy preview** (20 min)

---

## 📦 PHASE 1: Foundation (12 มิ.ย. — 30 มิ.ย.) — After Proposal Result

### User — ML / Backend (mostly done!)

- [x] FastAPI service scaffold ✓ (PR #5)
- [x] Alembic schema migration ✓ (PR #5)
- [x] Allometric calculator + 16 tests ✓ (PRs #3, #5)
- [ ] **[User]** Setup local Postgres + PostGIS for offline dev (Docker)
- [ ] **[User]** Download NEON LiDAR sample dataset (~5GB) — see `services/ml/scripts/download_neon.py`
- [ ] **[User]** Implement `classify_ground` (PDAL CSF) — Phase 2 step 1
- [ ] **[User]** Implement `normalize_height` — Phase 2 step 2
- [ ] **[User]** Implement `pitfree CHM` — Phase 2 step 3
- [ ] **[User]** Implement `watershed segmentation` — Phase 2 step 4
- [ ] **[User]** Get Google Colab Pro+ subscription (for PointNet++ training)
- [ ] **[User]** Run lidR R workflow on sample (understand reference impl)

### Person A — Web

- [ ] Setup Vercel deployment + connect GitHub
- [ ] Implement Authentication flow (NextAuth + Supabase) — depends on User finishing Supabase setup
- [ ] Implement Community Dashboard (user profile, scanned trees list)
- [ ] Implement Industrial Dashboard

### Person B — Design

- [ ] Finalize Design System ใน Figma (button, card, dialog variants)
- [ ] Design Token export — push tokens เป็น JSON ใน `packages/design-tokens/tokens/`
- [ ] Wireframe Mobile App final
- [ ] Infographics for marketing
- [ ] Logo variants: SVG version, monochrome, reversed, wordmark, mark-only (see assets/brand/README.md TODO)

---

## 🔬 PHASE 2: Core AI Pipeline (1 ก.ค. — 14 ก.ค.)

### User (Core ML)
- [ ] Setup PointNet++ training pipeline (PyTorch + Open3D-ML)
- [ ] Fine-tune Wood-Leaf Segmentation บน NEON (target IoU ≥ 0.70)
- [ ] Implement TLSeparation as baseline (fallback)
- [ ] Implement QSM (Cylinder Fitting per tree)
- [ ] Test pipeline end-to-end with sample .las file
- [ ] Optimize for Colab T4 (chunking large point clouds)

### User (Backend Integration)
- [ ] Implement `/upload/las` endpoint (chunked upload to Supabase Storage)
- [ ] Implement `/upload/photos` endpoint
- [ ] Implement `/jobs/{id}` status endpoint
- [ ] WebSocket `/ws/jobs` for real-time progress
- [ ] Job Queue setup (Supabase Queues or Redis)
- [ ] Build RunPod Serverless Docker image (services/ml/Dockerfile.gpu)
- [ ] Deploy FastAPI to Railway

### Person A (Web Core Features)
- [ ] File Upload component (.las/.laz with progress bar — tus protocol)
- [ ] **3D Point Cloud Viewer** (Three.js + potree-core + R3F) — Wow feature
- [ ] Tree detail view (DBH, Height, Volume, Carbon chart)
- [ ] GIS Map (Leaflet + PostGIS API + GPS pins)

### Person B (Design — Mobile)
- [ ] Hi-fidelity Mobile mockups (Flutter screens — final)
- [ ] App Icon (1024×1024 PNG)
- [ ] Splash screen animation (Lottie)

---

## 📱 PHASE 3: Mobile App + Submit Final (15 ก.ค. — 17 ก.ค.)

### User (Mobile)
- [x] Flutter scaffold ✓ (PR #1, prep with PR #5)
- [ ] Install Flutter SDK + Android Studio locally
- [ ] `flutter create . --platforms=android --org=com.carbonscan`
- [ ] `flutter pub get` + `flutter run` (verify boots)
- [ ] Implement Camera UI (multi-shot, GPS embedded)
- [ ] Implement Photo upload pipeline (chunked, with retry)
- [ ] Tree Species Classifier on-device (TFLite — needs trained model from Phase 2)
- [ ] Results screen with charts
- [ ] Anti-fraud: Real-time camera lock (no gallery upload)
- [ ] Build signed APK + test on real Android device

### User (Backend — Photogrammetry)
- [ ] COLMAP wrapper (services/ml/photogrammetry/colmap_wrapper.py)
- [ ] OpenMVS wrapper (services/ml/photogrammetry/openmvs_wrapper.py)
- [ ] Job chain: photogrammetry → pipeline (auto-trigger second job)

### Person A (Web Final)
- [ ] Carbon Credit Marketplace UI (listings + checkout)
- [ ] Report Generator (PDF per tree/plot, react-pdf)
- [ ] Final QA + bug fixes
- [ ] Deploy production to Vercel

### Person B (Pitching Prep)
- [ ] Demo Video 3-5 นาที (script + record + edit)
- [ ] Voice-over recording (Thai + English subs)
- [ ] Pitch deck draft

### All
- [ ] **17 ก.ค. < 17:00** — ส่งรายงานฉบับสมบูรณ์ใน SIMs

---

## 🎤 PHASE 4: Presentation Round (7 ส.ค. — 24 ส.ค.)

- [ ] **7 ส.ค.** ตรวจรายชื่อเข้ารอบนำเสนอ
- [ ] เตรียม Slide Deck final (8-10 slides)
- [ ] Rehearse pitching (3+ รอบ, ถ่ายวิดีโอตัวเอง)
- [ ] เตรียม Q&A คำตอบ 10 ข้อ
- [ ] เตรียม Backup demo (offline videos + cached data)
- [ ] เตรียม Poster A1 + นามบัตร
- [ ] **21 ส.ค.** รอบชิงชนะเลิศ
- [ ] **24 ส.ค.** 🏆 ประกาศผล

---

## 📊 Status Legend
- [ ] = Not started
- [/] = In progress
- [x] = Completed
- [!] = Blocked (เขียนเหตุผลต่อท้าย)

---

## 🚨 Open Questions (รอ User ตอบ — สำคัญสำหรับ Proposal)

1. **ทีม 3 คนชื่ออะไรบ้าง?** (ใส่ใน Proposal cover + section 1)
2. **ที่ปรึกษาโครงการชื่ออะไร? คณะอะไร? ตำแหน่งวิชาการ?**
3. **มี Template Proposal ของสถาบัน/NSC ฉบับ Word ให้กรอกหรือยัง?**
4. **งบประมาณที่อยากตั้งใน Proposal เท่าไหร่?** (NSC สนับสนุน ~3,000-5,000 บาท/โครงการ)
5. **ลงทะเบียน SIMs แล้วหรือยัง?**
6. **ที่ปรึกษามี Background ป่าไม้/CV/AI/อะไร?** (เพื่อปรับ technical depth)
7. **Android phone รุ่นไหนในทีม?** (ARCore Depth check สำหรับ Phase 3)
