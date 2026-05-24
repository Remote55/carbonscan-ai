# 📚 CarbonScan AI — คู่มือเรียนรู้ระบบฉบับสมบูรณ์

> **สำหรับ:** สมาชิกทีม CarbonScan AI (User + Person A + Person B) + ผู้สนใจโปรเจกต์
> **ระดับความรู้ที่ต้องมีก่อนอ่าน:** เป็นนักศึกษา CS ปี 2-3 (รู้ Python/JS พื้นฐาน, ไม่ต้องรู้ ML/3D/LiDAR มาก่อน)
> **เวลาในการอ่านทั้งหมด:** ~6-8 ชั่วโมง (ถ้าจริงจัง) หรือ ~2-3 ชั่วโมง (ถ้าอ่านเฉพาะ summary)

---

## 🎯 คู่มือนี้คืออะไร

CarbonScan AI เป็นระบบใหญ่ที่มี **4 ภาษา** (Python, TypeScript, Dart, SQL), **8 ขั้นตอน ML**, และ **9 papers ที่อ้างอิง** — เอาเข้าจริงเปิด GitHub repo ครั้งแรกก็งง

คู่มือนี้เขียนเพื่อตอบคำถาม:
- **"ระบบนี้ทำอะไร?"** → [01-overview.md](01-overview.md)
- **"LiDAR / Point Cloud คืออะไร?"** → [02-core-concepts.md](02-core-concepts.md)
- **"สถาปัตยกรรมเป็นยังไง?"** → [03-architecture.md](03-architecture.md)
- **"AI ของเรา 8 ขั้นทำอะไรบ้าง?"** → [04-13 ML chapters](#part-2--ml-pipeline-โฟกัสหลัก-10-บท)
- **"Carbon คำนวณยังไง สูตรอะไร?"** → [12-ml-step8-allometric.md](12-ml-step8-allometric.md) ⭐
- **"Web/Mobile/API ใช้ลายไลบรารีอะไร?"** → [14-17 Application Layers](#part-3--application-layers-4-บท)
- **"Deploy ยังไง?"** → [19-devops-cicd.md](19-devops-cicd.md)

---

## 📖 สารบัญ (Table of Contents)

### Part 1 — Foundations (เริ่มจากตรงนี้)

| บท | หัวข้อ | เวลา | ลิงก์ |
|---|---|---|---|
| 01 | ภาพรวมโครงการ — ทำไมต้องมี CarbonScan AI | 15 นาที | [→](01-overview.md) |
| 02 | แนวคิดพื้นฐาน — LiDAR, Point Cloud, GIS, Carbon Credit | 30 นาที | [→](02-core-concepts.md) |
| 03 | สถาปัตยกรรมระบบ — 4 layers + ADRs | 20 นาที | [→](03-architecture.md) |

### Part 2 — ML Pipeline (โฟกัสหลัก — 10 บท)

> 🔥 **บทสำคัญที่สุด:** บท 12 (Allometric) — ทุกสูตรคาร์บอน

| บท | หัวข้อ | สูตร/Algorithm | ลิงก์ |
|---|---|---|---|
| 04 | ภาพรวม ML Pipeline 8 ขั้น | Pipeline diagram | [→](04-ml-pipeline-overview.md) |
| 05 | Step 1: แยกพื้นดิน (Ground Classification) | CSF + grid heuristic | [→](05-ml-step1-ground-classification.md) |
| 06 | Step 2: ปรับความสูง (Height Normalization) | KD-tree + IDW | [→](06-ml-step2-height-normalization.md) |
| 07 | Step 3: สร้าง CHM (Canopy Height Model) | Pit-free, max-Z raster | [→](07-ml-step3-canopy-height-model.md) |
| 08 | Step 4: แยกต้นไม้ทีละต้น (Tree Segmentation) | Watershed segmentation | [→](08-ml-step4-tree-segmentation.md) |
| 09 | Step 5: แยกลำต้น/ใบ (Wood-Leaf Separation) | PCA eigenvalues + PointNet++ | [→](09-ml-step5-wood-leaf-separation.md) |
| 10 | Step 6: วัด DBH/Height/Volume (QSM) | RANSAC circle + Taper equation | [→](10-ml-step6-qsm.md) |
| 11 | Step 7: จำแนกพันธุ์ไม้ (Species Classifier) | ResNet-50 + TFLite | [→](11-ml-step7-species-classifier.md) |
| **12** | **Step 8: คำนวณคาร์บอน (Allometric) ⭐** | **AGB = a × DBH^b × H^c, etc.** | [→](12-ml-step8-allometric.md) |
| 13 | Validation — Synthetic + Belgium (Demol 2021) | MAE, RMSE, parity plots | [→](13-ml-validation.md) |

### Part 3 — Application Layers (4 บท)

| บท | หัวข้อ | Tech | ลิงก์ |
|---|---|---|---|
| 14 | Frontend Web | Next.js 14 + Three.js + Leaflet | [→](14-frontend-web.md) |
| 15 | Frontend Mobile | Flutter 3.44 + Riverpod + camera | [→](15-frontend-mobile.md) |
| 16 | Backend API | FastAPI + PostgreSQL + PostGIS | [→](16-backend-api.md) |
| 17 | Data Flow — End-to-end User Journey | 3 user paths | [→](17-data-flow.md) |

### Part 4 — Infrastructure & Process (3 บท)

| บท | หัวข้อ | ลิงก์ |
|---|---|---|
| 18 | เครื่องมือและฮาร์ดแวร์ (LiDAR scanners, Cloud GPUs) | [→](18-tools-hardware.md) |
| 19 | DevOps & CI/CD (Git workflow, deploys, monitoring) | [→](19-devops-cicd.md) |
| 20 | ชุดข้อมูล (Synthetic + Belgium + future) | [→](20-datasets.md) |

### Part 5 — Reference (1 บท)

| บท | หัวข้อ | ลิงก์ |
|---|---|---|
| 21 | Bibliography + Glossary EN↔ไทย + Further reading | [→](21-references-glossary.md) |

---

## 🗺️ ลำดับการอ่านที่แนะนำ (Recommended Reading Path)

### Path A — สำหรับคนใหม่ (อ่านครั้งแรก) — 6-8 ชั่วโมง

```
01 → 02 → 03 → 04 → (05-11 ตามลำดับ) → 12 → 13 → 14 → 15 → 16 → 17 → 18 → 19 → 20 → 21
```

### Path B — สำหรับเตรียม NSC pitching — 2 ชั่วโมง

```
01 (Overview)
↓
12 (Allometric — สูตรหลัก ต้องท่องได้)
↓
13 (Validation results — ตัวเลขโชว์)
↓
21 (Citations — ถ้ากรรมการถาม "อ่าน paper ไหน")
```

### Path C — สำหรับ Person A (Web frontend) — 3 ชั่วโมง

```
01 → 03 → 17 (data flow ที่ web ต้องเห็น)
↓
14 (Frontend Web tech stack)
↓
16 (API endpoints ที่ web เรียก)
↓
19 (Deploy Vercel)
```

### Path D — สำหรับ Person B (Design) — 2 ชั่วโมง

```
01 → 02 (concept ที่ design ต้องสื่อ)
↓
03 (architecture เพื่อทำ diagram)
↓
17 (user journey — กำหนด UX)
↓
20 (datasets — สำหรับ infographic)
```

### Path E — แก้ปัญหาเฉพาะ (Quick Lookup)

| ถ้าอยากรู้ | อ่านบท |
|---|---|
| สูตร AGB / Carbon | 12 |
| ทำไมเลือก Next.js ไม่ใช่ Vite | 03 (ADR 0003) |
| GPS dedup ทำยังไง | 02 (Anti-fraud) + 16 (PostGIS query) |
| Validation accuracy ของเรา | 13 |
| LiDAR scanner ราคาเท่าไหร่ | 18 |
| ทำไม Volume error 18.8% | 10 (Taper limitations) + 13 |
| Belgium dataset มาจากไหน | 20 |
| TGO 2017 standard คืออะไร | 12 + 21 |

---

## 🔧 Quick Lookup — สูตรที่ใช้บ่อย (Cheat Sheet)

> 💡 รายละเอียดสูตรทั้งหมดอยู่ในบท 12 — นี่คือสรุปด่วน

### Allometric — DBH + Height → Biomass → Carbon → CO₂eq

```
1. AGB (Above-Ground Biomass)
   • Species-specific:  AGB = a × DBH^b × H^c        [kg]
   • Pantropical fallback (Chave 2014):
                        AGB = 0.0673 × (ρ × DBH² × H)^0.976  [kg]
                        (ρ = wood density g/cm³, DBH cm, H m)

2. BGB (Below-Ground Biomass)
                        BGB = AGB × 0.24             [kg]
                        (root:shoot ratio, IPCC 2006 tropical default)

3. Total Biomass
                        B = AGB + BGB                [kg]

4. Carbon
                        C = B × 0.47                 [kg C]
                        (carbon fraction, IPCC 2006 default)

5. CO₂ equivalent
                        CO₂eq = C × (44/12)          [kg CO₂]
                        (molecular mass ratio C → CO₂)
```

### Tree Geometry

```
DBH measurement:       Diameter of trunk at 1.3 m above ground   [cm]
Tree height:           Max-Z of point cloud (after normalization) [m]
Stem volume (taper):   V = (π/4) × DBH² × H × form_factor         [m³]
                       form_factor ≈ 0.5 for typical trees
```

### Validation Stats

```
MAE  = (1/n) Σ |pred - truth|        — Mean Absolute Error
RMSE = √((1/n) Σ (pred - truth)²)    — Root Mean Squared Error
Bias = (1/n) Σ (pred - truth)        — signed mean error
Error% = (pred - truth) / truth × 100
```

---

## 📋 Glossary — ศัพท์ที่ต้องรู้ก่อน

> รายละเอียดเต็มในบท [21-references-glossary.md](21-references-glossary.md)

| EN | ไทย | คำอธิบายสั้น |
|---|---|---|
| **LiDAR** | ลีดาร์ | เครื่องสแกน 3 มิติด้วย laser |
| **Point Cloud** | กลุ่มจุด 3D | ข้อมูลผลลัพธ์ของ LiDAR — ล้านๆ จุดในพื้นที่ 3D |
| **TLS** | Terrestrial Laser Scanning | LiDAR ตั้งกับพื้น |
| **ALS** | Airborne Laser Scanning | LiDAR ติด drone/เครื่องบิน |
| **DBH** | Diameter at Breast Height | เส้นผ่านศูนย์กลางลำต้นที่ระดับอก (1.3 ม.) |
| **CHM** | Canopy Height Model | แผนที่ความสูงเรือนยอด |
| **QSM** | Quantitative Structure Model | โมเดลทรงกระบอกของต้นไม้ |
| **AGB** | Above-Ground Biomass | ชีวมวลเหนือพื้นดิน (กก.) |
| **BGB** | Below-Ground Biomass | ชีวมวลรากใต้ดิน (กก.) |
| **CSF** | Cloth Simulation Filter | อัลกอริทึมแยกพื้นดินจาก Point Cloud |
| **PCA** | Principal Component Analysis | วิธีหาแกนที่ data spread มากที่สุด |
| **RANSAC** | Random Sample Consensus | วิธี fit shape บน data ที่มี outlier |
| **TGO** | Thailand Greenhouse Gas Management Organization | องค์การบริหารจัดการก๊าซเรือนกระจก |
| **Chave 2014** | สูตร pantropical biomass | สมการมาตรฐานป่าเขตร้อนทั่วโลก |
| **IPCC** | Intergovernmental Panel on Climate Change | คณะกรรมการระหว่างประเทศ — ค่ามาตรฐานคาร์บอน |
| **CBAM** | Carbon Border Adjustment Mechanism | ภาษีคาร์บอนหน้าด่าน EU |

---

## 🎨 Convention ใน Doc นี้

- 🟢 **สีเขียว** = สิ่งที่ทำได้แล้ว (Phase 1 implemented)
- 🟡 **สีเหลือง** = สิ่งที่ออกแบบไว้แต่ยังไม่ได้ implement
- 🔴 **สีแดง** = สิ่งที่ยังไม่ทำ (Phase 2+)
- 📂 **`path/to/file.py`** = อ้างอิงไฟล์ในโปรเจกต์ — เปิดดูได้
- 💡 **Tip** = เคล็ดลับ/ข้อสังเกต
- ⚠️ **Warning** = ระวัง pitfall
- ❓ **คำถามตรวจสอบ** = ตอบเองได้ = เข้าใจจริง

---

## 🧪 วิธีตรวจสอบว่าเข้าใจจริง

หลังอ่านจบทุกบท ลองทำ:

1. **Self-test ทุกบท** — ทำ "คำถามตรวจสอบความเข้าใจ" ท้ายบท (3-5 ข้อ)
2. **Verify formulas** — เปิด `services/ml/pipeline/allometric.py` แล้วเทียบกับบท 12
3. **Run tests** — `cd services/ml && pytest` ผ่าน 25/25
4. **Run notebook** — `jupyter notebooks/e2e_validation.ipynb` รันได้
5. **อธิบายให้คนอื่นฟัง** — สอน Person A หรือ Person B เรื่อง "ML pipeline ทำอะไร" ใน 5 นาที — ถ้าทำได้ = เข้าใจจริง

---

## 🔄 Document History

| เวอร์ชัน | วันที่ | สิ่งที่เปลี่ยน |
|---|---|---|
| v1.0 | 2026-05-24 | เริ่มเขียน — รวม master + Part 1 + บท 12 |

---

## 📞 Contact

ถ้าอ่านแล้วงงตรงไหน — ทักใน Discord/Line group ของทีม + บอกบทกับ section ที่ติด ผู้เขียนจะแก้/อธิบายเพิ่ม

> 💡 **Tip:** ถ้าจะอ่านบนเครื่อง — เปิด VS Code → ติดตั้ง extension "Markdown Preview Enhanced" → จะแสดงสูตร LaTeX สวยและ TOC navigate ได้
