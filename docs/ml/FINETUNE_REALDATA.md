# Fine-tuning Wood/Leaf PointNet++ on Real TLS Data (Wan 2021)

> **Why:** the synthetic-trained model scores IoU **0.978 on the synthetic test**
> but only **~0.33 zero-shot on real TLS** (PCA baseline ~0.25). That sim-to-real
> gap is expected — closing it needs training on *real labelled* data. This
> runbook fine-tunes the model on the real Wan 2021 dataset and reports a
> spatially separated development-split real IoU, not promotion evidence.

## Data
**Wan 2021** — Dryad `10.5061/dryad.rfj6q5799` (CC-BY). 3 plot files
`x y z R G B label` (label col 6: **0 = wood, 1 = leaf**), 73 trees / 3 species
(white birch, Dahurian larch, Chinese scholar tree). ~7.8 GB total — keep it
**local** (git-ignored under `services/ml/data/realdata/wan2021/`).

## Step 1 — Convert locally (handles the multi-GB files → tiny `.npz`)

Run where the big `.txt` files live. The converter seek-samples each plot, tiles
it into ~2.5 m cells (≈ single-tree scale), normalises each cell to the unit
sphere (PointNet++ input format), and splits tiles **spatially** with a buffer
gap for development/validation only.

```bash
cd services/ml
./.venv/Scripts/python.exe -m training.realdata_dataset \
  --plots data/realdata/wan2021/reference_pc_White_Birch.txt \
          data/realdata/wan2021/reference_pc_Dahurian_Larch.txt \
          data/realdata/wan2021/reference_pc_Chinese_scholar_tree.txt \
  --out-train data/realdata/wan_train.npz \
  --out-test  data/realdata/wan_test.npz
```

Expected output (≈):
```
train_samples: 295   test_samples: 77   train_wood_frac: 0.287   test_wood_frac: 0.241
```
`wan_train.npz` (~12 MB) + `wan_test.npz` (~3 MB) — small enough to upload to Colab.
`--out-test` and `wan_test.npz` are legacy names for the development/validation split;
they do not make it an independent final test.

### The split and its limit
Per plot, tiles are cut along x at `frac` (default 0.70); tiles inside a `buffer`
band (default 2.5 m) around the cut are **dropped**. This is a **spatially
separated development split with a 2.5 m excluded band**. Native tree IDs are
unavailable, so spatial separation cannot prove unseen-tree separation. The same
dev loader selected the epoch, so it is validation/development evidence,
not an independent final test or promotion gate.

> **Harder, cross-species test (optional):** pass only 2 plots to `--plots` and
> evaluate on the 3rd species' tiles (regenerate that plot as the development
> split). This remains development evidence, not an independent final test.
> This is leave-one-species-out and is a stronger (harder) claim.

## Step 2 — Fine-tune on Colab (free GPU)

Upload `wan_train.npz`, `wan_test.npz`, and the existing synthetic checkpoint
`woodleaf_pn2.pt`, plus the repo (or at least the `training/` + `pipeline/`
packages). Then:

```python
!pip install torch numpy
# fine-tune from the synthetic checkpoint on real data:
!python -m training.train_woodleaf \
    --train-npz wan_train.npz --val-npz wan_test.npz \
    --init-checkpoint woodleaf_pn2.pt \
    --class-weight auto \
    --epochs 60 --lr 1e-4 --batch-size 8 \
    --out woodleaf_pn2_wan.pt
```

- **`--class-weight auto` is important.** The data is ~70% leaf, so plain
  cross-entropy lets the model ignore the minority **wood** class (a first run
  without it left wood IoU stuck at ~0.19). Auto uses inverse-frequency
  ('balanced') weights to lift the wood class.
- `--init-checkpoint` starts from the synthetic weights (fine-tune, not from
  scratch). Use a **low LR (1e-4)** so it adapts without forgetting.
