# 5 คำถามที่อาจารย์ขอให้ตอบ

> [!CAUTION]
> **Historical/target Q&A.** RunPod Serverless, WebSocket notification, GIS และ Marketplace
> ที่กล่าวด้านล่างยังเป็น Planned. Demo ที่ตรวจสอบแล้วใช้ local API/worker, GET polling และ
> local/shared filesystem. Current ML default คือ `tlsep`; PointNet++ Experimental/not promoted;
> Species classifier = Stub. ตรวจตัวเลข/ราคาปัจจุบันอีกครั้งก่อนตอบกรรมการ.

> เอามาวาง Proposal section ที่เกี่ยวข้องได้เลย

---

## Q1: คาดว่า GPU ที่จะใช้คือตัวไหน?

**คำตอบ:**

โครงการนี้แบ่งการใช้ GPU เป็น 2 phase:

### Phase Training (ช่วงพัฒนาโมเดล)
- **Google Colab Pro+** (subscription $49.99/เดือน) ให้บริการ NVIDIA A100 40GB หรือ V100 16GB ซึ่งเพียงพอสำหรับการเทรน PointNet++ บน NEON Dataset (จำนวน parameters ~10M, expected training ~100 GPU-hours, ค่าใช้จ่ายรวมประมาณ $50 ตลอด Phase)
- **Backup ฟรี:** Kaggle Notebooks (P100 16GB, ฟรี 30 ชม./สัปดาห์) สำหรับ debugging และ small experiments

### Phase Production / Inference
- **RunPod Serverless GPU** (NVIDIA A10G 24GB หรือ RTX 4090) แบบ pay-per-second ราคา ~$0.39/hr — ปิดตัวอัตโนมัติเมื่อไม่มีงาน (scale-to-zero) เพื่อประหยัดค่าใช้จ่าย
- **Team workstation:** Notebook ของทีม — รัน inference เบาๆ ผ่าน CPU + ONNX Runtime สำหรับ debugging

### เหตุผลการเลือก
ทีมเป็นนักศึกษาระดับปริญญาตรี งบประมาณจำกัด ไม่สามารถลงทุนซื้อ Workstation GPU (RTX 4090 ราคา ~70,000 บาท + ค่าไฟ + ค่าเสื่อมราคา) ได้ — Cloud GPU แบบ on-demand จึงเหมาะสมกว่าทั้งในด้านต้นทุนและ scalability เมื่อโครงการขยายในอนาคต

---

## Q2: เมื่อถึงขั้นตอนการ Inference ผ่าน Platform จะใช้ทรัพยากรอะไร และถ้ามีค่าใช้จ่ายในการประมวลผล จะจัดการอย่างไร?

**คำตอบ:**

### Decoupled Architecture
เราออกแบบระบบให้แยกส่วน Frontend/Backend/GPU Worker ออกจากกัน ดังนี้:

```
[Flutter App / Web Upload]
        │ HTTPS
        ▼
[Next.js Frontend on Vercel] ──── [FastAPI Backend on Railway — $5/mo]
                                        │
                                        ▼
                              [Job Queue (Supabase Queues)]
                                        │ trigger
                                        ▼
                              [RunPod Serverless GPU Worker]
                                        │ pulls job
                                        ▼
                       [Process .las/.ply file (5-15 min)]
                                        │ write
                                        ▼
                            [Supabase Storage + PostGIS DB]
                                        │ notify via WebSocket
                                        ▼
                              [User sees result on Dashboard]
```

### ค่าใช้จ่ายต่อเดือน (Prototype scale, ~100 jobs/เดือน)

| ทรัพยากร | ค่าใช้จ่าย |
|---|---|
| Vercel (Web Dashboard) | $0 (Hobby tier) |
| FastAPI Backend on Railway | $5 |
| Supabase (DB + Storage 1GB + Auth) | $0 (Free tier) |
| RunPod GPU (avg 10 นาที/job × 100 jobs × $0.39/hr) | ~$6.50 |
| **รวม** | **~$11.50/เดือน (~400 บาท)** |

