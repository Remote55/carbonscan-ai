# บท 18 — เครื่องมือ + ฮาร์ดแวร์ที่ใช้ในการพัฒนา

> 🎯 **เป้าหมาย:** รู้จัก hardware/software ทุกอย่างที่ใช้ — ทั้ง dev tools และ deployment infra
> 📚 **พื้นฐาน:** [บท 03 — Architecture](03-architecture.md)
> ⏱️ **เวลา:** ~20 นาที

---

## 1. Dev Hardware (เครื่องที่ทีมใช้)

### 1.1 Minimum Specs

| Component | Min | Recommended |
|---|---|---|
| **CPU** | 4-core | 8-core (i7/Ryzen 7) |
| **RAM** | 16 GB | 32 GB |
| **Storage** | 256 GB SSD | 512 GB SSD |
| **GPU** | Integrated | NVIDIA RTX 3060+ (สำหรับ ML local) |
| **OS** | Windows 10+ / macOS / Linux | Windows 11 หรือ macOS |

### 1.2 ที่ทีมใช้จริง

- User: Windows 11, 32 GB RAM, RTX 3060 (สำหรับ ML training)
- Person A: ใดๆ ที่รัน Next.js dev server ได้ (8 GB+ พอ)
- Person B: macOS หรือ Windows ใดๆ (สำหรับ Figma)

---

## 2. LiDAR Scanners (Production Equipment)

### 2.1 TLS (Terrestrial Laser Scanning)

| Brand / Model | Range | Accuracy | ราคา (THB) |
|---|---|---|---|
| **Leica BLK360** | 60 m | ±4 mm | ~1.5M |
| **FARO Focus M70** | 70 m | ±2 mm | ~1.8M |
| **RIEGL VZ-1000** | 1,400 m | ±5 mm | ~3.5M |
| **Trimble TX8** | 340 m | ±2 mm | ~3M |

**Use case:** ตรวจสอบ research-grade, แปลงเล็ก-กลาง (1-10 ไร่/scan)

### 2.2 UAV LiDAR (Drone)

| Brand / Model | Sensor | Coverage | ราคา (THB) |
|---|---|---|---|
| **DJI Matrice 350 + Zenmuse L2** | Livox LiDAR | 10-100 ha/flight | ~1.5M |
| **DJI Matrice 300 + Zenmuse L1** | Livox LiDAR | 10-100 ha/flight | ~1M |
| **Yellowscan Mapper+** | Hesai LiDAR | 50-200 ha/flight | ~2.5M |

**Use case:** Scan ป่าใหญ่, plantation, area-wide survey

### 2.3 Mobile LiDAR

| Brand / Model | Mount | ราคา (THB) |
|---|---|---|
| **iPhone Pro (12/13/14/15)** | In-built | ~30K-60K (มือถือ) |
| **Leica BLK2GO** | Handheld | ~1.5M |

**Use case:** iPhone — short range (5m), good for indoor/single object
**Note:** ⚠️ **ADR-0002:** เราไม่ทำ iPhone LiDAR app (ดู [บท 03](03-architecture.md))

### 2.4 ทำไมระบบเรารองรับ LiDAR หลายแบบ

- Auditor บางคนมี TLS, บางคนมี Drone — ระบบ accept ทั้ง 2
- ไฟล์ output มาตรฐานเดียวกัน (`.las` หรือ `.laz`)

---

## 3. Cloud Infrastructure

### 3.1 Web Hosting — Vercel

| Plan | Cost | Limit |
|---|---|---|
| **Hobby** (เราใช้) | Free | 100 GB bandwidth, 6000 build min/mo |
| Pro | $20/mo | 1 TB, unlimited |

**Features:**
- Auto-deploy from GitHub
- Preview deployments per PR
- Edge functions
- Vercel Analytics (free for Hobby)

### 3.2 API Hosting — Railway

| Plan | Cost | Limit |
|---|---|---|
| **Hobby** (เราใช้) | $5/mo | 500 hr execution, 1 GB RAM |
| Developer | $20/mo | unlimited execution |

**Features:**
- Docker-based deploy
- Auto-scale (limited on Hobby)
- Easy env var management

### 3.3 Database + Storage — Supabase

| Plan | Cost | Limit |
|---|---|---|
| **Free** (เราใช้) | Free | 500 MB DB, 1 GB Storage |
| Pro | $25/mo | 8 GB DB, 100 GB Storage |

**Features:**
- PostgreSQL 16 with PostGIS
- Storage (S3-compatible)
- Auth (email + OAuth)
- Row-Level Security (RLS)
- Real-time subscriptions

### 3.4 GPU Compute — RunPod Serverless

