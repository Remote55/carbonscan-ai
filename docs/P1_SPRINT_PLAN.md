# Sprint Plan — Phase 1 (P1) สู่ Final Report

> **เป้าหมาย:** ยกระดับจาก "proposal ที่ผ่าน" → "ผลงานที่ชนะ" โดยปิดช่องว่างที่ proposal ยังเป็นแค่ target
> **ช่วงเวลา:** 17 มิ.ย. 2569 → **Final Report deadline 17 ก.ค. 2569** (~4 สัปดาห์)
> **อัปเดต:** 2026-06-17
> **อ้างอิงต่อเนื่อง:** [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) · [SESSION_HANDOFF.md](SESSION_HANDOFF.md) · [proposal/outline.md](../proposal/outline.md)

---

## 0. TL;DR

P1 มี **3 เป้าหมายที่เป็นตัวตัดสินการชนะ** — แต่ละข้อเปลี่ยน "คำสัญญาใน proposal" ให้เป็น "หลักฐานจริงที่กรรมการจับต้องได้":

| # | เป้าหมาย | เปลี่ยนจาก → เป็น | พิสูจน์อะไรต่อกรรมการ |
|---|---|---|---|
| **G1** | Thai ground truth validation | "validate แค่ไม้ Belgium" → "มี parity plot ไม้ไทยจริง" | ระบบใช้ได้กับไม้ไทย ไม่ใช่แค่ทฤษฎีต่างประเทศ |
| **G2** | PointNet++ wood-leaf จริง | "Phase 1 PCA heuristic" → "Deep Learning IoU ≥ 0.70" | จุดขาย "AI/Deep Tech" เป็นของจริง |
| **G3** | TreeQSM volume | "taper error 18.8%" → "< 10%" | ความแม่นยำระดับ research-grade ครบทุก metric |

**งบ:** ใช้ free tier เป็นหลัก (Colab/Kaggle ฟรีสำหรับ train) — ค่าใช้จ่ายเพิ่มเฉพาะค่าเดินทางเก็บข้อมูลภาคสนาม (~1,200 บาท ที่อยู่ในงบแล้ว)

---

## 1. ทีมและกำลังคน (Capacity)

| คน | บทบาทใน P1 | งานหลัก |
|---|---|---|
| **User** (Lead) | ML/Backend | G1 + G2 + G3 (critical path) + integrate pipeline |
| **Person A** | Web | 3D Viewer (Three.js) + GIS Map + เชื่อม API — ทำคู่ขนาน |
| **Person B** | Design | Screenshots, pitch deck draft, video storyboard — ทำคู่ขนาน |

> ⚠️ G1/G2/G3 อยู่บน critical path ของ User คนเดียว — Person A/B ทำงาน parallel ที่ไม่ block กัน

---

## 2. ภาพรวม 4 สัปดาห์ (Sprint Breakdown)

| สัปดาห์ | ช่วง | โฟกัส | Milestone |
|---|---|---|---|
| **S1** | 17–23 มิ.ย. | G1 เก็บข้อมูลภาคสนาม + G2 เตรียม training data | มีข้อมูลไม้ไทย + dataset พร้อม train |
| **S2** | 24–30 มิ.ย. | G2 train PointNet++ + G3 implement TreeQSM | โมเดลผ่าน IoU ≥ 0.70 + volume < 10% |
| **S3** | 1–7 ก.ค. | Integrate G2+G3 เข้า pipeline + รัน Thai validation + Web 3D viewer | pipeline เวอร์ชันสมบูรณ์ + parity plot ไทย |
| **S4** | 8–14 ก.ค. | เขียน Final Report + figures + ทดสอบ end-to-end | ร่าง Final Report เสร็จ |
| buffer | 15–17 ก.ค. | ตรวจ + แก้ + **ส่ง** | ส่ง Final Report (17 ก.ค. 17:00) |

