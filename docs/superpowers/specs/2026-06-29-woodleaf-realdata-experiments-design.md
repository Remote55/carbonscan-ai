# Spec — Wood/Leaf Real-Data Experiments (same-environment training)

> **Status:** Approved design, ready for implementation
> **Date:** 2026-06-29 · **Topic:** เทรน/เทส wood-leaf บนไม้จริง (Wan) แบบ same-environment ด้วยข้อมูลที่มากขึ้น, ลอง 4 variants, เก็บผลทุกแบบ
> **Context:** ดู [AI_AGENT_CONTEXT.md](../../AI_AGENT_CONTEXT.md), [FINETUNE_REALDATA.md](../../ml/FINETUNE_REALDATA.md)

## 1. Goal
ทำตามคำแนะนำอาจารย์ (Wannipa): เทรน/เทสบน **environment เดียวกัน (ไม้จริง Wan → ไม้จริง Wan)** ด้วย **ข้อมูลจริงที่มากขึ้น** (เดิมใช้แค่ 295 tiles จาก ~3M/30M จุด/plot), ใช้ **synthetic เป็น augmentation** (ไม่ใช่เทรนล้วน), ลอง **4 variants** แล้ว **เก็บผลทุกแบบ** (แม้ผลไม่ดี)

## 2. Decisions (จาก brainstorming + อาจารย์)
- เทรน **from-scratch บนไม้จริง** เป็นหลัก (ไม่ init จาก synthetic) — `--init-checkpoint` มีอยู่แล้ว ไม่ต้องแก้
- **synthetic = augmentation** (ผสมเข้าชุด train) ไม่ใช่ pretrain
- ดึงข้อมูลจริง **มากขึ้น** ผ่าน knob ของ converter (reproducible)
- ทุก run **self-report** wood/leaf/mean IoU บน held-out (เดิมพิมพ์แค่ wood)
- เก็บผลทุก variant ลง results log
- ใช้ flags ของ `train_woodleaf` เดิม — ไม่สร้าง experiment-runner ใหม่ (YAGNI)

## 3. Components

### 3.1 Converter knobs — `training/realdata_dataset.py`
- เพิ่ม CLI args `--n-off` (default 3000) และ `--per` (default 1000) ส่งต่อเข้า `load_wan_plot(..., n_off=, per=)` (พารามิเตอร์มีอยู่แล้ว เพียงยังไม่ expose ใน CLI)
- ใช้ค่าใหญ่ขึ้นตอน regen (เช่น `--n-off 10000 --per 1500`) → ดึง ~15M จุด/plot → tiles เยอะ/หนาแน่นขึ้น
- คง spatial held-out + buffer split เดิม (กันรั่ว)

### 3.2 Synthetic augmentation — `training/train_woodleaf.py`
```
_augment_with_synthetic(x: np.ndarray, y: np.ndarray, n: int, seed: int = 50_000) -> (x, y)
```
- ถ้า `n > 0`: สร้าง `n` synthetic samples ด้วย `build_woodleaf_dataset(n_samples=n, n_points=x.shape[1], seed0=seed)` แล้ว `concatenate` กับ (x, y) จาก npz (seed0 ตั้งสูงเพื่อไม่ทับกับ synthetic ชุดอื่น)
- เพิ่ม CLI `--augment-synthetic N` (default 0); ใช้เฉพาะตอนมี `--train-npz`

### 3.3 Full held-out report — `training/train_woodleaf.py`
```
_iou_triple(preds: np.ndarray, gts: np.ndarray) -> tuple[float, float, float]   # (wood, leaf, mean)
evaluate_full(model, loader, device) -> dict   # {wood_iou, leaf_iou, mean_iou, accuracy}
```
- จบ training พิมพ์สรุป held-out: `wood/leaf/mean IoU + accuracy` (pooled per-point) — ทุก run จึง self-report ครบ ไม่ต้องส่ง checkpoint มา eval ทีละอัน
- `evaluate()` (wood IoU per-tile) ที่มีอยู่คงไว้สำหรับ track ระหว่างเทรน + เลือก best checkpoint

### 3.4 Results log — `docs/ml/WOODLEAF_RESULTS.md` (ใหม่)
ตาราง log ทุก variant: config (init / augment / class-weight / #train tiles) + wood/leaf/mean IoU บน Wan held-out. เติมผลเดิม 3 แถว (zero-shot, fine-tune, fine-tune+CW) + ช่องว่างสำหรับ 4 variants ใหม่

### 3.5 Recipe — `docs/ml/FINETUNE_REALDATA.md` (อัปเดต)
เพิ่มส่วน "same-environment experiments": คำสั่ง regen ชุดใหญ่ + 4 คำสั่ง Colab (matrix) + วิธีอ่านเลข final report ลง results log

## 4. Variant matrix (4 runs)
| # | init | augment-synthetic | class-weight |
|---|---|---|---|
| 1 | scratch | 0 | none |
| 2 | scratch | 0 | auto |
| 3 | scratch | N (เช่น 200) | none |
| 4 | scratch | N | auto |

(ทั้งหมด `--train-npz wan_train.npz --val-npz wan_test.npz`, ไม่มี `--init-checkpoint`)

## 5. Data flow
regen npz ใหญ่ (local, `realdata_dataset --n-off 10000 --per 1500`) → upload Colab → รัน 4 variants → แต่ละ run พิมพ์ wood/leaf/mean บน held-out → กรอกลง `WOODLEAF_RESULTS.md`

## 6. Testing (TDD)
- `_iou_triple(pred, gt)`: ค่า known (perfect→1.0; overlap ที่คำนวณมือ) — pure NumPy
- `_augment_with_synthetic(x, y, n, ...)`: assert shape = (orig+n, P, 3) / (orig+n, P), dtype ถูก, ส่วนต้นยังเป็นข้อมูลเดิม
- `--n-off/--per` เป็น pass-through (ไม่ต้อง unit test หนัก) — verify ด้วย ruff + การรันจริงตอน regen
- full suite เดิมไม่ break; torch-gated tests ใช้ `pytest.importorskip("torch")` ตามแบบเดิม

## 7. Out of scope (YAGNI)
ไม่ทำ: auto experiment-runner/sweep, hyperparameter search, Shivalik, การเปลี่ยน architecture, photogrammetry path

## 8. Acceptance criteria
- [ ] converter `--n-off/--per` ใช้ได้ + regen ชุดใหญ่สำเร็จ (รายงานจำนวน tiles จริง)
- [ ] `--augment-synthetic` + final wood/leaf/mean report ทำงาน (smoke)
- [ ] `WOODLEAF_RESULTS.md` มีผลเดิม 3 แถว + ช่อง 4 variants
- [ ] `FINETUNE_REALDATA.md` มี 4 คำสั่ง Colab
- [ ] tests ใหม่ผ่าน · ruff clean · full suite ไม่ break

## 9. ไฟล์ที่จะแตะ
ใหม่: `docs/ml/WOODLEAF_RESULTS.md`
แก้: `training/realdata_dataset.py` (CLI knobs), `training/train_woodleaf.py` (augment + full report), `tests/test_woodleaf_training.py` (+ tests), `docs/ml/FINETUNE_REALDATA.md` (recipe)
Regenerate (local, gitignored): `data/realdata/wan_train.npz` / `wan_test.npz`
