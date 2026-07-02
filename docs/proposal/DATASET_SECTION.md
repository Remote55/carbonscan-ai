# ชุดข้อมูลและการแบ่งข้อมูล (Dataset & Split) — สำหรับรายงานรอบ 2 (ส่ง 17 ก.ค.)

> ตอบ comment กรรมการ #1 (อ้าง dataset ให้ชัด) + คำขออาจารย์ (จำนวน + split train/valid/test)
> **ก็อปย่อหน้าด้านล่างลงรายงานได้เลย** (ปรับสำนวนตามเล่ม)

---

## ⚠️ จุดสำคัญที่ต้องเข้าใจก่อน (กัน framing ผิด)
โปรเจคใช้ข้อมูล **3 ชุด คนละบทบาท** — ส่วนใหญ่เป็น **point cloud ไม่ใช่ "ภาพถ่าย"** มีแค่ smallholder path ที่เป็นรูปถ่าย ต้องแยกให้ชัดในรายงาน ไม่งั้นกรรมการสับสน

---

## ข้อความพร้อมใช้ (paste ลงรายงาน)

**ชุดข้อมูลและการแบ่งข้อมูล**

ระบบใช้ข้อมูลสามชุดตามบทบาทการทำงาน ดังนี้

**1) ชุดข้อมูลตรวจสอบความแม่นยำหลัก (ข้อมูลจริง + เฉลยจากการโค่นจริง):**
ใช้ชุดข้อมูลเปิด **Demol et al. (2021)** ซึ่งเป็น Terrestrial Laser Scanning (TLS) point cloud ของต้นไม้ **65 ต้น จาก 4 ชนิด** (ดึงจำนวนจากไฟล์เฉลยจริง `Destructive_and_qsm_data_DEMOL.csv`) ได้แก่ Fagus sylvatica (15 ต้น), Pinus sylvestris (30 ต้น จาก 2 พื้นที่), Fraxinus excelsior (15 ต้น), และ Larix decidua (5 ต้น) — รวม 65 ต้น แต่ละต้นมีความหนาแน่นประมาณ 85,000–380,000 จุด พร้อม **เฉลยจากการตัดโค่นและชั่งจริง (destructive sampling)** ทั้งค่า DBH ความสูง ปริมาตร และมวล

การแบ่งข้อมูล: ใช้ทั้ง **65 ต้นเป็นชุดทดสอบ (test/validation) ทั้งหมด (100%)** โดย **ไม่ได้นำมาฝึกโมเดล** — จึงเป็นการทดสอบกับข้อมูลจริงที่โมเดลไม่เคยเห็น (independent test) ผลที่ได้: DBH MAE = 1.17 ซม., Tree Height MAE = 0.54 ม. ซึ่งอยู่ในมาตรฐานงานวิจัย TLS forestry

> **แหล่งอ้างอิง:** Demol, M., Verbeeck, H., Gielen, B., et al. (2021). *Trees*, 35, 671–685. DOI: 10.1007/s00468-020-02067-7 — ชุดข้อมูล: Zenodo DOI 10.5281/zenodo.4557401 (https://zenodo.org/records/4557401)

**2) ชุดข้อมูลฝึกแบบจำลอง Wood-Leaf Segmentation (PointNet++):**
ฝึกบน **point cloud สังเคราะห์ (synthetic)** ที่สร้างจากตัวกำเนิดของระบบ ซึ่งทราบป้ายกำกับ (label) ราย point ว่าเป็นลำต้น/ใบ/พื้นดิน แบ่งข้อมูลเป็น:

| ชุด | จำนวน (ต้น) | สัดส่วน |
|---|---|---|
| Train | 256 | 81% |
| Validation | 48 | 15% |
| Test (held-out) | 12 | 4% |
| **รวม** | **316** | 100% |

(seed คนละชุดกัน ไม่ทับซ้อน) ผล: PointNet++ ได้ Wood IoU = **0.978** เทียบกับวิธี PCA heuristic 0.769 (+0.208, ชนะทุกต้นในชุดทดสอบ)

> หมายเหตุ: IoU 0.978 นี้วัดบน **ชุดทดสอบ synthetic** — พิสูจน์ว่าสถาปัตยกรรมและวิธีฝึกถูกต้องและชนะ baseline (ไม่ใช่ตัวเลขความแม่นบนไม้จริง — ดูข้อ 2.1)

**2.1) การทดสอบ Wood-Leaf บนไม้จริง (Wan et al. 2021) — sim-to-real gap และการปิดช่องว่างด้วยการเทรนบนไม้จริง**

เพื่อประเมินการใช้งานกับไม้จริง ได้ทดสอบโมเดลกับชุดข้อมูลเปิด **Wan et al. (2021)** ซึ่งเป็น TLS point cloud ของไม้ **73 ต้น 3 ชนิด** (*Betula papyrifera*, *Larix gmelinii*, *Styphnolobium japonicum*) พร้อม **เฉลย wood/leaf ราย point ที่ติดป้ายด้วยมือ** การแบ่งข้อมูลใช้ **การตัดเชิงพื้นที่ (spatial held-out) พร้อมแถบกันชน (buffer)** เพื่อให้ชุดทดสอบเป็นบริเวณ/ต้นที่โมเดลไม่เคยเห็น (กันข้อมูลรั่วข้าม train/test)