```
        17มิ.ย.   24มิ.ย.    1ก.ค.     8ก.ค.    15ก.ค.
        |────S1────|────S2────|────S3────|────S4────|─buffer─|
G1 Thai  ███████████
G2 PNet++ ████████████████████
G3 QSM             ███████████
Integrate                    ████████████
Web/3D    ████████████████████████████████
Report                                 ██████████████
```

---

## 3. รายละเอียดแต่ละเป้าหมาย

### G1 — Thai Ground Truth Validation ⭐ (ตัวตัดสินที่ทีมอื่นไม่มี)

**ปัญหาที่ปิด:** ตอนนี้ระบบ validate แค่ไม้ Belgium (Fagus/Pinus/...) — ยังไม่มีหลักฐานว่าใช้กับ "สัก/ยางนา" จริงได้ และค่าคาร์บอนของไม้ไทยยังไม่เคยเทียบ ground truth

**แนวทาง (งบต่ำ, ไม่มี TLS):**
1. หาแปลงตัวอย่าง 5–10 ต้น (ในมหาวิทยาลัย / สวนที่เข้าถึงได้ / ขอความช่วยเหลือจากอาจารย์ที่ปรึกษา) — เน้น สัก/ยางนา ที่อยู่ใน scope
2. วัด ground truth ด้วยมือ: **DBH** (สายวัดรอบลำต้นที่ 1.3 ม. → ÷π) + **ความสูง** (clinometer app ฟรี เช่น "Measure Height" หรือยืม Vertex จากคณะ)
3. สแกนด้วย **mobile photogrammetry** (30–50 รูป/ต้น) → COLMAP/OpenMVS → .ply → เข้า pipeline
4. (ถ้าขอ TLS จากอาจารย์/คณะได้ = โบนัสใหญ่ — ความแม่นสูงกว่ามาก)
5. สร้าง `fig16_thai_parity.png` — predicted vs measured (DBH + Height)

**Acceptance Criteria:**
- [ ] วัด ground truth ≥ 5 ต้น (DBH + Height) บันทึกใน CSV
- [ ] รันผ่าน pipeline ได้ครบทุกต้น
- [ ] มี parity plot + รายงาน MAE **อย่างตรงไปตรงมา** (photogrammetry คาดว่า error สูงกว่า TLS — เฟรมเป็น "smallholder path")
- [ ] เพิ่มผลลง Final Report §7.2.5 + ตอบกรรมการได้ว่า "ทดสอบกับไม้ไทยจริงแล้ว"

**ความเสี่ยง:** photogrammetry แม่นยำต่ำ/ล้มเหลวกับใบหนา → mitigation: เก็บหลายต้น, รายงาน confidence, ระบุชัดว่าเป็น secondary path; ถ้าได้ TLS ใช้แทน

**งบ:** ค่าเดินทาง ~1,200 บาท (ในงบแล้ว) · เครื่องมือ: สายวัด (ถูก) + clinometer app (ฟรี)

---

### G2 — PointNet++ Wood-Leaf Segmentation (ทำให้ "AI" เป็นจริง)

**ปัญหาที่ปิด:** จุดขายหลักคือ Deep Learning แต่ Phase 1 ยังเป็น PCA heuristic — ต้องส่งมอบโมเดลจริง

**แนวทาง training data (สำคัญสุด — งบ 0 บาท):**
1. **Synthetic labeled data** จาก `services/ml/pipeline/synthetic.py` — generator สร้างต้นไม้ที่รู้โครงสร้าง → ได้ label wood/leaf ฟรี เป็น training set หลัก
2. **Pseudo-labels** จาก PCA heuristic บน Belgium real clouds — weak supervision เสริม domain จริง
3. **Manual label** 2–3 ต้นจริง (ใน CloudCompare) เป็น **test set** ที่เชื่อถือได้
4. Train **PointNet++** บน Colab/Kaggle **free tier** (T4/P100) → export `.pt`
5. Integrate เป็น Phase 2 path ใน `wood_leaf_separation.py` (มี fallback PCA ถ้าโมเดลไม่โหลด)

