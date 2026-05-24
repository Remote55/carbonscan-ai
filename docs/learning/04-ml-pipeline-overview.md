# บท 04 — ภาพรวม ML Pipeline 8 ขั้น

> 🎯 **เป้าหมายของบท:** ผู้อ่านจะเข้าใจ flow ของ ML pipeline ทั้งหมด — input คืออะไร, แต่ละขั้นทำอะไร, output ออกมาเป็นยังไง
> 📚 **ความรู้พื้นฐาน:** อ่าน [บท 02 — Core Concepts](02-core-concepts.md) และ [บท 03 — Architecture](03-architecture.md) แล้ว
> ⏱️ **เวลา:** ~15 นาที (บทนี้เป็น "แผนที่" ก่อนเข้าบทละเอียด 05-12)

---

## 1. Pipeline ในภาพเดียว

```
INPUT: Point Cloud (.las / .laz / .ply)
       ~1-10 ล้านจุดของแปลงป่า
       │
       ▼
┌──────────────────────────────────────────────────┐
│ Step 1: Ground Classification                    │
│ ────────────────────────────────────────────────│
│ แยก "พื้นดิน" (น้ำตาล) จาก "พืช" (เขียว)         │
│ algorithm: CSF / grid-percentile heuristic       │
│ → output: each point labelled ground / non-ground│
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ Step 2: Height Normalization                     │
│ ────────────────────────────────────────────────│
│ ปรับ Z ให้พื้นดิน = 0 (subtract DTM)             │
│ algorithm: KD-tree + IDW interpolation            │
│ → output: Z normalized = height-above-ground     │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ Step 3: Canopy Height Model (CHM)                │
│ ────────────────────────────────────────────────│
│ Rasterize เป็น 2D grid: แต่ละ cell = max Z       │
│ algorithm: Max-Z + morphological closing         │
│ → output: 2D float array (H × W)                 │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ Step 4: Individual Tree Detection (ITD)          │
│ ────────────────────────────────────────────────│
│ แยกต้นไม้ทีละต้นจาก CHM                          │
│ algorithm: Watershed segmentation                 │
│ → output: per-point tree_id (1..N)               │
└──────────────────────┬───────────────────────────┘
                       ▼ (for each tree)
┌──────────────────────────────────────────────────┐
│ Step 5: Wood/Leaf Separation                     │
│ ────────────────────────────────────────────────│
│ แยกลำต้น/กิ่ง (wood) จาก ใบ (leaf)               │
│ algorithm: Local PCA eigenvalues / PointNet++    │
│ → output: per-point class (wood / leaf)          │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ Step 6: Quantitative Structure Model (QSM)       │
│ ────────────────────────────────────────────────│
│ วัด DBH, Height, Volume จาก wood points          │
│ algorithm: RANSAC circle + taper equation        │
│ → output: per-tree {DBH, H, V}                   │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ Step 7: Species Classification                   │
│ ────────────────────────────────────────────────│
│ จำแนกชนิดต้นไม้จากภาพ RGB                        │
│ algorithm: ResNet-50 transfer learning           │
│ → output: per-tree species (top-1 prediction)    │
└──────────────────────┬───────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────┐
│ Step 8: Allometric Carbon Calculation            │
│ ────────────────────────────────────────────────│
│ DBH + H + Species → Carbon kg → CO₂eq kg         │
│ algorithm: TGO 2017 + Chave 2014 + IPCC 2006     │
│ → output: per-tree carbon + plot total           │
└──────────────────────┬───────────────────────────┘
                       ▼
OUTPUT: JSON + PDF Certificate + Marketplace listing
```

---

## 2. ทำไมต้องมีถึง 8 ขั้น

อาจดูยุ่งยาก แต่ตัด step ไหนออกก็เสีย accuracy ใหญ่:

