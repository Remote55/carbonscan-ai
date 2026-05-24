# บท 06 — Step 2: Height Normalization (ปรับ Z = 0 บนพื้น)

> 🎯 **เป้าหมาย:** เข้าใจวิธีปรับ Z ของทุกจุดให้เริ่มต้นที่ 0 บนพื้นดิน เพื่อให้ "height-above-ground" ของต้นไม้ทุกต้นเทียบกันได้
> 📚 **พื้นฐาน:** [บท 05 — Ground Classification](05-ml-step1-ground-classification.md)
> ⏱️ **เวลา:** ~15 นาที

---

## 1. ปัญหา

ใน Point Cloud ดิบ Z (ความสูง) เป็น **absolute elevation** เช่น 320.4 m เหนือระดับน้ำทะเล

**ปัญหา:** ต้นไม้ที่อยู่บนเนินกับในที่ราบมี absolute Z ต่างกัน — แม้สูงจริงเท่ากัน!

```
ต้นไม้ A: ฐานที่ Z=300 m, ยอดที่ Z=320 m → สูงจริง 20 m
ต้นไม้ B: ฐานที่ Z=350 m, ยอดที่ Z=375 m → สูงจริง 25 m
```

แต่ถ้าใช้ absolute Z, ต้นไม้ A กับ B อยู่ที่ Z 300-375 → คอมพิวเตอร์งง

**ทางออก:** Normalize Z ให้พื้นดิน = 0 → จุดของต้นไม้ A สูง 0-20m, ต้นไม้ B สูง 0-25m

---

## 2. หลักการ — DTM Subtraction

### 2.1 DTM คืออะไร

**DTM** = **D**igital **T**errain **M**odel = แผนที่ความสูงของพื้นดินเป็น raster

```
DTM = surface ที่ผ่านจุด ground ทั้งหมด
      สำหรับทุก (x, y) ในพื้นที่ → ให้ z_terrain
```

### 2.2 Normalize ยังไง

```
สำหรับทุก point i:
    z_normalized[i] = z[i] - DTM(x_i, y_i)
```

หลังนี้:
- Ground points: z_normalized ≈ 0
- Tree top: z_normalized = ความสูงจริงเหนือพื้น

> 💡 **Analogy:** เหมือนวัดส่วนสูงของคน — ไม่ใช่ระดับเหนือน้ำทะเลของกระหม่อม แต่เป็น "หัวสูงกี่เซนต์เหนือพื้น"

---

## 3. อัลกอริทึม — KD-tree + Inverse Distance Weighting (IDW)

### 3.1 ทำไมไม่ใช้ DTM อย่างตรงๆ

DTM เต็มๆ ต้อง interpolate (เช่น TIN/triangulation) — ช้าและ memory-heavy

**Solution:** ใช้ **KD-tree** หา ground points ที่ **ใกล้ที่สุด** K จุด + interpolate ด้วย IDW

### 3.2 IDW Interpolation

สำหรับ point ที่ต้องการ normalize ที่ตำแหน่ง $(x, y)$:

1. หา **K nearest ground points** (เราใช้ K=8)
2. คำนวณ weighted average ของ Z:

$$
z_{\text{terrain}}(x, y) = \frac{\sum_{i=1}^{K} \frac{z_i}{d_i^p}}{\sum_{i=1}^{K} \frac{1}{d_i^p}}
$$

โดย:
- $d_i$ = ระยะ XY จาก point i ที่ใกล้สุด
- $p$ = power (เราใช้ p=2 = inverse-square)

3. **Normalize:**

$$
z_{\text{normalized}} = z - z_{\text{terrain}}(x, y)
$$

> 💡 **เทคนิค:** Inverse square (p=2) ทำให้จุดที่ใกล้กว่ามีน้ำหนัก **มาก** กว่าจุดที่ไกล — ตามสามัญสำนึก

---

## 4. โค้ดของเรา

📂 **`services/ml/pipeline/height_normalization.py`**

```python
from scipy.spatial import cKDTree

def normalize_height_array(
    points: np.ndarray,
    ground_mask: np.ndarray,
    *,
    k_neighbors: int = 8,
    distance_weight_power: float = 2.0,
) -> np.ndarray:
    """Normalize Z so ground ≈ 0."""

    # 1. Extract ground points
    ground_xy = points[ground_mask, :2]
    ground_z = points[ground_mask, 2]

    # 2. Build KD-tree
    tree = cKDTree(ground_xy)

    # 3. Query K-nearest for all points
    dists, idx = tree.query(points[:, :2], k=k_neighbors)

    # 4. IDW interpolation
    weights = 1.0 / (dists ** distance_weight_power + 1e-9)  # avoid div by 0
    weights /= weights.sum(axis=1, keepdims=True)            # normalize
    terrain_z = np.sum(ground_z[idx] * weights, axis=1)      # weighted avg

    # 5. Subtract
    out = points.copy()
    out[:, 2] = points[:, 2] - terrain_z
    return out
```

### Performance
- 1M points: ~3 seconds (KD-tree query is O(log N) per point)
- 10M points: ~20 seconds

---

## 5. ผลที่ได้

```
Z range (raw):       300.4 → 375.8 m
Z range (normalized):  -0.3 → 22.5 m

Ground point Z stats after normalization:
  mean = +0.05 m   (ใกล้ 0 = ดี)
  std  = 0.18 m    (variation ของพื้นเล็กน้อย OK)
```

---

## 6. ✅ Properties สำคัญ

- ✅ Ground points **mean Z ≈ 0** (ที่ตั้งใจไว้)
- ✅ Tree top Z = ความสูงจริงเหนือพื้น
- ✅ Slope/terrain ถูก "หัก" ออก — ต้นไม้บนเนินกับที่ราบเทียบกันได้
- ⚠️ ถ้า ground classification (Step 1) ผิด — Step 2 จะ propagate error ไปด้วย

---

## 7. Libraries

| Library | Purpose |
|---|---|
| `scipy.spatial.cKDTree` | Fast nearest-neighbor lookup |
| `numpy` | Vectorized arithmetic |

---

## 8. ข้อจำกัด + Phase 2

| ข้อจำกัด | Phase 2 |
|---|---|
| IDW อาจสร้าง artifact ที่ขอบ data | Delaunay triangulation (TIN) |
| K=8 fixed — บางที่ density ต่ำ → ไม่พอ | Adaptive K based on local density |
| ไม่จัดการ multi-layer terrain | (ระบบไม่ต้องการ — ป่าไม่ใช่อาคาร) |

---

## 9. ❓ คำถามตรวจสอบความเข้าใจ

1. **DTM คืออะไร? ทำไม normalize ด้วย DTM?**
2. **ทำไมใช้ IDW ไม่ใช่ average ธรรมดา?**
3. **K=8 นี้คืออะไร? ถ้าตั้ง K=1 จะเกิดอะไรขึ้น?**
4. **หลัง normalize ground points ควรมี Z mean ใกล้เท่าไหร่?**
5. **ถ้า Step 1 (ground classification) ผิด → Step 2 จะเป็นยังไง?**

---

## 10. อ่านต่อ

- [บท 07 — Step 3: Canopy Height Model (CHM)](07-ml-step3-canopy-height-model.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
