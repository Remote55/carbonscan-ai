# Proposal Outline — CarbonScan AI

> Working draft for NSC 2026 Proposal Document
>
> **Length target:** 8-10 หน้า (excluding cover + appendix)

---

## หน้าปก (Cover Page)

- โลโก้ NSC + CarbonScan AI
- ชื่อโครงการ (ไทย + อังกฤษ)
- ทีม + อาจารย์ที่ปรึกษา
- สถาบัน
- วันที่ส่ง
- หมวดการแข่งขัน: หมวด 14 อุดมศึกษา

---

## ข้อมูลโครงการ

| Field | Value |
|---|---|
| ชื่อโครงการ (ไทย) | คาร์บอนสแกน เอไอ: แพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้อัจฉริยะด้วยเทคโนโลยี 3D Vision และระบบจับคู่ชดเชยคาร์บอนภาคอุตสาหกรรม |
| ชื่อโครงการ (อังกฤษ) | CarbonScan AI: 3D Vision Tree Biomass Assessment and B2B Carbon Offset Matchmaking Platform |
| หมวด | 14 — โปรแกรมเพื่องานการพัฒนาด้านวิทยาศาสตร์และเทคโนโลยี |
| ระดับ | อุดมศึกษา (ปริญญาตรี) |
| สมาชิก | (TBD: ชื่อ-สกุล x3) |
| อาจารย์ที่ปรึกษา | (TBD: ชื่อ-สกุล + ตำแหน่ง) |
| สถาบัน | (TBD: ชื่อมหาวิทยาลัย + คณะ) |

---

## บทคัดย่อ (Abstract)

> ⚠️ **เป้าหมาย:** 200-300 คำ พร้อม keywords

ในยุคที่ภาคอุตสาหกรรมทั่วโลกต้องเผชิญมาตรการสิ่งแวดล้อมเข้มงวด (Carbon Neutrality, CBAM) ความต้องการ "คาร์บอนเครดิตภาคป่าไม้" สูงขึ้นอย่างก้าวกระโดด แต่กระบวนการประเมินคาร์บอนเครดิตในไทยยังพึ่งพาผู้ตรวจสอบ (Auditor) ที่มีต้นทุนสูง (~100,000 บาท/แปลง) ทำให้เกษตรกรรายย่อยและชุมชนเข้าไม่ถึงระบบ ในขณะที่โรงงานที่ลงทุนกับ CSR ก็ขาดเครื่องมือตรวจสอบที่โปร่งใส

โครงการ "CarbonScan AI" นำเสนอแพลตฟอร์มประเมินคาร์บอนชีวมวลต้นไม้ที่ผสานเทคโนโลยี **3D Point Cloud Processing + Deep Learning (PointNet++) + Photogrammetry** เข้ากับสถาปัตยกรรม Cloud-native โดยรองรับข้อมูล input 2 ทาง: (1) ไฟล์ LiDAR Point Cloud `.las/.laz` จาก Auditor หรือ Public Dataset และ (2) ภาพถ่ายจากกล้องสมาร์ทโฟนทั่วไป (Android/iOS) ที่นำมา reconstruction ด้วยเทคนิค Structure-from-Motion (COLMAP/OpenMVS)

ระบบจะทำการแยกจุดข้อมูลใน point cloud ออกเป็นใบและลำต้น/กิ่ง (Wood-Leaf Semantic Segmentation) จากนั้นคำนวณปริมาตรไม้ผ่าน Quantitative Structure Model (QSM) และแปลงเป็นปริมาณคาร์บอนโดยใช้สมการแอลโลเมตริก (Allometric Equation) ตามมาตรฐานองค์การบริหารจัดการก๊าซเรือนกระจก (TGO) ผลลัพธ์จะแสดงผ่าน Web Dashboard 3D และระบบจับคู่ B2B ระหว่างชุมชนผู้ปลูกต้นไม้และโรงงานอุตสาหกรรม พร้อมระบบป้องกันการนับซ้ำด้วย GPS + EXIF metadata

ในเวอร์ชันต้นแบบ ระบบรองรับการจำแนกและคำนวณคาร์บอนของไม้เศรษฐกิจ 5 ชนิด (สัก, ยางนา, ไผ่, ยางพารา, มะค่าโมง) ด้วยความแม่นยำ DBH ±5cm และคาดว่าจะช่วยลดต้นทุนการประเมินคาร์บอนเครดิตภาคป่าไม้ในไทยได้กว่า 100 เท่า