| ถ้าตัด step นี้ | ปัญหาที่เกิด |
|---|---|
| ไม่มี Ground Classification | ไม่รู้ว่า "ดิน" หรือ "ต้นไม้" → คาร์บอนผิดทั้งหมด |
| ไม่มี Height Normalization | ต้นไม้บนเนินจะดูสูงกว่าจริง |
| ไม่มี CHM | ไม่สามารถใช้ image processing techniques ในขั้นต่อไป |
| ไม่มี Tree Segmentation | นับทั้งแปลงเป็นต้นเดียว → คาร์บอนรวมผิด |
| ไม่มี Wood/Leaf Separation | DBH วัดบนใบ → ผิดมาก |
| ไม่มี QSM | ไม่มีตัวเลข dimensions ของต้น |
| ไม่มี Species Classification | ต้องใช้ Chave generic — error สูง ~15% |
| ไม่มี Allometric | ได้แค่ขนาด ไม่ใช่ carbon |

---

## 3. Pipeline Status Today (24 พ.ค. 2026)

| Step | File | Status | Tests |
|---|---|---|---|
| 1 Ground | `ground_classification.py` | 🟢 Phase 1 heuristic | ✅ |
| 2 Normalize | `height_normalization.py` | 🟢 Phase 1 | ✅ |
| 3 CHM | `canopy_height_model.py` | 🟢 Phase 1 | ✅ |
| 4 Tree Seg | `tree_segmentation.py` | 🟢 Phase 1 watershed | ✅ |
| 5 Wood/Leaf | `wood_leaf_separation.py` | 🟢 Rule-based (PointNet++ Phase 2) | ✅ |
| 6 QSM | `qsm.py` | 🟢 Phase 1 RANSAC + taper | ✅ |
| 7 Species | `species_classifier.py` | 🟡 Stub (Phase 2 ResNet) | - |
| 8 Allometric | `allometric.py` | 🟢 Full implementation | ✅ 16/16 |

> 💡 **โน้ตสำคัญ:** Step 5-6 มี Phase 1 implementation (heuristic) — รันจริง วัดผลแม่นยำ ~6% ใน Belgium dataset

---

## 4. Runtime Budget

จาก benchmark บน RunPod A10G GPU:

| Step | Per plot (0.1 ha) | Per tree | Total in 0.1 ha (5-10 trees) |
|---|---|---|---|
| 1 Ground | 30 sec | - | 30 sec |
| 2 Normalize | 30 sec | - | 30 sec |
| 3 CHM | 1 min | - | 1 min |
| 4 Tree Seg | 10 sec | - | 10 sec |
| 5 Wood/Leaf | - | 5 sec | 25-50 sec |
| 6 QSM | - | 2 sec | 10-20 sec |
| 7 Species | - | 1 sec | 5-10 sec |
| 8 Allometric | - | <1 ms | <1 sec |
| **Total** | | | **~3-4 min** |

ที่ scale ใหญ่ขึ้น (1 ไร่ × 50-100 ต้น):
- ~10-15 นาที per ไร่

---

## 5. ทำไม Order สำคัญ

แต่ละ step ต้องอาศัย output ของ step ก่อนหน้า — ลำดับเปลี่ยนไม่ได้:

```
Tree segmentation ต้องการ CHM (Step 3)
CHM ต้องการ Z normalized (Step 2)
Z normalized ต้องการ ground points (Step 1)
                  ↑
              ขั้นแรกของทั้งหมด
```

```
Wood/Leaf separation ต้องการ per-tree point cloud (Step 4)
QSM ต้องการ wood points (Step 5)
Allometric ต้องการ DBH + Height + Species (Step 6 + 7)
```

---

## 6. Errors Compound

> ⚠️ **สำคัญ:** error ของ step ก่อนหน้า **สะสมไป step ถัดไป**

