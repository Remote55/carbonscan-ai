# CarbonScan AI — Working Memory

> โหลดเข้า context อัตโนมัติทุกครั้งที่เปิด project นี้

## Project
**CarbonScan AI** — แพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้ด้วย LiDAR Point Cloud + AI Wood-Leaf Segmentation + B2B Carbon Offset Matchmaking

### Competition
- **NSC 2026** (National Software Contest ครั้งที่ 28)
- **หมวด 14** โปรแกรมเพื่องานการพัฒนาด้านวิทยาศาสตร์และเทคโนโลยี
- **ระดับ:** อุดมศึกษา (ปริญญาตรี)
- **Deadline ใกล้สุด:** 29 พ.ค. 2569 (Proposal) | 17 ก.ค. 2569 (Final Report)

## Team
| Role | Person | Focus |
|---|---|---|
| **Lead / Core** | User | AI/ML, Mobile (Flutter), Backend (FastAPI), Team Lead, Proposal |
| **Frontend** | Person A | Next.js Web Dashboard, 3D Viewer, GIS Map |
| **Design** | Person B | UI/UX (Figma), Branding, Video, Slides |

> ⚠️ ยังไม่ได้ใส่ชื่อจริง — รอข้อมูลจาก User

## Tech Stack
- **Web:** Next.js 14 + TypeScript + Tailwind + shadcn/ui + Three.js + React Three Fiber + Leaflet
- **Mobile:** Flutter (Android + iOS cross-platform) + Riverpod + TFLite
- **Backend:** FastAPI (Python) + PostgreSQL + PostGIS + Supabase
- **AI/ML:** PyTorch + PointNet++ + Open3D + laspy + PDAL + COLMAP + OpenMVS
- **Cloud:** Vercel (Web) + Railway (API) + RunPod Serverless GPU + Supabase

## Key Architecture Decisions
1. **Dual-Input Pipeline** — รับทั้ง .las upload (Public Dataset/Auditor) + Photogrammetry จากภาพถ่ายมือถือ
2. **ไม่ใช้ iPhone LiDAR** — ทีมไม่มี → ใช้ COLMAP/OpenMVS แทน
3. **Cloud GPU On-demand** — RunPod Serverless แทนซื้อ Workstation
4. **Open-Source First** — ทุก component ใช้ open-source ได้
5. **Lock Scope** — Prototype รองรับต้นไม้ 3-5 ชนิด (สัก, ยางนา, ไผ่, ยางพารา, มะค่าโมง)

## Reference Files
- `C:\Users\Acer\Downloads\Carbo.txt` — บันทึกสนทนาเดิม + 5 คำถามอาจารย์
- `D:\Research_Project\CarbontreeNsc\Segment individual trees and compute metrics · r-lidar_lidR Wiki.pdf` — เอกสาร lidR
- `C:\Users\Acer\.claude\plans\c-users-acer-downloads-carbo-txt-d-rese-tingly-moon.md` — Strategic Plan ฉบับเต็ม

## Critical Constraints
- **9 วัน** ถึง Deadline Proposal
- **ต้องเดินลายเซ็น** ที่ปรึกษา + คณบดี/ผอ. (ใช้เวลา 2-3 วัน ในระบบ)
- **ทีมเป็นนักศึกษา** — ไม่มีงบซื้อ Hardware แพง
- **NSC 2026 ระบบปิดอัตโนมัติ** 17:00 น. — ห้ามเลท

## Glossary (ศัพท์ที่ใช้บ่อย)
| Term | Meaning |
|---|---|
| **DBH** | Diameter at Breast Height — เส้นผ่านศูนย์กลางลำต้นที่ระดับอก (1.3 ม.) |
| **QSM** | Quantitative Structure Model — โมเดลทรงกระบอกคำนวณปริมาตรไม้ |
| **CHM** | Canopy Height Model |
| **TLS** | Terrestrial Laser Scanning |
| **TGO** | องค์การบริหารจัดการก๊าซเรือนกระจก (Thailand Greenhouse Gas Management Organization) |
| **Allometric** | สมการแอลโลเมตริก แปลง dimension ของต้นไม้ → biomass |
| **CBAM** | Carbon Border Adjustment Mechanism (EU Carbon Tax) |
| **ITD** | Individual Tree Detection |
| **NEON** | National Ecological Observatory Network (USA — มี LiDAR Open Data) |
| **SfM** | Structure from Motion (Photogrammetry) |
| **MVS** | Multi-View Stereo |

## Preferences
- ตอบเป็นภาษาไทย (แต่ technical terms ใช้ EN ได้)
- โฟกัสที่ "ทำให้กรรมการ NSC ว้าว" — Deep Tech + Visual storytelling
- หลีกเลี่ยง Over-engineer — Prototype ที่ทำเสร็จดีกว่า Vision ที่สมบูรณ์แต่ไม่เสร็จ
- ทุก decision ที่มีค่าใช้จ่าย ให้พิจารณาว่า "นักศึกษาจ่ายไหวไหม"
