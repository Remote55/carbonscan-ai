# CarbonScan AI — Task List

> **Project:** CarbonScan AI — NSC 2026 (หมวด 14 อุดมศึกษา)
> **Deadline ใกล้สุด:** 29 พ.ค. 2569 17:00 น. (ส่ง Proposal)
> **ทีม:** User (Core/Lead), Person A (Web), Person B (Design)

---

## ✅ Just Completed (Repo Scaffold)

- [x] **[User]** Monorepo structure (apps/, services/, packages/, docs/, proposal/, data/, .github/)
- [x] **[User]** Root config: README.md, .gitignore, .editorconfig, LICENSE, CONTRIBUTING.md
- [x] **[User]** Monorepo tooling: package.json, pnpm-workspace.yaml, turbo.json
- [x] **[User]** Core docs (7): ONBOARDING, ARCHITECTURE, ROADMAP, DEVELOPMENT, API, DATA_MODEL, DEPLOYMENT
- [x] **[User]** App/Service READMEs (5): web, mobile, api, ml, packages
- [x] **[User]** Person-specific guide: apps/web/PERSON_A_GUIDE.md
- [x] **[User]** ML docs (3): PIPELINE, ALLOMETRIC, DATASETS
- [x] **[User]** Design docs (2): DESIGN_SYSTEM, BRAND + packages/design-tokens/README
- [x] **[User]** ADRs (6): monorepo, no-iphone-lidar, tech-stack, dual-input, cloud-gpu, team-ownership
- [x] **[User]** Proposal docs (4): README, outline, 5-questions-answers, references
- [x] **[User]** GitHub templates: PR, bug, feature, CODEOWNERS
- [x] **[User]** Setup scripts: setup.sh (mac/linux), setup.ps1 (windows)

> **Total:** 44 markdown files + 7 config files = **51 files** scaffolded

---

## 🔥 PHASE 0: Proposal Sprint (เหลือ ~8 วัน ถึง 29 พ.ค.) — CRITICAL