| วิธี | Wood IoU | Leaf IoU | Mean IoU |
|---|---|---|---|
| PCA heuristic (zero-shot) | – | – | ~0.25 |
| PointNet++ ฝึก synthetic แล้วทดสอบไม้จริง (zero-shot) | 0.18 | 0.62 | 0.33 |
| **PointNet++ เทรนบนไม้จริงโดยตรง + augment synthetic** | **0.42** | **0.81** | **0.61** |
| *(อ้างอิง) PointNet++ บนชุดทดสอบ synthetic* | *0.978* | – | – |

การทดลองเปรียบเทียบ 4 เงื่อนไข (เทรนจากศูนย์บนไม้จริง): การ **augment ด้วย synthetic** ยก Wood IoU จาก 0.29 → 0.42; ส่วน class-weight ช่วยเฉพาะตอนไม่ได้ augment (บันทึกครบทุกเงื่อนไขใน `docs/ml/WOODLEAF_RESULTS.md`)

**ข้อค้นพบ (honest):** มี **ช่องว่าง synthetic→ไม้จริง (sim-to-real gap) ที่ชัดเจน** — โมเดลที่ฝึก synthetic ล้วนแล้วนำไปทดสอบไม้จริงแบบ zero-shot ทำได้เพียง Mean IoU 0.33 **แต่เมื่อเทรนบนไม้จริงโดยตรง (environment เดียวกัน) + augment ด้วย synthetic ช่องว่างแคบลงมาก: Mean IoU 0.33 → 0.61 และ Wood IoU 0.19 → 0.42** (เกินเท่าตัว) — ยืนยันว่าสถาปัตยกรรมเรียนรู้ไม้จริงได้เมื่อมี label จริง Wood IoU ที่ยังไม่ถึงเป้า 0.70 คือช่องว่างที่เหลือ ซึ่งปิดได้ด้วยการเก็บ **ข้อมูลไม้ไทยภาคสนามที่ติดป้ายเพิ่ม** (แผนขั้นถัดไป)

> การรายงานทั้งเส้นทาง (synthetic 0.978 → zero-shot 0.33 → เทรนบนไม้จริง 0.61) อย่างตรงไปตรงมา สะท้อนความเข้มงวดเชิงวิธีวิจัย: ทดสอบกับข้อมูลจริงอิสระ → วัดข้อจำกัดอย่างซื่อสัตย์ → แก้ด้วยการเทรน same-environment → มีแผนปิดช่องว่างที่ชัดเจน
>
> **แหล่งอ้างอิง (Wood-Leaf ไม้จริง):** Wan, P., Zhang, W., Jin, S. (2021). *Plot-level wood-leaf separation for TLS point clouds*. Dryad, DOI: 10.5061/dryad.rfj6q5799 (CC-BY)

**3) ชุดข้อมูล Photogrammetry (เส้นทาง smallholder, Phase 3):**
ภาพถ่ายจากมือถือ **30–50 รูป/ต้น** เดินถ่ายรอบต้น แปลงเป็น point cloud ด้วย COLMAP + OpenMVS แล้วเข้า pipeline เดียวกัน (อยู่ระหว่างเก็บข้อมูลภาคสนามไม้ไทย)

---

## สรุปคำตอบให้อาจารย์
- **อ้าง dataset ชัด:** Demol et al. 2021 (Zenodo 10.5281/zenodo.4557401) + Wan et al. 2021 (Dryad 10.5061/dryad.rfj6q5799) ✅
- **จำนวน:** Belgium 65 ต้น (TLS, validate DBH/สูง/ปริมาตร); synthetic 316 ต้น (ฝึก wood-leaf); Wan 73 ต้น (test wood-leaf ไม้จริง); photogrammetry 30–50 รูป/ต้น
- **Split:** Belgium = test 100% (ไม่เทรน); synthetic = Train 256 / Val 48 / Test 12 (81/15/4%); Wan = spatial held-out + buffer (กันรั่ว)
- **ชี้แจงเพิ่ม:** ข้อมูลหลักเป็น point cloud (TLS + synthetic) ไม่ใช่ภาพถ่าย; "รูป 30–50 ใบ/ต้น" คือ photogrammetry path เท่านั้น
- **honest finding:** wood-leaf IoU บน synthetic = 0.978 แต่บนไม้จริง (zero-shot) ~0.33 → มี sim-to-real gap; แผนปิด = เก็บ field data ไทย + ติดป้าย + fine-tune (Phase ถัดไป)

> **ทิศทางที่ชัวร์สุดเพื่อความแม่นบนไม้จริง:** เก็บ Thai field data (รูป 30–50 ใบ/ต้น → point cloud) + ติดป้าย wood/leaf ด้วยมือใน CloudCompare 5–10 ต้น/ชนิด + วัด DBH/ความสูงภาคสนาม แล้ว fine-tune (ดู `docs/ml/FINETUNE_REALDATA.md`)