**Keywords:** LiDAR, Point Cloud, Wood-Leaf Segmentation, PointNet++, Carbon Credit, Allometric Equation, Photogrammetry, Climate FinTech, ESG

---

## 1. หลักการและเหตุผล (Background & Rationale)

### 1.1 บริบทระดับโลกและไทย
- Carbon Neutrality 2050
- CBAM (มีผลตั้งแต่ปี 2026)
- ความต้องการ Carbon Credit ภาคป่าไม้

### 1.2 ปัญหาคอขวด
- กระบวนการ Auditing ต้นทุนสูง (~100,000 บาท/แปลง)
- ใช้สายวัดทีละต้น (slow, error-prone)
- ชุมชนเข้าไม่ถึง
- โรงงานเสี่ยง Greenwashing

### 1.3 ทำไมต้องใช้ AI + 3D
- ลดต้นทุน 100×
- โปร่งใส ตรวจสอบได้
- Scalable

### 1.4 Why Now
- LiDAR ราคาลดลง
- 3D Deep Learning เทคโนโลยี mature (PointNet++, KPConv)
- Cloud GPU on-demand (RunPod, etc.)

---

## 2. วัตถุประสงค์ (Objectives)

1. พัฒนาระบบประมวลผล LiDAR Point Cloud ที่สามารถแยกใบและลำต้น/กิ่งของต้นไม้ได้อย่างอัตโนมัติ (Wood-Leaf Semantic Segmentation) ด้วย IoU ≥ 0.70
2. พัฒนาระบบคำนวณปริมาตรไม้ผ่าน Quantitative Structure Model (QSM) และคาร์บอนผ่านสมการแอลโลเมตริก TGO
3. พัฒนา Web Dashboard ที่แสดงผล 3D Point Cloud + GIS Map + Marketplace สำหรับการจับคู่ B2B
4. พัฒนา Mobile Application (Android/iOS) ที่ใช้กล้องธรรมดาถ่ายภาพต้นไม้ + Photogrammetry บน Cloud เพื่อสร้าง Point Cloud สำหรับชุมชนที่ไม่มี LiDAR scanner
5. ทดสอบความแม่นยำของระบบเทียบกับการวัดด้วยสายวัดจริง (Ground Truth) ในต้นไม้ 20 ต้น

---

## 3. ขอบเขตของโครงการ (Scope)

### In-Scope (เวอร์ชัน Prototype สำหรับการแข่งขัน)
- รองรับ 5 ชนิดต้นไม้: สัก, ยางนา, ไผ่, ยางพารา, มะค่าโมง
- Input: `.las/.laz` หรือภาพถ่าย 30-50 รูป
- Output: DBH, Height, Volume, Biomass, Carbon (kg), CO2 equivalent (kg)
- Web Dashboard (responsive) — Industrial + Community views
- Mobile App (Android primary, iOS secondary)
- Marketplace B2B (mock payment flow)

### Out-of-Scope (ในเฟสนี้)
- รองรับต้นไม้ทุกชนิด (จะขยายในเฟสถัดไป)
- Drone integration
- Blockchain ledger
- Real-time scanning (ใช้ async pipeline)
- การชำระเงินจริง (ใช้ Stripe test mode)

---

## 4. วิธีดำเนินการ (Methodology)

### 4.1 สถาปัตยกรรมระบบ
(แทรก architecture diagram จาก `docs/ARCHITECTURE.md`)

### 4.2 ML Pipeline 8 ขั้นตอน
1. Pre-processing
2. Ground Classification (CSF algorithm)
3. Height Normalization
4. Canopy Height Model (Pit-free)
5. Individual Tree Detection (Watershed)
6. **Wood-Leaf Semantic Segmentation (PointNet++)** ⭐
7. Quantitative Structure Model (QSM)
8. Allometric Carbon Calculation (TGO Standard)

(แทรก pipeline diagram + อธิบายแต่ละขั้น 2-3 ประโยค)

### 4.3 เทคโนโลยีที่ใช้