### Day 1 ✅ (Scaffold + Setup — DONE)
- [x] **[User]** Repo scaffold complete (ดู section ด้านบน)
- [ ] **[All]** ตั้งกลุ่ม Line/Discord สำหรับทีม + Pin แผนนี้ไว้บนสุด
- [ ] **[User]** ลงทะเบียนระบบ SIMs (https://www.nstda.or.th/sims) ทุกคนในทีม
- [ ] **[User]** ติดต่อ ที่ปรึกษา → นัดส่ง Proposal v1 อ่านในวันที่ 23 พ.ค.
- [ ] **[User]** สร้าง GitHub Organization + Repo: `carbonscan-ai` → push scaffold
- [ ] **[Person B]** เริ่ม Brand Direction: Logo concept + Color palette (Forest Green + Sky Blue) — ดู `docs/design/BRAND.md`
- [ ] **[Person A]** Read `apps/web/PERSON_A_GUIDE.md` → Setup Next.js 14 boilerplate ใน `apps/web/`

### Day 2 — 21 พ.ค.
- [ ] **[User]** ร่าง Proposal v1 (8-10 หน้า) — section 1 หลักการและเหตุผล + 2 วัตถุประสงค์
- [ ] **[User]** ร่าง section 3 เทคโนโลยี (Tech Stack ครบ) + section 4 วิธีดำเนินงาน
- [ ] **[Person B]** ออกแบบ Logo draft 3 ตัว ส่งให้ User เลือก
- [ ] **[Person B]** เริ่ม Wireframe Web Dashboard (Mobile + Desktop)
- [ ] **[Person A]** Setup Tailwind + shadcn/ui + Folder structure

### Day 3 — 22 พ.ค.
- [ ] **[User]** Research สูตร TGO Allometric Equation + Wood density 5 ชนิด (สัก, ยางนา, ไผ่, ยางพารา, มะค่าโมง)
- [ ] **[User]** ร่าง section 5 ผลที่คาดว่าจะได้รับ + ตอบ 5 คำถามอาจารย์ในเอกสาร
- [ ] **[Person B]** Logo Final + ส่ง Brand Asset (PNG/SVG) ให้ Person A
- [ ] **[Person A]** Setup Supabase project + Database schema draft

### Day 4 — 23 พ.ค.
- [ ] **[User]** ส่ง Proposal v1 ให้ที่ปรึกษาอ่าน (ทาง LINE/Email)
- [ ] **[Person B]** Layout Cover page + Section dividers + Charts ใน Word
- [ ] **[Person A]** Setup Three.js + React Three Fiber demo scene

### Day 5 — 24 พ.ค.
- [ ] **[User]** แก้ Proposal v2 ตาม feedback ที่ปรึกษา
- [ ] **[User]** Lock Scope ชนิดต้นไม้ Prototype (3-5 ชนิด)
- [ ] **[Person B]** Wireframe Mobile App (Flutter screens)
- [ ] **[Person A]** Implement Landing Page + Routing

### Day 6 — 25 พ.ค. ⚠️ START SIGNATURE PROCESS
- [ ] **[User]** Print Proposal v2 → ส่งให้ที่ปรึกษาเซ็น (ตัวจริง)
- [ ] **[User]** ส่งเอกสารเข้าระบบสถาบัน → ขอลายเซ็นคณบดี/ผอ.
- [ ] **[Person B]** Hi-fidelity Prototype (Figma)
- [ ] **[Person A]** Implement Auth + Dashboard skeleton

### Day 7 — 26 พ.ค. (Buffer Day)
- [ ] **[User]** ตามเรื่องลายเซ็น + เตรียม PDF version
- [ ] **[Person B]** Infographic: Pipeline LiDAR → AI → Carbon
- [ ] **[Person A]** Implement Map (Leaflet basic)

### Day 8 — 27 พ.ค.
- [ ] **[All]** Final check: Proposal + เอกสารแนบ
- [ ] **[User]** แปลง Proposal เป็น PDF (รวมลายเซ็น)
- [ ] **[Person B]** Mockup สำหรับ Pitching (เผื่อ Future)

### Day 9 — 28 พ.ค. ⚠️ UPLOAD DAY
- [ ] **[User]** อัปโหลด Proposal เข้าระบบ SIMs ล่วงหน้า 24 ชม.
- [ ] **[User]** Verify submission status

### Day 10 — 29 พ.ค. DEADLINE
- [ ] **[User]** Final verification ก่อน 17:00 น.
- [ ] **[All]** เฉลิมฉลอง 🎉

---

## 📦 PHASE 1: Foundation (12 มิ.ย. — 30 มิ.ย.) — After Proposal Result

### User (Core/Lead)
- [ ] Setup Python environment (conda) + PyTorch + CUDA + Open3D + laspy + PDAL
- [ ] Setup Google Colab Pro+ account
- [ ] Download NEON LiDAR Dataset (sample plot, ~5GB)
- [ ] Run lidR R workflow บน sample dataset (ทำความเข้าใจ pipeline)
- [ ] Port `classify_ground` (csf algorithm) เป็น Python ด้วย PDAL
- [ ] Port `normalize_height` เป็น Python
- [ ] Port `pitfree` + `grid_canopy` (CHM generation)

### Person A (Web)
- [ ] Setup Vercel deployment + Connect GitHub
- [ ] Implement full Authentication flow (NextAuth + Supabase)
- [ ] Implement Landing Page (final version) + Marketing copy
- [ ] Implement Community Dashboard (user profile, scanned trees list)

### Person B (Design)
- [ ] Finalize Design System ใน Figma (button, card, color tokens)
- [ ] Component Library export → ให้ Person A ใช้
- [ ] Infographic: B2B Flow (โรงงาน → ระบบจับคู่ → ชุมชน)
- [ ] Infographic: Anti-Fraud Mechanism

---

## 🔬 PHASE 2: Core AI Pipeline (1 ก.ค. — 14 ก.ค.)

### User (Core)
- [ ] Implement Watershed Tree Segmentation (Python port from lidR)
- [ ] Setup PointNet++ training pipeline (PyTorch)
- [ ] Fine-tune PointNet++ for Wood-Leaf Segmentation บน NEON
- [ ] Implement TLSeparation as baseline (fallback)
- [ ] Implement QSM (Cylinder Fitting per tree)
- [ ] Implement Allometric Equation calculator (TGO formulas + Wood density DB)
- [ ] Test pipeline end-to-end with sample .las file
- [ ] Optimize for Google Colab T4 (chunking large point clouds)

### User (Backend)
- [ ] Setup FastAPI service skeleton
- [ ] Implement REST endpoints: `/api/upload`, `/api/process`, `/api/results/{id}`
- [ ] WebSocket endpoint for job progress
- [ ] Job Queue setup (Supabase Queues)
- [ ] Setup RunPod Serverless GPU worker (Docker image)
- [ ] Deploy FastAPI to Railway

### Person A
- [ ] Implement File Upload component (.las/.laz with progress bar — tus protocol)
- [ ] Implement 3D Point Cloud Viewer (Three.js + potree-core)
- [ ] Implement Tree detail view (DBH, Height, Volume, Carbon kg/yr)
- [ ] Implement GIS Map (Leaflet + PostGIS API + GPS pins per tree)

### Person B
- [ ] Hi-fidelity Mockup (Flutter Mobile screens — final)
- [ ] App Icon (Android + iOS)
- [ ] Splash screen animation (Lottie)
- [ ] In-app illustrations

---

## 📱 PHASE 3: Mobile App + Submit Final (15 ก.ค. — 17 ก.ค.)

### User (Mobile)
- [ ] Setup Flutter project + Riverpod state management
- [ ] Camera UI (multi-shot, 30-50 frames around tree)
- [ ] GPS capture with 6-decimal precision + EXIF metadata
- [ ] Photo upload to Backend (chunked)
- [ ] Tree Species Classifier on-device (TFLite)
- [ ] Results screen with charts
- [ ] Anti-fraud: Real-time camera lock (no gallery upload)
- [ ] Build APK + sign + test on Android device

### Backend
- [ ] Implement Photogrammetry pipeline (COLMAP wrapper)
- [ ] Add to Job Queue for mobile-uploaded photos
- [ ] Tree Species ID API (RGB image → species)

### Person A
- [ ] Carbon Credit Marketplace UI
- [ ] Report Generator (PDF download per tree/plot)
- [ ] Final QA + Bug fixes
- [ ] Deploy production to Vercel

### Person B
- [ ] Demo Video 3-5 นาที (script + record + edit)
- [ ] Voice-over recording
- [ ] Pitch deck draft (สำหรับรอบนำเสนอ)

### All
- [ ] **17 ก.ค.** ส่งรายงานฉบับสมบูรณ์ในระบบ SIMs (ก่อน 17:00 น.)

---

## 🎤 PHASE 4: Presentation Round (7 ส.ค. — 24 ส.ค.)

- [ ] **7 ส.ค.** ตรวจรายชื่อเข้ารอบนำเสนอ
- [ ] เตรียม Slide Deck final
- [ ] Rehearse pitching (3 รอบขั้นต่ำ)
- [ ] เตรียม Q&A คำตอบ 10 ข้อ
- [ ] เตรียม Backup demo (offline + online)
- [ ] **21 ส.ค.** รอบชิงชนะเลิศ
- [ ] **24 ส.ค.** ประกาศผล

---

## 📊 Status Legend
- [ ] = Not started
- [/] = In progress
- [x] = Completed
- [!] = Blocked (เขียนเหตุผลต่อท้าย)

## 🚨 Open Questions (รอ User ตอบ)
1. ทีม 3 คนชื่ออะไรบ้าง?
2. ที่ปรึกษาโครงการชื่ออะไร? คณะอะไร?
3. มี Template Proposal ของสถาบัน/NSC ฉบับ Word ให้กรอกหรือยัง?
4. งบประมาณที่อยากตั้งใน Proposal เท่าไหร่?
5. ลงทะเบียน SIMs แล้วหรือยัง?
6. ที่ปรึกษามี Background ป่าไม้/CV/AI ฯลฯ?
7. Android phone รุ่นไหนในทีม? (ARCore Depth check)
