# Spec — Zero-shot Real Wood/Leaf IoU Evaluation

> **Status:** Approved design, ready for implementation
> **Date:** 2026-06-26 · **Topic:** วัด wood/leaf IoU ของ segmenter บน **ไม้จริง** (zero-shot) เพื่อปิด con "IoU วัดบน synthetic ล้วน"
> **Context:** ดู [AI_AGENT_CONTEXT.md](../../AI_AGENT_CONTEXT.md) + [DATASET_SECTION.md](../../proposal/DATASET_SECTION.md) ก่อนเริ่ม

## 1. Goal
รัน wood/leaf segmenter ที่มีอยู่ (PointNet++ เทรนบน synthetic + PCA baseline `tlsep`) บน **point cloud ไม้จริงที่มี label มือ** แบบ **zero-shot (ไม่ retrain)** แล้วรายงาน **wood IoU / leaf IoU / mean IoU แยกตาม backend แยกตาม dataset** → เปลี่ยนข้อความ "IoU 0.978 วัดบน synthetic; ไม้จริงอยู่ระหว่างเก็บ" ให้เป็น **ตัวเลขจริงบนไม้จริง**

## 2. Decisions (จาก brainstorming)
- **Zero-shot transfer** เท่านั้น — ไม่ retrain/fine-tune (เร็ว + honest + มีโมเดลพร้อม). IoU บนไม้จริงอาจต่ำกว่า synthetic 0.978 = ผลที่ honest และยังแข็งกว่า synthetic ล้วน
- **Phased A→B (de-risk):**
  - **Phase 1 — Wan 2021 (จีน):** label ราย point ตรง ๆ → เสียบเร็ว, การันตีได้ตัวเลขก่อน
  - **Phase 2 — Shivalik (อินเดีย):** GT มาเป็นไฟล์ "wood-only" ต้องจับคู่จุดเอง; ได้ไม้เขตร้อนเอเชีย (มีสัก *Tectona grandis*) + เทียบกับ 4 baseline ที่ชุดข้อมูลแถมมา (LeWoS/TLSeparation/CANUPO/RF)
- **Reuse** ของเดิม: `training.metrics.iou_score`, `pipeline.field_eval.load_point_cloud`, `wood_leaf_separation.WoodLeafSegmenter`
- **ไม่ commit dataset เข้า git** (ใหญ่) — โหลดเองวางใน `data/realdata/<ds>/` (gitignore)

## 3. Components (โมดูลใหม่ `services/ml/pipeline/realdata_eval.py`)

### 3.1 Loaders (ตัวเดียวที่ผูกกับ format ของแต่ละ dataset)
```
load_labelled_cloud(path, *, label_col, wood_labels) -> (points (N,3) float64, gt (N,) uint8∈{0,1})
```
- สำหรับ **Wan**: อ่าน XYZ + คอลัมน์ที่ index `label_col` จากไฟล์ (.txt/.csv) → `gt = 0 (wood)` ถ้า label ∈ `wood_labels`, ไม่งั้น `1 (leaf)`
- ค่า `label_col` + `wood_labels` จริง **ยืนยันตอนเปิดไฟล์จริงครั้งแรก** แล้วตั้งเป็น default ของ dataset นั้นจุดเดียว (ใน CLI mapping)

```
derive_labels_from_woodonly(full_path, wood_only_path, tol=1e-3) -> (points (N,3), gt (N,) uint8)
```
- สำหรับ **Shivalik**: โหลดต้นเต็ม + ไฟล์ wood-only ด้วย **XYZ เท่านั้น** → สร้าง `cKDTree` บน wood-only → จุดในต้นเต็มที่อยู่ห่าง wood-only ≤ `tol` → wood(0), ที่เหลือ → leaf(1)
- ใช้ XYZ จับคู่ (เลี่ยงปัญหา zero-intensity ที่เปเปอร์เตือน)

> **สำคัญ:** loader ทั้งสองต้องโหลด **ทุกจุด** (ปิด decimation ภายในของ `field_eval.load_point_cloud` ด้วยการส่ง `max_points` ค่ามหาศาล) — ไม่งั้น full vs wood-only จะถูกสุ่มลดจุดคนละชุด → การจับคู่/label เพี้ยน. การลดจุดทำทีหลังแบบจับคู่ใน `evaluate_cloud` เท่านั้น

### 3.2 Eval core (dataset-agnostic)
```
evaluate_cloud(points, gt, *, backend="tlsep", model_path=None, max_points=200_000)
    -> {wood_iou, leaf_iou, mean_iou, accuracy, wood_frac_gt, wood_frac_pred, n_points}
```
- ถ้า `len(points) > max_points` → **decimate points+gt พร้อมกัน** (seeded) ก่อน segment
- `WoodLeafSegmenter(backend, model_path).segment(points)` → pred (WOOD=0/LEAF=1)
- `wood_iou = iou_score(pred, gt, 0)`, `leaf_iou = iou_score(pred, gt, 1)`, `mean_iou = (wood_iou+leaf_iou)/2`

```
evaluate_dataset(trees: list[(tree_id, points, gt)], *, backends, model_path=None)
    -> {"per_tree": [...], "summary": {backend: {mean_wood_iou, mean_leaf_iou, mean_iou, n_trees}}}
```