### Business Model (สำหรับ Scaling)
- **B2B Subscription:** Industrial users จ่าย ฿200/ไร่ ที่ Auditing — cover ค่า GPU + กำไรประมาณ 80%
- **Freemium:** Community users สแกนต้นไม้ฟรี (Cross-subsidized by B2B revenue)
- **Auditor Pro:** ฿2,000/เดือน — unlimited scans

หากมี traffic เพิ่มขึ้น เราสามารถ scale RunPod workers สูงสุด 3 concurrent (default) และเพิ่ม Supabase plan เป็น Pro ($25/mo) ได้

### Budget Control
- ตั้ง budget alert ที่ $20/เดือน (email notification)
- Idle timeout ของ RunPod = 5 วินาที (ปิดเร็วที่สุด)
- Max workers = 3 (กัน runaway cost)
- ทุก compute-heavy operation ผ่าน Job Queue (ไม่ใช่ synchronous)

---

## Q3: ประโยชน์ของงานนี้เพื่อใคร อย่างไรบ้าง?

**คำตอบ:**

ใช้กรอบ Triple Helix (Industry + Society + Government) + Academic:

### 1. เกษตรกร / ชุมชนผู้ปลูกต้นไม้ (Society)
- เปลี่ยนต้นไม้ที่ปลูกเป็นรายได้ผ่านการขาย Carbon Credit โดยไม่ต้องจ้าง Auditor
- **ลดต้นทุนเข้าระบบจาก ฿100,000 → ฿0**
- เข้าถึงระบบเศรษฐกิจสีเขียวที่เคยเป็นเอกสิทธิ์ของบริษัทขนาดใหญ่

### 2. โรงงานอุตสาหกรรม / SMEs (Industry)
- มีตัวกลาง B2B ที่โปร่งใส เห็น GPS หมุดของต้นไม้ทุกต้นที่สนับสนุน
- หลีกเลี่ยงข้อครหา **Greenwashing**
- พร้อมรับมือมาตรการ **CBAM** (Carbon Border Adjustment Mechanism) ของ EU
- สร้าง ESG report ที่ verifiable ระดับ 3D

### 3. TGO / Carbon Auditors (Government / Verification Body)
- ลดเวลาลงพื้นที่จริงจาก **หลายสัปดาห์ → ชั่วโมง**
- ตรวจสอบความถูกต้องของข้อมูลย้อนหลังได้จากไฟล์ 3D Point Cloud
- เพิ่ม capacity ในการ verify โครงการคาร์บอนเครดิต

### 4. ภาคการศึกษา / วิจัย (Academic)
- Dataset และ Trained Model เป็น Open Source สำหรับ research community
- ลด barrier ในการทำงานวิจัย Forest Inventory
- เป็นต้นแบบสำหรับ multi-disciplinary research (CS + Forestry + GIS)

### 5. ประเทศไทย (National)
- สนับสนุนเป้าหมาย **Carbon Neutrality 2050** ของรัฐบาล
- เพิ่มขีดความสามารถในการส่งออกสินค้าเข้าตลาด EU (CBAM compliance)
- พัฒนา Climate FinTech ecosystem ของไทย

---

## Q4: คิดว่าตรงกับหัวข้อไหนของการแข่งขัน?

**คำตอบ:**

**หมวด 14 — โปรแกรมเพื่องานการพัฒนาด้านวิทยาศาสตร์และเทคโนโลยี** สำหรับระดับอุดมศึกษา

### เหตุผล Defend ได้

1. **Deep Tech ชัดเจน**
   - 3D Point Cloud Deep Learning (PointNet++, KPConv) เป็น Computer Science Research-grade
   - QSM (Quantitative Structure Model) เป็นเทคนิคจาก Forestry Science ระดับนานาชาติ
   - Photogrammetry + Structure from Motion (COLMAP/OpenMVS)

2. **Multi-disciplinary Science**
   ผสาน 3 สาขา:
   - Computer Science (3D Deep Learning, Cloud Architecture)
   - Forestry Science (Allometric Equation, Wood Biomass)
   - Geospatial Science (PostGIS, GIS Mapping)

