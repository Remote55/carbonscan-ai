# บท 01 — ภาพรวมโครงการ CarbonScan AI

> 🎯 **เป้าหมายของบท:** หลังอ่านจบ ผู้อ่านจะตอบได้ว่า "CarbonScan AI คืออะไร แก้ปัญหาอะไร สำหรับใคร และต่างจากที่มีอยู่ยังไง"
> 📚 **ความรู้พื้นฐานที่ต้องมีก่อน:** ไม่มี (เริ่มจากศูนย์)
> ⏱️ **เวลาในการอ่าน:** ~15 นาที

---

## 1. ปัญหาที่เราพยายามแก้

### 1.1 พื้นหลัง — ตลาดคาร์บอนเครดิตกำลังบูม

ตั้งแต่ปี 2024 เป็นต้นมา ตลาด **คาร์บอนเครดิต (Carbon Credit)** ของโลกขยายตัวอย่างก้าวกระโดด เพราะ:

1. **EU CBAM (Carbon Border Adjustment Mechanism)** — ภาษีคาร์บอนหน้าด่าน — สินค้าที่ส่งออก EU ต้องชดเชยคาร์บอนเป็นเงิน
2. **Net Zero commitments** — บริษัทใหญ่ทั่วโลกประกาศจะ "เป็นกลางทางคาร์บอน" ภายในปี 2050
3. **TGO (องค์การบริหารจัดการก๊าซเรือนกระจก)** — ประเทศไทยมีกฎหมายและมาตรฐานของตัวเอง
4. **ESG reporting** — นักลงทุนเรียกร้องให้บริษัทเปิดเผยตัวเลขคาร์บอน

ผลคือ **โรงงาน/บริษัทอุตสาหกรรม** ต้อง "ซื้อ" คาร์บอนเครดิตเพื่อชดเชยที่ตัวเองปล่อย — และ **คาร์บอนเครดิตป่าไม้** เป็นแหล่งหลักของตลาดนี้

### 1.2 คอขวด — การ "วัดคาร์บอน" ในป่ายังโบราณ

ก่อนที่ป่าจะ "ขาย" คาร์บอนเครดิตได้ ต้องมีคน **วัด** ก่อนว่าเก็บคาร์บอนได้กี่ตัน วิธีดั้งเดิม:

```
ทีม Forest Auditor 5-10 คน
     ↓
เดินเข้าป่า 1-2 สัปดาห์
     ↓
ใช้ ตลับเมตร โอบรอบลำต้น (วัด DBH ทีละต้น)
     ↓
ใช้ Clinometer ส่องยอดต้นเพื่อวัดความสูง
     ↓
จดในกระดาษ พิมพ์เข้า Excel
     ↓
ทำ Report ส่ง TGO หรือ Auditor ต่างประเทศ
```

**ปัญหาที่เห็นชัด:**

| ปัญหา | ผลกระทบ |
|---|---|
| 💰 **ต้นทุนสูง** | ตรวจ 1 แปลง 100 ไร่ = ฿50,000-200,000 — เกษตรกรรายย่อยจ่ายไม่ไหว |
| ⏱️ **ช้า** | 2-4 สัปดาห์ต่อแปลง — โครงการระดับชาติใช้เวลาเป็นปี |
| 👁️ **คลาดเคลื่อน (Human Error)** | คนวัดทีละต้น ความสูงด้วยตา — error ±10-20% ปกติ |
| 🕵️ **ตรวจสอบยาก (Verifiability)** | ส่ง Excel ให้ดู ไม่มี evidence ที่ third-party verify ได้ |
| 🚨 **เสี่ยง Greenwashing** | ไม่มีกลไกป้องกันการนับซ้ำ หรือรายงานเกิน |

**ใครเดือดร้อนบ้าง?**

1. **เกษตรกร/ชุมชนผู้ปลูก** → มีต้นไม้ แต่เข้าตลาดคาร์บอนไม่ได้ เพราะค่าตรวจสูง
2. **โรงงานผู้ซื้อ** → จ่ายเงิน CSR ปลูกป่า แต่ไม่รู้ว่าได้คาร์บอนจริงไหม — เสี่ยง greenwashing
3. **รัฐ/TGO** → อยากเก็บภาษีคาร์บอนได้แม่นยำ แต่ไม่มี infrastructure ที่ scalable
4. **Carbon auditors** → ต้องทำงานช้าและแพง เพราะใช้เครื่องมือเก่า

