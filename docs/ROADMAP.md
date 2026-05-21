# 🗺 Roadmap

> Phased plan from now (20 พ.ค. 2569) to NSC 2026 Final (24 ส.ค. 2569)
>
> **Status:** 🟡 Phase 0 — Proposal Sprint

---

## Phase Overview

| Phase | Window | Goal | Status |
|---|---|---|---|
| **Phase 0** | 20-29 พ.ค. (9 วัน) | ส่ง Proposal สำเร็จ | 🟡 In Progress |
| **Phase 1** | 30 พ.ค. - 30 มิ.ย. | Foundation + Infrastructure | ⚪ Not started |
| **Phase 2** | 1-14 ก.ค. | Core AI Pipeline + Integration | ⚪ Not started |
| **Phase 3** | 15-17 ก.ค. | Mobile App + Final Submission | ⚪ Not started |
| **Phase 4** | 7-21 ส.ค. | Pitching Preparation | ⚪ Not started |
| **Phase 5** | 21 ส.ค. | Final Competition | ⚪ Not started |

---

## 📌 Phase 0 — Proposal Sprint (20-29 พ.ค.)

### Goal
ส่ง Proposal คุณภาพสูง พร้อมลายเซ็นที่ปรึกษา + คณบดี ภายใน 29 พ.ค. 17:00 น.

### Deliverables
- [ ] Proposal Document (8-10 หน้า) Word + PDF
- [ ] ลายเซ็นที่ปรึกษา + หัวหน้าสถาบัน
- [ ] อัปโหลดเข้าระบบ SIMs
- [ ] Logo + Brand Direction
- [ ] Repository setup (folders, docs, README)

### Daily Plan
| Day | Date | Focus |
|---|---|---|
| 1 | 20 พ.ค. (today) | Repo setup, plan kickoff, ตั้งกลุ่ม |
| 2 | 21 พ.ค. | Draft Proposal v1 (User), Logo concept (Person B), Next.js setup (Person A) |
| 3 | 22 พ.ค. | Research TGO equations, Wood density, Allometric (User) |
| 4 | 23 พ.ค. | Send Proposal v1 to advisor for review |
| 5 | 24 พ.ค. | Revise Proposal v2 |
| 6 | 25 พ.ค. | **เริ่มเดินขอลายเซ็น** (CRITICAL) |
| 7 | 26 พ.ค. | Buffer day for signatures |
| 8 | 27 พ.ค. | Final formatting, PDF export |
| 9 | 28 พ.ค. | Upload to SIMs (1 day buffer) |
| 10 | 29 พ.ค. | Verify submission ก่อน 17:00 |

### Success Criteria
- Proposal คุณภาพสูง (เทคนิค + business + impact)
- ตอบ 5 คำถามอาจารย์ครบ
- ไม่มี typo, formatting สวย
- ส่งทันเวลา + มี backup copies

---

## 📌 Phase 1 — Foundation (30 พ.ค. - 30 มิ.ย.)

### Goal
สร้าง infrastructure + ทุก app skeleton + Core ML pipeline (lidR-equivalent)

### User
- [ ] Setup Python environment (services/ml)
- [ ] Download NEON LiDAR dataset (sample plot ~5GB)
- [ ] Run lidR R workflow บน sample data
- [ ] Port `classify_ground` to Python (PDAL/laspy)
- [ ] Port `normalize_height` to Python
- [ ] Port `pitfree CHM` to Python
- [ ] Port `watershed segmentation` to Python
- [ ] **End-to-end:** sample .las → segmented trees (no AI yet)
- [ ] Setup FastAPI skeleton + Supabase project
- [ ] Database schema (PostGIS) — trees, plots, users, jobs

### Person A
- [ ] Setup Next.js 14 production-ready boilerplate
- [ ] Tailwind + shadcn/ui + design tokens integration
- [ ] Authentication flow (NextAuth + Supabase)
- [ ] Landing Page (with marketing copy from Person B)
- [ ] Community Dashboard skeleton
- [ ] B2B Dashboard skeleton
- [ ] Deploy to Vercel + connect domain (carbonscan-ai.app or similar)

