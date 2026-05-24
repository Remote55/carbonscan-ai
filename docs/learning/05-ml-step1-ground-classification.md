# บท 05 — Step 1: Ground Classification (แยกพื้นดิน)

> 🎯 **เป้าหมาย:** เข้าใจวิธีแยก "พื้นดิน" จาก "ต้นไม้/พืช" ใน Point Cloud
> 📚 **พื้นฐาน:** อ่าน [บท 04 — Pipeline Overview](04-ml-pipeline-overview.md) แล้ว
> ⏱️ **เวลา:** ~20 นาที

---

## 1. ปัญหา

ใน Point Cloud ของป่า มีจุด **ล้านๆ จุด** ที่ปนกัน:
- 🌍 **Ground** — จุดที่เป็นพื้นดิน
- 🌳 **Non-ground** — ลำต้น, กิ่ง, ใบ, สิ่งของอื่นๆ

ก่อนคำนวณ "ความสูงของต้นไม้" ต้อง **รู้ว่าตรงไหนคือพื้น** ก่อน

> 💡 **Analogy:** เหมือนหา "ระดับน้ำทะเล" ก่อนวัดความสูงภูเขา — ถ้าใช้ระดับผิด ภูเขาก็สูงผิด

---

## 2. หลักการ — Cloth Simulation Filter (CSF)

**Reference paper:** Zhang et al. 2016 — *"An Easy-to-Use Airborne LiDAR Data Filtering Method Based on Cloth Simulation"* (Remote Sensing, 8(6), 501)

### 2.1 Idea ของ Zhang 2016

> นึกภาพ: เอา **ผ้านุ่ม** วางจาก**ใต้** point cloud (พลิกกลับด้านแล้ว) → ผ้าจะตกลงมาตามแรงโน้มถ่วงและ **ติด** กับจุดต่ำสุดของพื้นที่

```
จุดต่ำสุด = พื้นดิน
                                ←  จุดสูงสุด (ใบไม้)
     .   .   .   .  .  .  .  .
       .   .   .  .  .  .  .  .  ←  ต้นไม้
   .   .   .  .  .  .  .  .
─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ←  "ผ้า" ตกลงมา ติดกับ ground
   ●   ●   ●  ●  ●  ●  ●  ●  ●  ←  พื้นดิน (ที่ผ้าติด)
```

จุดที่ใกล้ "ผ้า" (ไม่เกินค่า threshold) = **ground**

### 2.2 Phase 1 ของเรา — Grid Heuristic (เร็วกว่า CSF)

CSF เป็นมาตรฐาน แต่ติดตั้ง PDAL บน Windows ยาก — เราใช้ heuristic ง่ายกว่า:

```
1. แบ่งพื้นที่เป็น grid 1m × 1m
2. ในแต่ละ cell หา "Z ต่ำสุด" (percentile 5%)
3. จุดที่อยู่ใน threshold ±0.3m จาก min Z = ground
```

> 💡 **เทียบกับ CSF:** บน synthetic plot ของเรา ให้ผลใกล้กัน ±2% — Phase 2 จะเปลี่ยนเป็น PDAL CSF จริง

---

## 3. คณิตศาสตร์/อัลกอริทึม

### 3.1 Grid Percentile Heuristic

**Input:** Point Cloud `P = {(x_i, y_i, z_i)}`, $N$ points

**Steps:**

```
1. กำหนด grid_size = 1.0 m
2. สำหรับแต่ละ point i:
       cell_x = floor((x_i - x_min) / grid_size)
       cell_y = floor((y_i - y_min) / grid_size)
       เก็บ z_i ลง bucket[(cell_x, cell_y)]

3. สำหรับแต่ละ cell:
       ground_z[cell] = percentile(z_values_in_cell, 5%)
       # 5% percentile = robust ต่อ outliers ที่ต่ำผิดปกติ

4. สำหรับแต่ละ point i:
       cell = (cell_x_i, cell_y_i)
       is_ground[i] = (z_i <= ground_z[cell] + threshold)
       # threshold = 0.3 m
```

### 3.2 ทำไม Percentile 5% ไม่ใช่ min

