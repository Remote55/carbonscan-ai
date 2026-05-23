# ML Notebooks

Jupyter notebooks for ML pipeline development and validation.

## Files

### `e2e_validation.ipynb` — End-to-End Pipeline Validation

Runs every step of the ML pipeline (1–8) against a **synthetic forest plot** and
produces the figures used in the NSC 2026 Proposal "Preliminary Results"
section.

**Why synthetic data?** A real NEON LiDAR tile is ~5 GB and takes hours to
download. The synthetic generator (`pipeline.synthetic`) produces a realistic
point cloud (ground + 5 trees with trunks, branches, and leaves) using
parametric rules tuned to typical airborne LiDAR densities. Once real data
arrives, swap the data-loading cell for `laspy.read(...)` — everything
downstream stays identical.

**Outputs (saved to `docs/proposal/figures/`):**

| File                            | Content                                       |
|---------------------------------|-----------------------------------------------|
| `fig01_raw_point_cloud.png`     | Raw 3D point cloud colored by class           |
| `fig02_ground_classification.png` | Predicted vs ground-truth ground            |
| `fig03_height_normalization.png` | Z-distribution before/after                  |
| `fig04_chm.png`                 | Canopy Height Model heatmap                   |
| `fig05_tree_segmentation.png`   | Watershed output overlaid on CHM              |
| `fig06_wood_leaf.png`           | Per-tree wood/leaf classification             |
| `fig07_carbon_bars.png`         | Per-tree carbon bar chart                     |
| `fig08_accuracy.png`            | DBH + Height parity plots vs ground truth     |
| `e2e_results.csv`               | Tabular per-tree results                      |

## Running

### 1. Install dependencies (one-time)

The `services/ml/` package already has a `pyproject.toml` declaring everything
needed. From the project root:

```powershell
cd D:\Project_Carbon\services\ml

# Activate the existing virtual environment (created in PR #5)
.\.venv\Scripts\Activate.ps1

# Install in editable mode + dev extras (jupyterlab, matplotlib, etc.)
pip install -e ".[dev]"
```

If `.venv` doesn't exist yet:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 2. Open the notebook

```powershell
# From services/ml/ with the venv active
jupyter lab notebooks/e2e_validation.ipynb
```

Or use VS Code's notebook editor — pick the kernel `Python 3 (carbonscan-ml)`
(or whichever name your `.venv` registers as).

### 3. Run all cells

`Run → Run All Cells`. Total runtime: ~30 seconds on a laptop CPU.

You should see 8 figures appear inline, and the same images saved as PNG to
`docs/proposal/figures/`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'pipeline'` | Run `pip install -e .` from `services/ml/` |
| Figures look empty / NaN warnings | Increase `n_trees` or check that `seed` produced ground points |
| `cKDTree` slow on large clouds | Set `synthetic.generate_synthetic_plot(leaves_per_tree=2000)` to reduce point count |
| Want to use real NEON data | Replace cell under "Generate Synthetic Plot" with `points = np.column_stack([las.x, las.y, las.z])` after `las = laspy.read("path/to/plot.las")` |

## Swapping In Real Data

When NEON arrives, the only cell that changes is "1. Generate Synthetic Plot":

```python
import laspy

las = laspy.read("data/raw/NEON_D01_HARV_DP1_727000_4699000.las")
points = np.column_stack([las.x, las.y, las.z])
# `gt_labels` and `trees` are not available for real data — the F1 / parity
# cells will need to be skipped or replaced with field-survey ground truth.
```

Every other cell (`classify_ground_array`, `normalize_height_array`, …)
operates purely on `(N, 3)` arrays and works identically on real data.