### Person B
- [ ] Finalize Brand Identity (Logo, Color, Typography)
- [ ] Design System ใน Figma (export to packages/design-tokens/)
- [ ] Wireframe → Hi-fi prototype (Web + Mobile)
- [ ] Infographics: Pipeline, Allometric, Anti-Fraud
- [ ] Component Library (Figma → React handoff)

### Milestone
🎯 **End of Phase 1:** ทุก app build successfully, basic UI ใช้งานได้, ML pipeline non-AI workflow รัน end-to-end

---

## 📌 Phase 2 — Core AI Pipeline (1-14 ก.ค.)

### Goal
Train AI model สำหรับ Wood-Leaf Segmentation + integrate ทุกอย่างเข้าด้วยกัน

### User (AI)
- [ ] Setup PointNet++ training environment (Colab Pro+)
- [ ] Annotate NEON sample data (wood/leaf labels)
- [ ] Train PointNet++ baseline (target IoU > 0.7)
- [ ] Implement TLSeparation (rule-based fallback)
- [ ] Implement QSM (cylinder fitting per tree)
- [ ] Build Wood Density DB (5 species จาก TGO)
- [ ] Implement Allometric Calculator
- [ ] **End-to-end:** .las → DBH/Height/Volume/Carbon per tree
- [ ] Train Tree Species Classifier (ResNet50 transfer learning)
- [ ] Export to TFLite (for mobile)

### User (Backend)
- [ ] REST API endpoints (`/upload`, `/jobs`, `/trees`, `/marketplace`)
- [ ] WebSocket for job progress
- [ ] Job Queue integration (Supabase Queues)
- [ ] RunPod Serverless GPU Worker (Docker image)
- [ ] Deploy API to Railway

### Person A
- [ ] File Upload component (.las/.laz with progress)
- [ ] **3D Point Cloud Viewer** (Three.js + potree-core) — โชว์ wood/leaf colors
- [ ] GIS Map (Leaflet + PostGIS API + GPS pins)
- [ ] Tree Detail View (DBH, Height, Carbon chart)
- [ ] Connect ทุก endpoint ของ API

### Person B
- [ ] Final design ทุกหน้า (Hi-fi)
- [ ] App Icon (Android + iOS)
- [ ] Lottie animations
- [ ] Illustration assets

### Milestone
🎯 **End of Phase 2:** Upload .las file → ดูผลลัพธ์บน Web ภายใน 5 นาที

---

## 📌 Phase 3 — Mobile App + Final Submission (15-17 ก.ค.)

### Goal
Mobile App ทำงานได้ + ส่งรายงานฉบับสมบูรณ์

### User (Mobile)
- [ ] Flutter project setup + Riverpod state management
- [ ] Camera UI (multi-shot, GPS embedded)
- [ ] Tree Species Classifier on-device (TFLite)
- [ ] Photo upload pipeline (chunked, with retry)
- [ ] Results screen (charts + visualizations)
- [ ] Anti-fraud (camera lock, no gallery upload)
- [ ] Build APK + sign + test
- [ ] (Optional) Build IPA via cloud (Codemagic)

### User (Backend)
- [ ] Photogrammetry Worker (COLMAP/OpenMVS wrapper)
- [ ] Add to Job Queue for mobile uploads
- [ ] Species ID API endpoint (RGB → species)

### Person A
- [ ] Carbon Credit Marketplace (full UI + checkout flow)
- [ ] PDF Report Generator (per tree, per plot)
- [ ] Final QA + bug fixes
- [ ] Production deploy

### Person B
- [ ] **Demo Video** 3-5 minutes (script + record + edit)
- [ ] Voice-over (Thai + English subs)
- [ ] Pitch deck draft (สำหรับนำเสนอ)