| GPU | Cost / hour | Use |
|---|---|---|
| **RTX 3090** (24GB) | $0.34 | Wood-leaf inference |
| **A10G** (24GB) | $0.39 | Pipeline production |
| **RTX 4090** (24GB) | $0.69 | Heavy training |
| **A100** (40GB) | $1.89 | PointNet++ training |

**Why Serverless:**
- ✅ Pay per second (scale to zero)
- ✅ No idle cost
- ✅ Docker container support
- ✅ Auto-scale on queue depth

**Budget estimate:**
- NSC phase: ~100 hours GPU × $0.39 = **$39/mo**
- Production: ~$200-500/mo

### 3.5 Domain + DNS — Cloudflare

| Service | Cost |
|---|---|
| Domain (e.g., `.app`, `.co.th`) | $10-30/year |
| DNS | Free |
| CDN | Free |

---

## 4. Total Monthly Cost — NSC Submission Phase

| Item | Cost (USD/mo) |
|---|---|
| Vercel Hobby | $0 |
| Railway Hobby | $5 |
| Supabase Free | $0 |
| RunPod GPU (~100 hr) | $39 |
| Sentry Developer | $0 |
| Domain | $1 (amortized) |
| **Total** | **~$45/mo** |

> 💡 ตลอด NSC 2 เดือน ≈ $90 = ฿3,200 — ครอบคลุมด้วยเงินสนับสนุนจาก NSC

---

## 5. Development Tools (Software)

### 5.1 Code Editors

| Tool | Purpose |
|---|---|
| **VS Code** (recommended) | Main editor — extensions: Python, Pylance, Dart, Tailwind, GitLens |
| **Android Studio** | Flutter Android dev + emulator |
| **DBeaver** | DB browser (free) |

### 5.2 Version Control

| Tool | Purpose |
|---|---|
| **Git** | Source control |
| **GitHub** | Remote hosting + PR + CI |
| **gh CLI** | GitHub CLI (faster than web UI) |

### 5.3 Languages / Runtimes

| Runtime | Version |
|---|---|
| **Python** | 3.11 (ML, API) |
| **Node.js** | 20 LTS (Web) |
| **Dart/Flutter** | 3.44 / 3.12 |
| **PostgreSQL** | 16 (via Supabase) |

### 5.4 Container / Tools

| Tool | Purpose |
|---|---|
| **Docker Desktop** | Container build/run |
| **pnpm** | Web package manager |
| **poetry** | Python dependency mgmt |
| **CloudCompare** (free) | View point clouds |
| **MeshLab** (free) | 3D model editor |

### 5.5 Design

| Tool | Purpose |
|---|---|
| **Figma** | UI/UX design (Person B) |
| **Excalidraw** | Diagrams |
| **Mermaid** | Code-based diagrams |

### 5.6 Communication

| Tool | Purpose |
|---|---|
| **Discord / Line** | Daily team sync |
| **Notion / Google Docs** | Shared notes |
| **GitHub Issues** | Task tracking |

---

## 6. ML Stack

### 6.1 Python Libraries (Production)

| Library | Purpose |
|---|---|
| **NumPy** | Array math |
| **SciPy** | KD-tree, sparse, signal |
| **scikit-image** | Image processing (CHM, watershed) |
| **scikit-learn** | Classical ML (clustering) |
| **Open3D** | 3D point cloud ops |
| **laspy** | LAS/LAZ I/O |
| **PDAL** | Point cloud filters (CSF, etc.) |
| **PyTorch** | Deep Learning (Phase 2) |
| **PyTorch Geometric** | Point cloud DL (Phase 2) |

### 6.2 Training Tools (Phase 2)

| Tool | Purpose |
|---|---|
| **Jupyter Notebook** | Training experiments |
| **Weights & Biases** | Experiment tracking |
| **Google Colab Pro+** | Cloud GPU for training (~$50/mo) |
| **CloudCompare** | Manual annotation |

---

## 7. Monitoring + Observability

| Tool | Purpose |
|---|---|
| **Sentry** | Error tracking (Web, Mobile, API) |
| **Vercel Analytics** | Web performance |
| **Supabase Logs** | Database query monitoring |
| **GitHub Actions** | CI/CD logs |

---

## 8. ❓ คำถามตรวจสอบความเข้าใจ

1. **TLS vs UAV LiDAR — เลือกใช้ตอนไหน?**
2. **RunPod Serverless ดียังไง vs self-host GPU?**
3. **Supabase Free tier มี limit อะไร? พอสำหรับ NSC ไหม?**
4. **ทีมใช้งบ Cloud ประมาณเท่าไหร่ตลอด NSC?**
5. **VS Code extensions ที่จำเป็นสำหรับโปรเจกต์นี้คืออะไร?**

---

## 9. อ่านต่อ

- [บท 19 — DevOps / CI / CD](19-devops-cicd.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