**สถานะ scaffold (พร้อมแล้ว — 17 มิ.ย.):** ✅ `services/ml/training/` setup ครบ — `woodleaf_dataset.py` (synthetic→labeled, torch-free), `metrics.py` (IoU), `pointnet2_seg.py` (PointNet++ SSG), `train_woodleaf.py` (Colab CLI), integrate hook ใน `wood_leaf_separation.py` (backend="pointnet" + fallback), 16 tests ผ่าน. **เหลือแค่รัน train จริงบน Colab** (ดู `training/README.md`)

**Acceptance Criteria:**
- [x] Scaffold + dataset + model + train CLI + integration + tests (TDD) ✅
- [ ] รัน train จริงบน Colab → **IoU ≥ 0.70** บน held-out test set
- [ ] เพิ่ม manual-labeled real tree เป็น test set (CloudCompare)
- [ ] ตาราง/รูปเทียบ **PointNet++ vs PCA baseline** (โชว์ว่า DL ดีขึ้นจริง)
- [x] integrate เข้า pipeline + unit test ผ่าน (41/41, ไม่ break ของเดิม) ✅

**ความเสี่ยง:** train ไม่ทัน/IoU ไม่ถึง → mitigation: PCA fallback ยัง functional (proposal เขียนไว้แล้วว่า DL เป็น enhancement); ตั้ง checkpoint กลาง S2 ถ้าไม่เวิร์คให้ลด scope เป็น "เทรนได้ + รายงานผลเบื้องต้น"

**งบ:** 0 บาท (free GPU)

---

### G3 — TreeQSM Volume (ปิด metric สุดท้าย)

**ปัญหาที่ปิด:** Volume error 18.8% สูงกว่า DBH/Height มาก เพราะใช้ taper equation แบบ approximation

**สถานะ (17 มิ.ย.) — มี finding สำคัญ:** ✅ implement `estimate_volume_sectional` (stacked-cylinder, TreeQSM-style) ใน `qsm.py` + 5 unit tests ผ่าน (recover ปริมาตร cylinder/cone จริงได้ และชนะ taper บน cone สะอาด) **แต่** รันบน Belgium จริงได้ **volume error +896%** (จาก 18.8% เดิม) — แย่ลงมาก เพราะ wood/leaf PCA ยังเหลือจุดเรือนยอด พอ slice แล้ว fit วงกลมต่อชั้นไปจับ "ก้อนกิ่ง" รัศมีใหญ่ทุกชั้น

**บทเรียน:** sectional QSM ต้องการ **wood points สะอาด (ขึ้นกับ G2 PointNet++)** + การ model กิ่งจริง ถึงจะชนะ taper → จึง **คง taper เป็น default (18.8%) ไม่ ship regression**; เก็บ `estimate_volume_sectional` เป็น utility ที่ test แล้ว พร้อมใช้เมื่อ G2 ให้ wood สะอาด

**✅ สถานะ (18 มิ.ย.) — hypothesis ทดสอบแล้ว/ปิดคำถาม:** หลัง G2 เทรน PointNet++ เสร็จ (IoU 0.96–0.98) รัน experiment ([`notebooks/experiment_g3_pointnet_volume.py`](../services/ml/notebooks/experiment_g3_pointnet_volume.py)) ใช้ **PointNet++ wood (สะอาด) + sectional** บน Belgium 65 ต้น → ยังได้ **373.6% (median 144%)** แย่กว่า taper 23.4% เหมือนเดิม
> **ข้อสรุปจริง:** ปัญหา **ไม่ใช่** คุณภาพ wood (clean แล้วยังพัง) — แต่เป็น **ตัว algorithm**: การ slice แนวนอนแล้ว fit วงกลมต่อชั้น มันจับ "การกระจายของกิ่ง" (กิ่ง = wood จริง แต่แผ่กว้าง) → overestimate ทุกชั้น (ncyl 47–82). **TreeQSM จริงต้อง fit ทรงกระบอกตาม "แกนกิ่ง" (branch-axis + cover sets) ไม่ใช่ slice แนวนอน** → เป็นงานใหญ่ เกิน scope prototype NSC