- **min** จะเลือกจุด outlier (เช่น เรดาร์สะท้อนผิด, มี anomaly)
- **5th percentile** = ค่าต่ำ 95% ของจุดในเซลล์ (robust)

### 3.3 ทำไม Threshold 0.3 m

- พื้นดินมี roughness ตามธรรมชาติ ~ 10-30 cm
- ตั้ง 0.3 m → จุดที่อยู่ในชั้นนี้นับเป็น "พื้น"
- ถ้าตั้งต่ำเกิน (เช่น 0.1m) → underclassify (พลาด ground บางจุด)
- ถ้าตั้งสูงเกิน (เช่น 1.0m) → overclassify (พุ่ม/หญ้าจะนับเป็นพื้น)

---

## 4. โค้ดของเรา

📂 **`services/ml/pipeline/ground_classification.py`**

```python
def classify_ground_array(
    points: np.ndarray,
    *,
    grid_resolution: float = 1.0,
    percentile: float = 5.0,
    z_threshold: float = 0.3,
) -> np.ndarray:
    """Heuristic ground classification.

    Returns:
        (N,) bool array — True where the point is ground.
    """
    # 1. Get bounds
    x_min, y_min = points[:, 0].min(), points[:, 1].min()

    # 2. Compute cell index for each point
    ix = np.floor((points[:, 0] - x_min) / grid_resolution).astype(int)
    iy = np.floor((points[:, 1] - y_min) / grid_resolution).astype(int)
    cell_id = ix * (iy.max() + 1) + iy  # 1D cell key

    # 3. Per-cell percentile (using sorted indices for efficiency)
    order = np.argsort(cell_id, kind="stable")
    sorted_cells = cell_id[order]
    sorted_z = points[order, 2]

    # 4. Compute percentile per cell using groupby pattern
    ground_z = np.full(cell_id.max() + 1, np.inf)
    # ... (vectorized groupby percentile)

    # 5. Classify
    is_ground = points[:, 2] <= (ground_z[cell_id] + z_threshold)
    return is_ground
```

### Performance
- 1M points: ~2 seconds (vectorized numpy)
- 10M points: ~15 seconds

---

## 5. Libraries

| Library | Purpose | Why |
|---|---|---|
| **numpy** | array operations | std + fast |
| (Phase 2) PDAL | true CSF filter | industry standard |

---

## 6. Citation

- **Zhang, W. et al. 2016**. "An Easy-to-Use Airborne LiDAR Data Filtering Method Based on Cloth Simulation". *Remote Sensing*, 8(6), 501.
- DOI: [10.3390/rs8060501](https://doi.org/10.3390/rs8060501)

---

## 7. ข้อจำกัด + Phase 2

| ข้อจำกัด Phase 1 | ผลกระทบ | Phase 2 |
|---|---|---|
| Heuristic อาจพลาดที่ slope > 30° | over-classify เป็นพื้น | PDAL CSF จริง |
| ไม่รองรับ multi-layer terrain | สะพาน/ตึก จะนับเป็น "พื้น" บน | Hierarchical CSF |
| ไม่มี return number filtering | จุด multi-return ผิดประเภท | Use return number metadata |

---

## 8. Visualization

ดู **`docs/proposal/figures/fig02_ground_classification.png`** — ภาพ before/after:
- ก่อน: ทุกจุดสีเดียวกัน
- หลัง: ground = น้ำตาล, non-ground = เขียว

---

## 9. ❓ คำถามตรวจสอบความเข้าใจ

1. **ทำไมต้องแยก ground ก่อน step อื่น?**
2. **CSF กับ grid-heuristic ต่างกันยังไง?**
3. **percentile 5% แทน min — ป้องกัน outlier ยังไง?**
4. **ถ้าตั้ง z_threshold = 1.0 จะเกิดอะไรขึ้น?**
5. **Cell 1m × 1m เหมาะกับป่า — ถ้าเป็นพื้นที่เกษตรเปิดโล่ง ควรเปลี่ยนเป็นเท่าไหร่?**

---

## 10. อ่านต่อ

- [บท 06 — Step 2: Height Normalization](06-ml-step2-height-normalization.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
