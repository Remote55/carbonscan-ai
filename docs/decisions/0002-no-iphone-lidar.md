# ADR 0002: Pivot Away from iPhone LiDAR (Use Photogrammetry + Public Dataset)

- **Status:** Accepted
- **Date:** 2026-05-20
- **Deciders:** User (Team Lead), Advisor

---

## Context

แผนเดิมของโปรเจกต์คือใช้ **iPhone Pro LiDAR Scanner** ในการสแกนต้นไม้ภาคพื้นเพื่อสร้าง Point Cloud

แต่:
1. **ทีมไม่มี iPhone Pro ที่มี LiDAR** (iPhone 12 Pro+, 13 Pro+, 14 Pro+, 15 Pro+)
2. **อาจารย์ pivot โจทย์** ไปทาง LiDAR Point Cloud processing บน Cloud (ไม่ใช่ Mobile)
3. **iPhone LiDAR ระยะหวังผลเพียง 5 เมตร** — ไม่พอสำหรับต้นไม้สูง 10-20 ม.
4. **ต้นทุนซื้อ iPhone Pro** ~30,000+ บาท เกินงบนักศึกษา

---

## Decision

เราจะ **ไม่พึ่งพา iPhone LiDAR** สำหรับการเก็บข้อมูล Point Cloud

แทนที่ด้วย **dual-input architecture:**
1. **Path A (Primary):** รับไฟล์ `.las/.laz` upload จาก Auditor / Public Dataset
2. **Path B (Mobile):** ใช้กล้องธรรมดามือถือ (Android/iOS) ถ่ายภาพรอบต้นไม้ 30-50 รูป → Photogrammetry (COLMAP/OpenMVS) บน Cloud → output Point Cloud

ดู [ADR 0004 Dual-Input Architecture](0004-dual-input-architecture.md) สำหรับรายละเอียด architecture

---

## Alternatives Considered

### Option A: ใช้ iPhone Pro LiDAR
- ✅ Real-time depth
- ✅ "Cool factor" สำหรับ demo
- ❌ ทีมไม่มี hardware
- ❌ ระยะหวังผลแค่ 5 ม.
- ❌ จำกัด user เฉพาะคน iOS

### Option B: ARCore Depth API (Android เฉพาะรุ่นบน)
- ✅ ทีมอาจมี Android
- ❌ รองรับเฉพาะรุ่นใหม่ (Pixel 4+, Samsung S20+)
- ❌ Accuracy ต่ำกว่า LiDAR
- ❌ ซับซ้อนกว่า photogrammetry

### Option C: Photogrammetry + Public Dataset ✅ chosen
- ✅ ใช้กับมือถือทุกรุ่นได้
- ✅ Public Dataset (NEON) เพียงพอสำหรับ Prototype demo
- ✅ Auditor สามารถ upload ไฟล์ TLS/ALS ที่มีอยู่แล้วได้
- ⚠️ Photogrammetry ใช้เวลาประมวลผล (~3-5 นาที/ต้น)
- ⚠️ Accuracy ต่ำกว่า LiDAR (±5-10 cm vs ±2-3 cm)

### Option D: Monocular Depth Estimation (AI ประมาณ depth จากภาพเดี่ยว)
- ✅ ใช้รูปเดียวก็ได้
- ❌ Accuracy ต่ำมาก ไม่เหมาะกับ DBH precision
- ℹ️ อาจใช้เสริมในอนาคต

---

## Consequences

### Positive
- ✅ ทีมไม่ต้องลงทุนซื้อ hardware แพง
- ✅ Platform เปิดให้ user ทุกแพลตฟอร์ม
- ✅ ตรงกับ pivot ของอาจารย์ (Cloud-based processing)
- ✅ Photogrammetry แม่นพอสำหรับ Prototype NSC (อิงงานวิจัย Liang et al. 2019, Mokros et al. 2021)

### Trade-offs
- ⚠️ Photogrammetry ใช้ GPU time มากกว่า LiDAR direct
- ⚠️ ต้องระบุใน Proposal ชัดเจนว่า "Photogrammetry as a proxy with ±5-10% error margin"
- ⚠️ Live demo ใช้ pre-computed dataset ไม่ใช่ real-time scan

### Neutral
- ℹ️ ในอนาคต ถ้า project ขยาย สามารถเพิ่ม LiDAR support ภายหลังได้ (architecture รองรับอยู่แล้ว)

---

## Implementation Notes

### What Mobile App ส่ง:
- 30-50 photos (multi-angle)
- GPS coordinates (6-decimal)
- Species hint (TFLite on-device classifier)
- Tree metadata (user-provided: estimated height for sanity check)

### What Backend ทำ:
1. รับ photos
2. Queue → Photogrammetry Worker (COLMAP/OpenMVS)
3. Output `.ply` → feed to ML pipeline (same as Path A)

### Validation Plan:
- Calibrate กับ ground truth (สายวัดจริง) ในต้นไม้ตัวอย่าง 20 ต้น
- Report RMSE ใน Proposal: target DBH RMSE ≤ 5 cm

---

## Follow-up Actions

- [x] Update Proposal v1 to mention dual-input
- [ ] Setup COLMAP + OpenMVS Docker image (services/ml/photogrammetry/)
- [ ] Calibration experiment ใน Phase 1
- [ ] Document accuracy table in `docs/ml/PIPELINE.md`

---

## References

- Liang et al. 2019: "Forest in situ observations using unmanned aerial vehicle as an alternative of terrestrial measurements"
- Mokros et al. 2021: "Novel low-cost mobile mapping systems for forest inventories as terrestrial laser scanning alternatives"
- [COLMAP docs](https://colmap.github.io/)
- [OpenMVS GitHub](https://github.com/cdcseacave/openMVS)
- [NEON Data Portal](https://data.neonscience.org/)
