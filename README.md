# 🌲 CarbonScan AI

> **NSC 2026 หมวด 14 อุดมศึกษา** — Sustainable Innovation Track
>
> แพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้อัจฉริยะ ด้วย LiDAR Point Cloud + AI Wood-Leaf Segmentation + B2B Carbon Offset Matchmaking

[![Status](https://img.shields.io/badge/status-development-orange)]()
[![NSC 2026](https://img.shields.io/badge/NSC-2026-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## ⚡ TL;DR

**ปัญหา:** การประเมินคาร์บอนเครดิตในป่าไม้ของไทย ต้นทุน Auditor ระดับ ฿100,000/แปลง → ชุมชนเข้าไม่ถึง, โรงงาน CSR ตรวจสอบไม่ได้

**ทางออก:** Cloud Platform รับข้อมูล LiDAR Point Cloud (จาก Auditor หรือ Photogrammetry ภาพมือถือ) → AI แยกใบ/ลำต้น → คำนวณ Carbon ด้วยสมการ TGO → แสดงผลบน Web Dashboard + Mobile App

**ผลลัพธ์:** ลดต้นทุน 100×, โปร่งใส 100%, ตรวจสอบได้ผ่าน 3D Viewer + GPS

---

## 🚀 Quick Start

### สำหรับคนใหม่ที่เพิ่งมาทีม
👉 อ่าน **[docs/ONBOARDING.md](docs/ONBOARDING.md)** ก่อนเลย (30 นาที)

### สำหรับ Developer
```bash
# Clone
git clone https://github.com/<org>/carbonscan-ai.git
cd carbonscan-ai

# Setup (รวมทุก app/service)
./scripts/setup.sh    # macOS/Linux
./scripts/setup.ps1   # Windows

# Run Web Dashboard
cd apps/web && pnpm dev

# Run Backend API
cd services/api && uvicorn app.main:app --reload

# Run Mobile App
cd apps/mobile && flutter run
```

---

## 📂 Repository Structure

```
carbonscan-ai/
├── apps/
│   ├── web/          → Next.js 14 Web Dashboard  [Person A]
│   └── mobile/       → Flutter Mobile App        [User]
├── services/
│   ├── api/          → FastAPI Backend           [User]
│   └── ml/           → AI/ML Pipeline (PyTorch)  [User]
├── packages/
│   ├── design-tokens/ → Brand tokens             [Person B]
│   ├── ui/           → Shared React components
│   └── types/        → Shared TypeScript types
├── docs/             → All documentation
├── proposal/         → NSC 2026 Proposal docs
├── data/             → Sample datasets
└── scripts/          → Helper scripts
```

ดูรายละเอียดทุกโฟลเดอร์: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**

---

## 👥 Team & Ownership

| Owner | Role | Primary Folders |
|---|---|---|
| **User** | Lead / AI / Mobile / Backend | `apps/mobile/`, `services/api/`, `services/ml/`, `proposal/` |
| **Person A** | Frontend / Web Engineer | `apps/web/`, `packages/ui/`, `packages/types/` |
| **Person B** | UI/UX Designer / Content | `packages/design-tokens/`, `assets/brand/`, `docs/design/` |

ดูแบ่งงานละเอียด: **[docs/decisions/0006-team-ownership.md](docs/decisions/0006-team-ownership.md)**

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Web** | Next.js 14, TypeScript, Tailwind, shadcn/ui, Three.js (R3F), Leaflet |
| **Mobile** | Flutter 3.x, Riverpod, TFLite, Dio |
| **Backend** | FastAPI (Python 3.11), Pydantic, SQLAlchemy, Celery |
| **Database** | PostgreSQL 16 + PostGIS (via Supabase) |
| **AI/ML** | PyTorch, PointNet++, Open3D, laspy, PDAL, COLMAP, OpenMVS |
| **Storage** | Supabase Storage (S3-compatible) |
| **Queue** | Supabase Queues / Redis |
| **Cloud GPU** | RunPod Serverless (A10G/RTX 4090) |
| **Deploy** | Vercel (Web), Railway (API), RunPod (ML Worker) |
| **DevOps** | pnpm workspaces, Turborepo, Docker, GitHub Actions |

เหตุผลการเลือก: **[docs/decisions/0003-tech-stack-selection.md](docs/decisions/0003-tech-stack-selection.md)**

---

## 📅 Timeline (NSC 2026)

| Date | Milestone |
|---|---|
| **29 พ.ค. 2569 17:00** | 🔴 ส่ง Proposal ใน SIMs (CRITICAL) |
| **12 มิ.ย. 2569** | ประกาศผลรอบ Proposal |
| **17 ก.ค. 2569 17:00** | ส่งงานฉบับสมบูรณ์ |
| **21 ส.ค. 2569** | รอบชิงชนะเลิศ |
| **24 ส.ค. 2569** | 🏆 ประกาศผล |

แผนรายละเอียด: **[docs/ROADMAP.md](docs/ROADMAP.md)** | งานรายวัน: **[TASKS.md](TASKS.md)**

---

## 📚 Documentation Map

| Document | For Whom | Purpose |
|---|---|---|
| [README.md](README.md) | ทุกคน | Entry point (ไฟล์นี้) |
| [docs/ONBOARDING.md](docs/ONBOARDING.md) | คนใหม่ | จุดเริ่มต้น 30 นาที |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Developer | System design |
| [docs/ROADMAP.md](docs/ROADMAP.md) | ทุกคน | แผนงาน phases |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Developer | Workflow, Git, PR |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | DevOps | Deployment guide |
| [docs/API.md](docs/API.md) | Backend/Frontend | API reference |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Backend | DB schema |
| [docs/ml/PIPELINE.md](docs/ml/PIPELINE.md) | ML Engineer | ML pipeline |
| [docs/ml/ALLOMETRIC.md](docs/ml/ALLOMETRIC.md) | ML Engineer | TGO equations |
| [docs/design/DESIGN_SYSTEM.md](docs/design/DESIGN_SYSTEM.md) | Designer/Frontend | Design system |
| [docs/decisions/](docs/decisions/) | ทุกคน | ADRs (Architecture Decision Records) |
| [proposal/](proposal/) | User | NSC Proposal documents |
| [TASKS.md](TASKS.md) | ทุกคน | Task list daily |
| [CLAUDE.md](CLAUDE.md) | AI assistant | Working memory |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributor | วิธี contribute |

---

## 📜 License

MIT License — see [LICENSE](LICENSE)

## 🙏 Acknowledgments

- **lidR R package** (Jean-Romain Roussel) for tree segmentation methodology
- **NEON Science** for open LiDAR datasets
- **TGO (องค์การบริหารจัดการก๊าซเรือนกระจก)** for allometric standards
- **NSC 2026 / สวทช.** for hosting the competition

---

**Status:** 🟡 Pre-development (Proposal phase) | **Target:** 🥇 NSC 2026 Championship