### 1.3 ความจริงเพิ่มเติม — มี LiDAR แล้ว แต่ยังไม่พอ

> ⚠️ **อย่าเข้าใจผิด:** "LiDAR" (เลเซอร์สแกน 3D) มีในตลาดมาตั้งหลายปีแล้ว — drone-LiDAR scan ป่าได้ใน 1 บินเที่ยว

แล้วทำไมยังต้องมี CarbonScan AI?

เพราะ **LiDAR scanner = "data provider"** — เขาให้แค่ไฟล์ `.las` (point cloud) เท่านั้น

หลังจาก scan เสร็จ ลูกค้ายังต้อง:
1. หา**software** ที่ประมวลผล .las → แยกต้นไม้ → คำนวณคาร์บอน
2. หา**Auditor** ที่ตรวจสอบ certify
3. หา**Marketplace** ที่ขายคาร์บอนได้
4. ตรวจ**Anti-fraud** ว่าไม่ได้นับซ้ำ
5. ทำ**audit log** สำหรับ ESG reporting

**ทุกอย่างหลังจาก scan = ปัญหา software ที่ยังไม่มีใครแก้ครบ**

---

## 2. ทางออกของเรา — CarbonScan AI

### 2.1 One-liner

> **"LiDAR services ให้ไฟล์ .las — เราให้ carbon credit ที่ verify แล้วพร้อมขาย"**

CarbonScan AI **ไม่ใช่ตัวสแกน** เป็น **software platform** ที่อยู่ระหว่าง LiDAR ↔ Marketplace

### 2.2 Input → Processing → Output Flow

```
┌─ INPUT ─────────────────────────────────────────┐
│  • LiDAR (.las/.laz) จาก TLS / Drone — primary  │
│  • Mobile photogrammetry (30 JPG → .ply) —      │
│    secondary, smallholder only                  │
│  • CSV inventory file — bonus                   │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─ PROCESSING ─────────────────────────────────────┐
│  ML Pipeline 8 ขั้น (รัน Cloud GPU):            │
│   1. Ground classification (CSF)                │
│   2. Height normalization                       │
│   3. Canopy Height Model (CHM)                  │
│   4. Tree segmentation (Watershed)              │
│   5. Wood/Leaf separation (AI)                  │
│   6. QSM (DBH + Height + Volume)                │
│   7. Species classification (ResNet)            │
│   8. Allometric → Carbon (TGO 2017)             │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─ OUTPUT ─────────────────────────────────────────┐
│  📜 Verified Carbon Certificate (PDF)            │
│  🏪 B2B Marketplace listing — ชุมชน ↔ โรงงาน    │
│  📊 GIS Map + Audit Log (Additionality tracking)│
└──────────────────────────────────────────────────┘
```

---

## 3. 5 จุดเด่นที่ LiDAR-only ทำไม่ได้

> 💡 จุดเด่นเหล่านี้คือ "เหตุผลที่ user จะซื้อ idea เรา" — ตรงกับสิ่งที่อาจารย์ Wannipa แนะนำให้คิด

### 🇹🇭 1. Thai-localized
- TGO 2017 species DB (สมการของไทยโดยเฉพาะ)
- UI/Documentation ภาษาไทย
- รองรับระเบียบไทย (กรมป่าไม้, อบก.)

**LiDAR services ทั่วไป** → ใช้สมการ Chave 2014 pantropical ที่ overestimate ในไม้ไทยเฉพาะ

### 🔗 2. End-to-End Pipeline
- .las → AI segment → QSM → Allometric → **PDF Certificate**
- ลูกค้าเปิด link เดียวจบ ไม่ต้องประกอบ workflow เอง

**LiDAR services ทั่วไป** → ส่งให้แค่ไฟล์ .las แล้วลูกค้าต้องเสียเงินหา consultant ต่อ

### 🏪 3. B2B Marketplace
- ชุมชนผู้ปลูก → list ต้นไม้ที่ verify แล้ว
- โรงงานที่ต้องการ CBAM/ESG offset → browse + checkout
- ระบบจัดการธุรกรรมในแพลตฟอร์มเดียว

**LiDAR services ทั่วไป** → ไม่มี marketplace; ลูกค้าต้องไปหา broker เอง