ตัวอย่าง:
```
Step 1 ground error 5% → Step 2 normalize error 5%
Step 4 over-segment 10% → Step 6 measure wrong tree → DBH error 15%
Step 8 input DBH error 15% → Carbon error ~30% (เพราะ DBH²)
```

**เคล็ดลับ:** ปรับ Step 1-4 ให้แม่นยำดีกว่า optimize Step 5-7 — เพราะ error early stages คูณกันไปเรื่อยๆ

---

## 7. Pipeline ทั้งหมดในโค้ด

📂 **`services/ml/pipeline/main.py`** (entry point)

```python
def process_point_cloud(input_path, output_path=None):
    # 1. Load
    cloud = load_las(input_path)

    # 2. Steps 1-4 (plot-level)
    ground_mask = ground_classification.classify_ground_array(cloud)
    normalized = height_normalization.normalize_height_array(cloud, ground_mask)
    chm, transform = canopy_height_model.compute_chm_array(normalized)
    tree_labels = tree_segmentation.watershed_segmentation(chm)
    tree_clouds = tree_segmentation.extract_tree_points(normalized, tree_labels)

    # 3. Steps 5-8 (per tree)
    results = []
    for tree_id, pts in tree_clouds.items():
        wood_mask = wood_leaf_separation.segment_wood_leaf(pts)
        wood_pts = pts[wood_mask == WOOD]
        qsm_result = qsm.compute_qsm(wood_pts)
        species = species_classifier.predict(...)  # Phase 2
        carbon = allometric.calculate_carbon(
            qsm_result.dbh_cm, qsm_result.height_m, species
        )
        results.append({
            "tree_id": tree_id,
            "dbh_cm": qsm_result.dbh_cm,
            ...
            "carbon_kg": carbon.carbon_kg,
            "co2eq_kg": carbon.co2eq_kg,
        })

    return PipelineResult(trees=results, ...)
```

---

## 8. ❓ คำถามตรวจสอบความเข้าใจ

1. **ทำไม Step 2 (Normalize) ต้องทำหลัง Step 1 (Ground)?**

2. **ระหว่าง Step 1-4 เป็น "plot-level" และ Step 5-8 เป็น "per-tree" — หมายความว่ายังไง?**

3. **CHM (Step 3) เป็น 2D หรือ 3D? ทำไม?**

4. **Step 7 (Species) Phase 1 ของเราใช้ Mock/Stub — แล้ว Step 8 (Allometric) ทำงานยังไงโดยไม่มี species จริง?**
   - hint: ดู Chave 2014 fallback ใน [บท 12](12-ml-step8-allometric.md)

5. **ถ้าต้นไม้สูง 30 ม. แต่ pipeline detect ได้ DBH ผิด 5% → carbon error ประมาณกี่ %?**
   - hint: AGB ∝ DBH^b โดย b ≈ 2.0-2.4 → error คูณ

---

## 9. อ่านต่อ — Per-step deep dive

ลำดับแนะนำ (ตามลำดับ pipeline):

- [บท 05 — Step 1: Ground Classification](05-ml-step1-ground-classification.md)
- [บท 06 — Step 2: Height Normalization](06-ml-step2-height-normalization.md)
- [บท 07 — Step 3: Canopy Height Model](07-ml-step3-canopy-height-model.md)
- [บท 08 — Step 4: Tree Segmentation](08-ml-step4-tree-segmentation.md)
- [บท 09 — Step 5: Wood-Leaf Separation](09-ml-step5-wood-leaf-separation.md)
- [บท 10 — Step 6: QSM (DBH + Height + Volume)](10-ml-step6-qsm.md)
- [บท 11 — Step 7: Species Classification](11-ml-step7-species-classifier.md)
- [บท 12 — Step 8: Allometric Carbon ⭐](12-ml-step8-allometric.md) — สำคัญสุด
- [บท 13 — Validation (Synthetic + Belgium)](13-ml-validation.md)

---

> 📝 **เขียนครั้งแรก:** 2026-05-24