### Milestone
🎯 **17 ก.ค. 17:00:** ส่งรายงานฉบับสมบูรณ์ในระบบ SIMs

---

## 📌 Phase 4 — Pitching Preparation (7-20 ส.ค.)

### Goal
เตรียมการนำเสนอ + ซ้อมจน fluent

### Activities
- [ ] **7 ส.ค.** ตรวจรายชื่อเข้ารอบนำเสนอ
- [ ] Pitch deck (final version) — 8-10 slides
- [ ] Demo script ภาษาไทย + รั้งภาษาอังกฤษไว้ใช้
- [ ] Q&A preparation (10+ คำถามคาดการณ์)
- [ ] Rehearse pitching (3+ รอบขั้นต่ำ, ถ่ายวิดีโอตัวเอง)
- [ ] Test demo บน WiFi โรงงาน/มือถือ (เผื่อ internet พัง)
- [ ] Offline backup demo (downloaded videos)

### Optional Polish
- [ ] Poster A1 (สำหรับ booth ในรอบชิง)
- [ ] Booklet/Brochure แจกกรรมการ
- [ ] Social media announcement (Facebook, Twitter/X)

---

## 📌 Phase 5 — Final Competition (21 ส.ค.)

### Day-of Checklist
- [ ] นอนเต็มอิ่ม 8 ชั่วโมง
- [ ] เตรียม Laptop + Hotspot สำรอง
- [ ] เตรียม Phone ที่มี Flutter App pre-installed
- [ ] Demo Backup (USB + Cloud)
- [ ] Pitch deck on multiple devices
- [ ] เสื้อผ้าสุภาพ (ของทีม + อาจารย์)
- [ ] เอกสารแนบ (Proposal printed + นามบัตร)

### Result
🏆 **24 ส.ค. 2569** — ประกาศผลรอบชิงชนะเลิศ

---

## 🎯 Long-Term Vision (Post-NSC)

ไม่อยู่ใน scope การแข่ง แต่เป็นทิศทางที่อาจขยายต่อ:

- **Q4 2569:** ขอทุน Startup จาก NIA / Depa
- **Q1 2570:** Pilot กับ ม.เกษตร หรือ ม.อ. สำหรับการประเมินป่าจริง
- **Q2 2570:** ขอ Certificate จาก TGO
- **Q3 2570:** Open Source release (ดึง community contributors)
- **Q4 2570:** Pivot เป็น Climate FinTech Startup เต็มตัว

---

## 🚨 Critical Path

งานที่หากไม่เสร็จ → blocking ทั้งทีม:

1. **Proposal (29 พ.ค.)** — ถ้าไม่ส่ง = จบเกมส์
2. **ML Pipeline end-to-end (มิ.ย.)** — Web ต้องใช้
3. **API endpoints (เริ่ม ก.ค.)** — Mobile/Web ใช้
4. **Demo Video (16 ก.ค.)** — รอบ pitching ใช้

**Owner สำหรับ Critical Path:** User (ส่วนใหญ่)

---

## 📊 Phase Risk Register

| Phase | Top Risk | Mitigation |
|---|---|---|
| 0 | ลายเซ็นช้า | เริ่มเดิน 25 พ.ค., มี PDF preview |
| 1 | ML port lidR ไม่เป็น | ใช้ R script ก่อน, port เป็น Python ทีหลัง |
| 2 | PointNet++ Train ไม่ได้ผล | Fallback TLSeparation |
| 3 | iOS build ไม่ได้ | ใช้ Codemagic / ทำแค่ Android demo |
| 4 | กรรมการถามนอกเรื่อง | Q&A prep ครอบคลุม + ตอบ "ดี" ที่ขอบเขต |

---

📖 **See:**
- [TASKS.md](../TASKS.md) — Daily tasks
- [docs/decisions/](decisions/) — Why we chose this path
- [docs/DEVELOPMENT.md](DEVELOPMENT.md) — How to setup dev env