### 📈 4. Multi-temporal Tracking (Additionality)
- Scan ปีเดียวกัน 2 ครั้ง → คำนวณ **Carbon Delta** = ปริมาณที่เพิ่มขึ้น
- "Additionality" คือสิ่งที่ ESG reporting **บังคับ** ต้องมี — ต้องพิสูจน์ว่าเครดิตที่ขายเป็น "ของใหม่"

**LiDAR services ทั่วไป** → snapshot อันเดียว ไม่มี time-series tracking

### 🛡️ 5. Anti-fraud Verification
- GPS dedup ที่ความละเอียด 6 ทศนิยม (~10 cm)
- EXIF validation บนภาพ mobile
- Audit trail (immutable log) ทุกธุรกรรม
- Manual review โดย Auditor (สำหรับ high-value transactions)

**LiDAR services ทั่วไป** → ข้อมูลดิบ ไม่มี layer ของ trust

---

## 4. Target Users — ใครคือลูกค้าของเรา

### 🥇 Primary — Auditor / Carbon Survey Contractor

**คือใคร:** บริษัทรับทำ carbon survey, นักวิจัยป่าไม้, หน่วยงานเช่น กรมป่าไม้

**ใช้ระบบยังไง:**
1. มี LiDAR scanner อยู่แล้ว (ลงทุนซื้อ TLS 500k-2M หรือ drone LiDAR)
2. Scan ป่าได้ .las/.laz
3. **อัปโหลด .las เข้า CarbonScan AI** → รอ pipeline ประมวลผล
4. ดาวน์โหลด PDF certificate + 3D visualization
5. ส่งให้ลูกค้า (โรงงาน) ที่จ้างทำ

**ทำไมใช้เรา:** ราคา software cheaper than building in-house; certify ในระบบที่ TGO ยอมรับ

### 🥈 Secondary — ชุมชน / เกษตรกรรายย่อย

**คือใคร:** เจ้าของสวนยาง 5 ไร่, หมู่บ้านป่าชุมชน 50 ไร่

**ใช้ระบบยังไง:**
1. ไม่มี LiDAR scanner (แพงเกินไป)
2. **เปิด Mobile app** ของ CarbonScan AI
3. ถ่ายภาพต้นไม้ 30 รูปต่อต้น (สำหรับต้นไม้สำคัญ)
4. ระบบ photogrammetry แปลงเป็น point cloud
5. ผ่าน pipeline เดียวกัน → ได้ certificate
6. List ขายใน marketplace ของเรา → โรงงานซื้อโดยตรง

**ทำไมใช้เรา:** เป็นทางเดียวที่จะเข้าตลาดคาร์บอนได้ ไม่ต้องผ่าน middleman

### 💰 Buyer — Industrial / Corporate

**คือใคร:** โรงงานปูนซีเมนต์, บริษัทพลังงาน, ETS-regulated industries

**ใช้ระบบยังไง:**
1. เปิดเว็บ CarbonScan AI Marketplace
2. Filter: ภูมิภาค, species, ราคา/ตัน CO₂eq, certification status
3. ดู 3D visualization + GIS map ของแปลงที่จะซื้อ
4. กดซื้อ X tCO₂eq → ได้ PDF receipt
5. เก็บไว้ใน ESG report ของตัวเอง

**ทำไมใช้เรา:** transparent (3D evidence + GPS), cheap (no middleman), Thai-localized (ราคาดีกว่าซื้อจาก foreign brokers)

---

## 5. Scope ของโปรเจกต์ NSC 2026

> ⚠️ **อย่าสับสน:** NSC submission ≠ Production product

### สิ่งที่ส่งใน NSC (29 พ.ค. - 17 ก.ค. 2026)

**🟢 ใน scope (ที่ต้องทำให้เสร็จ):**
- ML Pipeline 8 ขั้น (Phase 1: heuristic versions — ทำงานได้)
- Synthetic data generator (สำหรับ test)
- Real data validation (Demol 2021 Belgium dataset)
- Mobile app skeleton (UI 4 screens — ไม่ต้องมี real capture)
- Web landing + auth + dashboard skeleton
- API skeleton with health endpoint
- Allometric calculator (TGO 2017) — เสร็จแล้ว, 16/16 tests pass
- 10+ figures สำหรับ Proposal