**Acceptance Criteria:**
- [x] implement sectional cylinder volume + unit tests (ถูกต้องบน stem สะอาด) ✅
- [x] วัดผลจริงบน Belgium (PCA wood) → finding: +896% ✅
- [x] **ทดสอบ PointNet++ clean wood + sectional → 373.6% (ยังแพ้ taper)** → hypothesis disproven ✅
- [x] **ข้อสรุป: คง taper 18.8% (ใน TLS literature range 10–20%)** — full TreeQSM เป็น future work ✅

**ความเสี่ยง:** หมดแล้ว — ปิดคำถามชัดเจนว่า height-sliced sectional ใช้กับต้นไม้มีกิ่งไม่ได้ (ไม่ว่า wood สะอาดแค่ไหน); taper เป็นคำตอบที่ถูกต้องสำหรับ prototype, รายงานตามจริง — ไม่ overclaim

**งบ:** 0 บาท (CPU)

---

## 4. งานคู่ขนาน (Person A / Person B — ไม่ block critical path)

| คน | งาน | Deadline | ทำไมสำคัญ |
|---|---|---|---|
| Person A | 3D Point Cloud Viewer (Three.js + R3F) แสดงสี wood/leaf/ground | S3 | **Hero demo** รอบ pitching |
| Person A | GIS Map (Leaflet) + เชื่อม `/trees` API | S3 | โชว์ provenance ต้นไม้ |
| Person B | ถ่าย screenshots Web + Mobile (ชุดใหม่) | S2 | ใส่ Final Report Appendix D |
| Person B | ร่าง pitch deck + video storyboard | S4 | เตรียมรอบ pitching (ส.ค.) |

---

## 5. งานขัดเงาเอกสาร (เก็บตกจากการ review)

- [ ] อัปเดต [ARCHITECTURE.md](ARCHITECTURE.md) ให้ตรงของจริง — ลบ "NextAuth" (ใช้ Supabase Auth), "Celery" (ใช้ PGMQ), เรียงลำดับ pipeline ให้ตรง 8 ขั้น
- [ ] สร้างตาราง `audit_log` จริงใน DB (mark Phase 2 ใน proposal แล้ว) + RLS policy
- [ ] sync species_db note ใน HANDOFF/SESSION_HANDOFF (ค่า a/b/c เก่า) ให้ตรง CSV
- [ ] ตรวจ DOI/URL ทุกตัวใน references ว่า active (ตาม checklist references.md)

---

## 6. Definition of Done (Final Report พร้อมส่ง)

- [ ] G1: Thai parity plot + ตัวเลข MAE จริง ใน §7.2.5
- [ ] G2: PointNet++ IoU ≥ 0.70 + เทียบ baseline ใน §7.2.2
- [ ] G3: Volume MAE < 10% (หรือ improvement ที่รายงานได้)
- [ ] ระบบรัน end-to-end ได้ (อัปโหลด → ผลคาร์บอน) — มี demo video
- [ ] Final Report ครบทุกหัวข้อ NSC template + figures fig01–16
- [ ] tests ทั้งหมดผ่าน (ไม่ break ของเดิม)
- [ ] commit + tag + push ก่อน deadline ≥ 24 ชม.

---

## 7. Cadence (จังหวะการทำงาน)

- **Daily:** stand-up สั้นใน Line/Discord — "เมื่อวานทำอะไร / วันนี้ทำอะไร / ติดอะไร"
- **กลาง S2 (27 มิ.ย.):** checkpoint G2 — ถ้า PointNet++ ส่อแววไม่ทัน → ตัดสินใจ scope ลง
- **สิ้นแต่ละ Sprint:** demo สั้น + อัปเดต checklist นี้
- **10 ก.ค.:** freeze feature — เหลือแต่เขียน report + แก้บั๊ก
