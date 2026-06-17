# Thai Field Ground Truth (Sprint P1 / G1)

ข้อมูลภาคสนามสำหรับ validate ระบบกับ **ไม้ไทยจริง** (สัก/ยางนา ฯลฯ) — ปิดช่องว่างที่ตอนนี้ validate แค่ไม้ Belgium

## ขั้นตอนเก็บข้อมูล (ภาคสนาม)

1. เลือกต้นไม้ 5–10 ต้น (เน้นชนิดใน scope: สัก ยางนา ยางพารา มะค่าโมง)
2. วัด **ground truth** ต่อต้น:
   - **DBH** ที่ระดับอก 1.3 ม. — ใช้คาลิปเปอร์ (ใส่ `dbh_cm`) **หรือ** สายวัดเส้นรอบวง (ใส่ `circumference_cm` ระบบหาร π ให้เอง)
   - **ความสูง** — clinometer app (ฟรี) หรือ Vertex (ยืมจากคณะ)
3. **สแกน** ต้นนั้นด้วยมือถือ: ถ่ายรอบต้น 30–50 รูป → COLMAP/OpenMVS → ได้ `.ply`
   (หรือถ้ายืม TLS ได้ = ได้ `.las/.laz` ความแม่นสูงกว่ามาก)
4. ตั้งชื่อไฟล์ point cloud ให้ตรงกับ `point_cloud_file` ใน CSV

## ไฟล์ในโฟลเดอร์นี้

| ไฟล์ | คำอธิบาย | track ใน git? |
|---|---|---|
| `thai_ground_truth_TEMPLATE.csv` | แม่แบบ — คัดลอกแล้วกรอกจริง | ✅ |
| `thai_ground_truth.csv` | ข้อมูลจริงที่กรอก (สร้างเอง) | ❌ (gitignored) |
| `pointclouds/` | ไฟล์ .ply/.las ของแต่ละต้น | ❌ (gitignored — ใหญ่) |

> คอลัมน์: ใส่ **อย่างใดอย่างหนึ่ง** ระหว่าง `dbh_cm` หรือ `circumference_cm` ก็พอ

## รันการ validate

```bash
cd services/ml

# ลองดูก่อนว่าระบบทำงาน (ไม่ต้องมีข้อมูลจริง — ใช้ต้นไม้ synthetic)
./.venv/Scripts/python.exe notebooks/validate_thai.py --demo

# พอเก็บข้อมูลจริงแล้ว
./.venv/Scripts/python.exe notebooks/validate_thai.py \
    --gt-csv data/field/thai_ground_truth.csv \
    --pc-dir data/field/pointclouds
```

**ผลลัพธ์:** `docs/proposal/figures/thai_validation.csv` + `fig16_thai_parity.png` (parity DBH + Height ภาษาไทย) → ใส่ใน Final Report §7.2.5

> หมายเหตุ: photogrammetry มือถือแม่นน้อยกว่า TLS — รายงาน error ตามจริง และเฟรมเป็น "smallholder path" (primary path คือ LiDAR upload)
