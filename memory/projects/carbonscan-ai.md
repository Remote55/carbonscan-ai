# Project: CarbonScan AI

## Summary
แพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้ด้วย LiDAR Point Cloud Processing + AI Wood-Leaf Segmentation + B2B Carbon Offset Matchmaking

## Competition Context
- **NSC 2026** (National Software Contest ครั้งที่ 28)
- **หมวด:** 14 (โปรแกรมเพื่อการพัฒนาด้านวิทยาศาสตร์และเทคโนโลยี)
- **ระดับ:** อุดมศึกษา (ปริญญาตรี)
- **ธีม:** Sustainable Innovation
- **Organizer:** สวทช. (NSTDA)

## Why
**คอขวดของการแก้ปัญหา Climate Change** ในไทยไม่ใช่การปลูกต้นไม้ แต่คือ "การวัดผลที่โปร่งใส แม่นยำ และเข้าถึงได้"
- ปัจจุบัน Carbon Credit Auditing ต้นทุนสูง ~100,000 บาท/แปลง
- ชุมชน/เกษตรกรเข้าไม่ถึงระบบ
- โรงงาน CSR ตรวจสอบผลลัพธ์ไม่ได้ → เสี่ยง Greenwashing

## Solution Architecture
**Dual-Input Pipeline:**
1. **Path A:** Auditor/Public upload .las/.laz → Cloud Pipeline → AI Wood-Leaf Segmentation → QSM → Carbon Calculation
2. **Path B:** Community member ถ่ายภาพรอบต้นไม้ผ่าน Flutter App → Cloud Photogrammetry (COLMAP/OpenMVS) → Same pipeline as A

**Output:**
- Web Dashboard with 3D Viewer (Three.js)
- GIS Map (Leaflet + PostGIS) with GPS pins
- B2B Marketplace for carbon credits
- PDF reports

## Key Decisions
- **ไม่ใช้ iPhone LiDAR** เพราะทีมไม่มี → ใช้ Photogrammetry + Public Dataset แทน
- **Lock Scope** 3-5 ชนิดต้นไม้ (สัก, ยางนา, ไผ่, ยางพารา, มะค่าโมง)
- **Cloud GPU On-demand** (RunPod Serverless) แทนซื้อ Workstation
- **Open-Source First** — ทุก component ใช้ open-source

## Critical Deadlines
| Date | Milestone |
|---|---|
| 29 พ.ค. 2569 17:00 | ส่ง Proposal ในระบบ SIMs |
| 12 มิ.ย. 2569 | ประกาศผลรอบ Proposal |
| 17 ก.ค. 2569 17:00 | ส่ง Final Report |
| 7 ส.ค. 2569 | ประกาศผลรอบนำเสนอ + เข้ารอบชิง |
| 21 ส.ค. 2569 | รอบชิงชนะเลิศ |
| 24 ส.ค. 2569 | ประกาศผลรอบชิง |

## Team
3 คน — รายละเอียดอยู่ใน [[team-roles]]

## Tech Stack
- Web: Next.js + TypeScript + Three.js + Leaflet
- Mobile: Flutter (Android + iOS)
- Backend: FastAPI + Supabase (PostGIS)
- AI/ML: PyTorch + PointNet++ + Open3D + COLMAP
- Cloud: Vercel + Railway + RunPod Serverless GPU

## Reference
- Strategic Plan: `C:\Users\Acer\.claude\plans\c-users-acer-downloads-carbo-txt-d-rese-tingly-moon.md`
- Original brief: `C:\Users\Acer\Downloads\Carbo.txt`
- lidR Wiki: `D:\Research_Project\CarbontreeNsc\Segment individual trees and compute metrics · r-lidar_lidR Wiki.pdf`