| Layer | Technology |
|---|---|
| Web | Next.js 14, TypeScript, Three.js, Leaflet |
| Mobile | Flutter (Android + iOS) |
| Backend | FastAPI (Python 3.11), PostgreSQL + PostGIS |
| AI/ML | PyTorch, PointNet++, Open3D, laspy, COLMAP |
| Cloud | Vercel, Railway, Supabase, RunPod Serverless GPU |

### 4.4 Dual-Input Architecture
อธิบาย Path A (LAS) + Path B (Photogrammetry)

### 4.5 Anti-Fraud Mechanism
- GPS 6-decimal precision + EXIF
- Camera-only (no gallery)
- Server-side dedup (radius 1-2m)
- Audit log

---

## 5. แผนการดำเนินงาน (Timeline & Milestones)

(แทรก Gantt chart)

| Phase | Window | Deliverables |
|---|---|---|
| 0: Proposal | 20-29 พ.ค. | ส่ง Proposal |
| 1: Foundation | 30 พ.ค. - 30 มิ.ย. | Infra + ML pipeline non-AI |
| 2: Core AI | 1-14 ก.ค. | PointNet++ trained, full pipeline |
| 3: Mobile + Submit | 15-17 ก.ค. | Mobile app + Final submission |
| 4: Pitching | 7-21 ส.ค. | Demo video, pitch deck |

---

## 6. ผลที่คาดว่าจะได้รับ (Expected Outcomes)

### 6.1 ผลผลิตเชิงเทคนิค
- ระบบประเมินคาร์บอนต้นไม้แม่นยำ (DBH RMSE ≤ 5 cm, Wood-Leaf IoU ≥ 0.70)
- เวลาประมวลผล < 10 นาที / แปลง (ไม่รวม upload)
- Mobile App รองรับทั้ง Android + iOS
- Open-source code base (GitHub)

### 6.2 ผลกระทบเชิงสังคม
- ชุมชนเข้าถึง Carbon Credit ด้วยต้นทุน 0 บาท
- โรงงานมีเครื่องมือ Verifiable Carbon Reporting
- TGO มีเครื่องมือเสริมการตรวจสอบ
- สนับสนุน Carbon Neutrality 2050 ของไทย

### 6.3 ผลกระทบเชิงวิชาการ
- Dataset + Trained Models เป็น Open Source สำหรับ research community
- โอกาสตีพิมพ์ paper ระดับนานาชาติ (ICCV, CVPR Workshop)

---

## 7. ข้อจำกัดและแนวทางแก้ไข (Risks & Mitigation)

(ดู section "Project Audit" ใน Strategic Plan)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Photogrammetry แม่นน้อย | กลาง | สูง | Calibration กับ ground truth, report RMSE |
| PointNet++ ไม่ train ทัน | กลาง | สูง | Fallback TLSeparation (rule-based) |
| Cloud GPU แพง | ต่ำ | กลาง | Budget cap, ใช้ Colab/Kaggle ในช่วง dev |
| ทีมงานติด/สอบ | สูง | กลาง | Backup person ทุก role |

### Q&A Defense (เผื่อกรรมการถาม)

**Q: Photogrammetry แม่นเท่า LiDAR ไหม?**
A: ไม่ — แต่ ±5-10 cm พอสำหรับ Prototype + ระบบมี calibration กับ Ground truth

**Q: จะรู้ได้ไงว่าไม่นับซ้ำ?**
A: GPS 6-decimal precision + EXIF + server-side dedup (radius 1-2m)

**Q: ใช้ GPU อะไร?**
A: Training ใน Colab Pro+ (A100), Production บน RunPod Serverless (A10G)

---

## 8. งบประมาณ (Budget)

⚠️ TBD: NSC sponsorship ~฿3,000-5,000

ค่าใช้จ่ายโดยประมาณ:
- Cloud GPU (RunPod): ~$50 (Phase 2-3)
- Domain (carbonscan.ai): ~$10/year
- Print + binding: ~฿500
- Misc: ~฿1,000

---

## 9. เอกสารอ้างอิง (References)

ดู [references.md](references.md)

---

## 10. ภาคผนวก (Appendix)

- A: CV ของทีม
- B: CV ของอาจารย์ที่ปรึกษา
- C: Architecture diagram (full size)
- D: Mockup screenshots
- E: Letter of recommendation (ถ้ามี)