- The per-epoch `val_wood_IoU` is the wood-class IoU on the legacy-named
  development/validation tiles. The same dev loader selected the epoch, so it
  is useful for monitoring but is not an independent final-test number.
- Best checkpoint is saved to `woodleaf_pn2_wan.pt`.

**Baselines to compare against (optional):**
```python
# train from scratch on real only (no synthetic init) — shows the value of pretraining
!python -m training.train_woodleaf --train-npz wan_train.npz --val-npz wan_test.npz \
    --epochs 60 --lr 1e-3 --out woodleaf_pn2_wan_scratch.pt
```

## Step 3 — Report honestly

| Setting | Wood IoU (historical development observation) |
|---|---|
| PCA baseline (`tlsep`), zero-shot | ~0.25 |
| PointNet++ synthetic-only, zero-shot | ~0.33 |
| **PointNet++ fine-tuned on real** | **← fill in from Colab** |
| (reference) PointNet++ on synthetic test | 0.978 |

Frame for the report: *"PointNet++ trained on synthetic reaches 0.978 on the
synthetic test; the ~0.33 zero-shot and any fine-tuned Wan figures are
approximate historical development observations. They are not independent real
TLS/final-test evidence or promotion evidence. A separately governed final
evaluation is still required before making a real-data performance claim."*

## Notes
- Files produced here (`*.npz`, `*.pt`, `data/realdata/`) are git-ignored — they
  are reproducible from the dataset + this runbook.
- Converter knobs: `--tile` (cell size m), `--n-points` (per-sample point count),
  `--min-pts` (drop sparse cells), `--frac` / `--buffer` (split). Defaults match
  the numbers above.

## Same-environment experiments (train+development on real Wan, 4 variants)

Per advisor guidance: use a train+development split in the **same real
environment** with more data, use synthetic only as **augmentation**, and
**keep every result**. This development split has the limits stated above and
does not become an independent final test.

### Step A — regenerate bigger real training and development sets (local)
```bash
cd services/ml && python -m training.realdata_dataset \
  --plots data/realdata/wan2021/reference_pc_White_Birch.txt \
          data/realdata/wan2021/reference_pc_Dahurian_Larch.txt \
          data/realdata/wan2021/reference_pc_Chinese_scholar_tree.txt \
  --out-train data/realdata/wan_train.npz --out-test data/realdata/wan_test.npz \
  --n-off 10000 --per 1500
```
Upload the two `.npz` to Colab (no checkpoint needed — these are from-scratch runs).

### Step B — run the 4 variants on Colab (GPU)
```python
# 1) from-scratch, no class-weight
!python -m training.train_woodleaf --train-npz wan_train.npz --val-npz wan_test.npz \
    --epochs 60 --lr 1e-3 --out wan_v1.pt
# 2) from-scratch, class-weight
!python -m training.train_woodleaf --train-npz wan_train.npz --val-npz wan_test.npz \
    --class-weight auto --epochs 60 --lr 1e-3 --out wan_v2.pt
# 3) from-scratch + synthetic augmentation, no class-weight
!python -m training.train_woodleaf --train-npz wan_train.npz --val-npz wan_test.npz \
    --augment-synthetic 200 --epochs 60 --lr 1e-3 --out wan_v3.pt
# 4) from-scratch + synthetic augmentation, class-weight
!python -m training.train_woodleaf --train-npz wan_train.npz --val-npz wan_test.npz \
    --augment-synthetic 200 --class-weight auto --epochs 60 --lr 1e-3 --out wan_v4.pt
```

### Step C — record results
Each run ends with a line like:
```
[held-out] wood_iou=0.31 leaf_iou=0.55 mean_iou=0.43 accuracy=0.62
```
Here `[held-out]` is the training script's legacy output label for the
development split. It is not an independent or final test.

Copy those numbers into the matrix table in `docs/ml/WOODLEAF_RESULTS.md` (one row per variant).