### 3.3 CLI — เพิ่ม command `eval-realdata` ใน `pipeline/main.py`
```
python -m pipeline.main eval-realdata --dataset wan --root data/realdata/wan2021 \
       --backend tlsep,pointnet --model woodleaf_pn2.pt --out wan_iou.json
```
- `--dataset {wan,shivalik}`: เลือกวิธี glob/pair ไฟล์
  - **wan**: glob ไฟล์ labelled → `load_labelled_cloud`
  - **shivalik**: จับคู่ไฟล์ต้นเต็ม ↔ ไฟล์ wood-only ตาม naming convention (ยืนยันตอนได้ไฟล์จริง) → `derive_labels_from_woodonly`
- `--backend` รับหลายค่าคั่นด้วย comma; `--model` checkpoint สำหรับ pointnet; `--out` JSON; `--max-points`
- เขียน JSON + print ตาราง (ต่อ backend: mean wood/leaf/mean IoU + จำนวนต้น)

## 4. Data flow
ดาวน์โหลดเอง → `data/realdata/<ds>/` (gitignore)
→ CLI glob/pair ไฟล์ → loader คืน `(tree_id, points, gt)` ต่อต้น
→ ต่อ backend: `evaluate_cloud` → metric ต่อต้น
→ `evaluate_dataset` aggregate → JSON + ตาราง console
→ ตัวเลขเข้ารายงาน: PointNet++ vs PCA; Shivalik เทียบ 4 baseline บนต้นเดียวกัน

## 5. Error handling
- `backend=pointnet` แต่ไม่มี/หา checkpoint ไม่เจอ → error ข้อความชัด
- ไฟล์เสีย/อ่านไม่ได้/ว่าง → skip ต้นนั้น + warn, ทำต้นอื่นต่อ
- Shivalik: ถ้าสัดส่วนจุดที่จับคู่ได้ผิดปกติ (เช่น wood_frac 0 หรือ 1) → warn ว่า `tol`/การ pair อาจผิด
- decimation ต้องคง index คู่ points/gt (ห้ามใช้ decimation ภายใน `load_point_cloud` ที่ทิ้ง gt)
- รายงาน **per-class IoU** เสมอ (ไม่พึ่ง accuracy เดี่ยว เพราะใบมักเยอะกว่าไม้ → accuracy หลอกตา)

## 6. Testing (TDD, ไม่แตะเน็ต)
- **`derive_labels_from_woodonly`**: fixture ต้นเต็ม 6 จุด, wood-only = 3 จุดในนั้น → assert 3 จุดนั้น = wood(0), ที่เหลือ leaf(1)
- **`load_labelled_cloud`**: เขียน temp `.txt` (XYZ + คอลัมน์ label) → assert points + gt + การ map ถูก
- **`evaluate_cloud`**: ป้อน pred/gt ที่รู้ผล (stub/monkeypatch segmenter) → assert wood_iou/leaf_iou/mean ตรงค่าที่คำนวณมือ; perfect match → 1.0
- **`evaluate_dataset`**: 2 fake trees → assert aggregate mean ถูก
- ใช้ fixture สังเคราะห์เล็ก/temp ทั้งหมด — **ไม่โหลด dataset จริงใน test**
- Full suite เดิมต้องไม่ break

## 7. Out of scope (YAGNI)
ไม่ทำ: retrain/fine-tune, กราฟ/รูป (คนเขียนรายงานทำเอง), GUI, commit dataset เข้า git, รองรับ big-endian/format แปลก, การ pair ALS↔TLS (ใช้แค่ TLS per-tree), full plot-level Shivalik (เป็น on-request)

## 8. Acceptance criteria
- [ ] `realdata_eval.py`: loaders + `evaluate_cloud` + `evaluate_dataset` ครบ + tests ผ่าน
- [ ] CLI `eval-realdata` รันได้จริงบนไฟล์ตัวอย่าง (smoke) → JSON + ตาราง
- [ ] **Phase 1:** รัน Wan 2021 → ได้ mean wood/leaf IoU (PointNet++ vs PCA)
- [ ] **Phase 2:** รัน Shivalik → ได้ IoU + เทียบ 4 baseline ที่แถมมา
- [ ] `ruff` clean · full suite ไม่ break

## 9. ไฟล์ที่จะแตะ
ใหม่: `pipeline/realdata_eval.py`, `tests/test_realdata_eval.py`, `.gitignore` (เพิ่ม `data/realdata/`)
แก้: `pipeline/main.py` (เพิ่ม CLI `eval-realdata`)
อาจอัปเดตภายหลัง: `docs/proposal/DATASET_SECTION.md` (ใส่เลข real IoU เมื่อรันเสร็จ)

## 10. Datasets (โหลดเอง — CC-BY/เปิด)
- **Wan 2021** (จีน, label wood/leaf ราย point): Dryad DOI `10.5061/dryad.rfj6q5799`
- **Shivalik 2026** (อินเดีย, 674 ต้น/24 ชนิด, wood-only files + 4 baseline): Zenodo DOI `10.5281/zenodo.15362444` · Sci Data DOI `10.1038/s41597-026-06674-w` · License CC-BY 4.0