**🟡 Sprint 1-7 ก่อน 17 ก.ค.:**
- Real LiDAR upload endpoint + processing
- 3D Point Cloud Viewer (Web) — **Wow Feature #1**
- GIS Map (Leaflet + PostGIS)
- Marketplace UI + mock checkout
- Demo video 3 นาที

**🔴 Post-NSC (ไม่ในนี้):**
- Production deploy ที่ scalable
- Real payment integration
- Mobile photogrammetry full implementation
- PointNet++ deep learning model (Phase 2)
- TGO certification (ต้อง 2-3 ปี)

---

## 6. ทำไมโครงการนี้สำคัญ

### 6.1 Impact ระดับชาติ

ประเทศไทยมี:
- พื้นที่ป่า **~31% ของประเทศ** (~16M เฮกตาร์)
- เกษตรกรรายย่อย **~6M ครัวเรือน**
- ป่าชุมชน **~12,000 แห่ง**

ถ้าระบบ CarbonScan AI ทำงานจริงในระดับชาติ:
- ลดต้นทุนตรวจคาร์บอน **100×** (จาก ฿200k → ฿2k ต่อแปลง)
- เปิดให้เกษตรกร **300,000+ ครัวเรือน** เข้าตลาดคาร์บอนได้
- รัฐเก็บภาษีคาร์บอนได้แม่นยำขึ้น → งบ environment เพิ่ม
- บริษัทไทยส่งออก EU ผ่าน CBAM ได้ราคาคู่ค้าเท่าเทียม

### 6.2 Impact ระดับวิชาการ

- ใช้ techniques ระดับ research (PointNet++, TreeQSM, RANSAC)
- Validate กับ peer-reviewed dataset (Demol 2021)
- **ทีมเรียนรู้** end-to-end software engineering + ML + GIS + business

### 6.3 ผมทำเพื่ออะไร (Personal motivation)

> **"พวกเราชอบป่าไม้และดอกไม้เป็นทุนเดิม" — User, 2026-05-24**

โปรเจกต์นี้ไม่ใช่แค่ NSC contest entry — เป็นโอกาสที่นักศึกษาทีมเล็กๆ จะมีส่วนช่วยแก้ปัญหา climate change ระดับชาติด้วย software

---

## 7. ส่วนประกอบของระบบใน 1 ภาพ

ดู `docs/proposal/figures/fig09_architecture.png` เพื่อภาพรวม 4 layers:

```
[1] INPUT     :  LiDAR Upload (primary) + Mobile (optional)
[2] GATEWAY   :  Web Dashboard ↔ FastAPI Service
[3] PROCESSING:  Supabase + Queue + COLMAP + RunPod GPU
                 + ML Pipeline 8 stages (dashed box)
[4] OUTPUT    :  Certificate (PDF) + Marketplace + GIS+Audit
```

รายละเอียดของแต่ละ box และเหตุผลการเลือก tech อยู่ใน [บท 03 — สถาปัตยกรรมระบบ](03-architecture.md)

---

## 8. ❓ คำถามตรวจสอบความเข้าใจ

> ตอบเองได้ทุกข้อ = เข้าใจบทนี้แล้ว

1. **ทำไม CarbonScan AI ถึงโฟกัสที่ "LiDAR upload" ไม่ใช่ "Mobile scan"?**
   - hint: ดูส่วน 1.3 + 4

2. **5 จุดเด่นของระบบเราที่ LiDAR-only ทำไม่ได้คืออะไร?**
   - ลองนึกออกมา 3-4 ข้อ ก่อนกลับไปดูส่วน 3

3. **"Additionality" ใน carbon market คืออะไร และทำไมสำคัญสำหรับ ESG reporting?**
   - hint: ส่วน 3.4

4. **ใครคือ primary user vs secondary user ของระบบ — และทำไมแบ่งแบบนั้น?**
   - hint: ส่วน 4

5. **ใน NSC submission scope (29 พ.ค. - 17 ก.ค.) เราต้องทำอะไรเสร็จบ้าง?**
   - hint: ส่วน 5

---

## 9. อ่านต่อ

- [บท 02 — แนวคิดพื้นฐาน (LiDAR, Point Cloud, Carbon Credit)](02-core-concepts.md)
- [บท 03 — สถาปัตยกรรมระบบ (4 layers)](03-architecture.md)
- [บท 12 — สูตรคาร์บอน (Allometric) ⭐](12-ml-step8-allometric.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24 | **แก้ไขล่าสุด:** 2026-05-24