3. **มี Output เป็น Scientific Methodology**
   - ไม่ใช่แค่ App ใช้งานทั่วไป
   - เป็น Tool ที่สนับสนุนการวิจัย และ open source dataset/model
   - มีศักยภาพตีพิมพ์ paper ในงานประชุมวิชาการระดับนานาชาติ

4. **ตรงธีม Sustainable Innovation ของ NSC 2026**
   - แก้ปัญหา Climate Change ด้วย Software Technology
   - มี measurable environmental impact (kgCO2eq/ต้น)

หากต้องเปรียบเทียบกับหมวดอื่น:
- ❌ หมวด 11 (บันเทิง) — ไม่ใช่
- ❌ หมวด 12 (การเรียนรู้) — ไม่ใช่หลัก
- ❌ หมวด 13 (สุขภาพ) — ไม่ใช่
- ✅ **หมวด 14 (วิทยาศาสตร์และเทคโนโลยี) — ตรงที่สุด**

---

## Q5: ทำไมจึงอยากทำงานนี้?

**คำตอบ (Personal Statement):**

> ⚠️ **User ใส่ Passion ของตัวเองเพิ่ม** — Template ด้านล่างเป็น guide

พวกเรา 3 คนมีพื้นฐานด้าน Software Development, Artificial Intelligence และ Design ที่หลากหลาย แต่สิ่งที่เราเชื่อร่วมกันคือ:

> **"คอขวดของการแก้ปัญหา Climate Change ในไทยไม่ใช่ 'การปลูกต้นไม้' แต่คือ 'การวัดผลที่โปร่งใส แม่นยำ และเข้าถึงได้'"**

ปัจจุบันการประเมินคาร์บอนเครดิตป่าไม้ในไทยมีต้นทุนสูงระดับแสนบาทต่อแปลง — ทำให้ชุมชนรายย่อยเข้าไม่ถึงระบบ และโรงงานก็ตรวจสอบผลลัพธ์การลงทุน CSR ไม่ได้

เรามองว่าหากเรานำ **LiDAR Point Cloud + AI Wood-Leaf Segmentation + Open Data** มาผสานกันบน Platform เดียว จะสามารถ:
1. ลดต้นทุน Auditing ลง **100 เท่า**
2. เพิ่มความโปร่งใส (Verifiable via 3D Visualization)
3. เป็นจุดเริ่มต้นของ **Climate FinTech ของประเทศไทย**

นอกจากนี้ ทีมพวกเรามีความสนใจเป็นการส่วนตัวในเทคโนโลยี:
- **3D Computer Vision** (Point Cloud Processing เป็น frontier ของ CV)
- **Sustainability Tech** (ESG เป็นเมกะเทรนด์ที่ทุกบริษัทต้องรับมือ)
- **Multi-disciplinary research** (ผสาน CS กับ Forestry/Environment)

เราจึงอยากใช้ NSC 2026 เป็นโอกาสในการ:
- นำทักษะที่มีไปสร้างผลกระทบจริงต่อสังคม
- เรียนรู้ Deep Tech ที่ผสาน multi-disciplinary
- สร้าง portfolio + foundation สำหรับการต่อยอดเป็น Startup หลังเรียนจบ

---

## ใช้คำตอบเหล่านี้ที่ไหนใน Proposal?

| Question | Suggested Placement |
|---|---|
| Q1 (GPU) | Section 4.3 "เทคโนโลยีที่ใช้" + ภาคผนวก D "Compute Resources" |
| Q2 (Inference + Cost) | Section 4.4 "Architecture" + Section 7 "Sustainability Plan" |
| Q3 (Beneficiaries) | Section 6 "ผลที่คาดว่าจะได้รับ" |
| Q4 (Category match) | Section 1 "Background" + Cover Letter |
| Q5 (Motivation) | Section 1.5 "Motivation" หรือ Cover Letter / Introduction |

📖 **See also:**
- [outline.md](outline.md) — Full proposal outline
- [docs/decisions/](../docs/decisions/) — Architectural decisions
