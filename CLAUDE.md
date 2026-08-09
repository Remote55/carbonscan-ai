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
| **Lead / Core** | User | AI/ML, Backend (FastAPI), Team Lead |
| **Frontend** | Person A | Next.js Web Dashboard, 3D Viewer, GIS Map |
| **Design** | Person B | UI/UX (Figma), Branding, Video, Slides |

> ⚠️ ยังไม่ได้ใส่ชื่อจริง — รอข้อมูลจาก User

## Tech Stack
- **Web:** Next.js 14 + TypeScript + Tailwind + shadcn/ui + Three.js + React Three Fiber + Leaflet
- **Backend:** FastAPI (Python) + PostgreSQL + PostGIS + Supabase
- **AI/ML:** numpy + scipy + scikit-image + Open3D + laspy (production path is tlsep — no GPU, no torch)
- **Cloud:** Vercel (Web) + Railway (API) + RunPod Serverless GPU + Supabase

## Key Architecture Decisions
1. **รับ point cloud จากเครื่องสแกนอย่างเดียว** (.ply / .las / .laz) — เส้นทางถ่ายด้วยโทรศัพท์
   (COLMAP/OpenMVS) ถูกตัดออกเมื่อ 9 ส.ค. 2569 พร้อมแอป Flutter: gate ยังตอบ BLOCKED
   และไม่เคยพิสูจน์ว่าภาพถ่ายลำต้นจริงให้จุดพอ fit วงกลมที่ 1.3 ม. ได้ไหม
   ทิศทางคือทำเส้นทางที่ใช้ได้จริงให้แม่น แทนที่จะขยายไปเส้นทางที่ยังไม่รู้ว่าเป็นไปได้
2. **ไม่ต้องใช้ GPU** — wood/leaf backend ที่ใช้จริงคือ tlsep (PCA บน KD-tree)
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

## Preferences
- ตอบเป็นภาษาไทย (แต่ technical terms ใช้ EN ได้)
- โฟกัสที่ "ทำให้กรรมการ NSC ว้าว" — Deep Tech + Visual storytelling
- หลีกเลี่ยง Over-engineer — Prototype ที่ทำเสร็จดีกว่า Vision ที่สมบูรณ์แต่ไม่เสร็จ
- ทุก decision ที่มีค่าใช้จ่าย ให้พิจารณาว่า "นักศึกษาจ่ายไหวไหม"
