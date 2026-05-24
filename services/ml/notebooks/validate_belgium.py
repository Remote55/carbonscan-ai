"""End-to-end validation on the Demol et al. (2021) Belgian destructive-biomass dataset.

Downloads expected at:
    services/ml/data/raw/zenodo_belgium/
        pointclouds/pointclouds_clean/*.txt        (66 tree point clouds)
        Destructive_and_qsm_data_DEMOL.csv         (destructive ground truth, 65 trees)
        optimal_QSMs.zip                            (reference QSMs, not used here)

For each tree:
    1. Load XYZ point cloud (whitespace-separated .txt)
    2. Normalise Z (subtract min Z so ground ≈ 0)
    3. Subsample to ≤20k points for PCA tractability
    4. Run Phase-1 wood/leaf segmenter (rule-based)
    5. Run Phase-1 QSM (RANSAC DBH + max-Z height + taper volume)
    6. Compare against CSV ground truth (felled DBH, felled height, destructive mass+volume)
    7. Save:
        - docs/proposal/figures/belgium_validation.csv          (per-tree results)
        - docs/proposal/figures/fig11_belgium_dbh_parity.png    (parity plot)
        - docs/proposal/figures/fig12_belgium_height_parity.png
        - docs/proposal/figures/fig13_belgium_volume_parity.png

Reference:
    Demol et al. 2021 — "Estimating forest above-ground biomass with terrestrial laser
    scanning: current status and future directions". Trees 35, 671-685.
    https://doi.org/10.1007/s00468-020-02067-7
    Dataset: https://doi.org/10.5281/zenodo.4557401
"""

from __future__ import annotations

import csv
import re
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Make pipeline importable when running from services/ml/
ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from pipeline import qsm, wood_leaf_separation  # noqa: E402

# --- Paths ---
DATA_DIR = ML_ROOT / "data" / "raw" / "zenodo_belgium"
PC_DIR = DATA_DIR / "pointclouds" / "pointclouds_clean"
CSV_PATH = DATA_DIR / "Destructive_and_qsm_data_DEMOL.csv"
FIG_DIR = ML_ROOT.parent.parent / "docs" / "proposal" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Species code → human-readable name (for figures)
SPECIES_NAMES = {
    "FEXC": "Fraxinus excelsior (Ash)",
    "FSYL": "Fagus sylvatica (Beech)",
    "PSYLA": "Pinus sylvestris (Pine, site A)",
    "PSYLB": "Pinus sylvestris (Pine, site B)",
    "LXDC": "Larix decidua (Larch)",
}


def file_to_csv_name(file_stem: str) -> str:
    """Files are 'FEXC1', CSV expects 'FEXC-01' — normalize."""
    m = re.match(r"^([A-Z]+)(\d+)$", file_stem)
    if not m:
        return file_stem
    sp, num = m.group(1), int(m.group(2))
    return f"{sp}-{num:02d}"


def species_prefix(tree_name: str) -> str:
    m = re.match(r"^([A-Z]+)", tree_name)
    return m.group(1) if m else "UNK"


def load_point_cloud(path: Path, max_points: int = 20_000) -> np.ndarray:
    """Load XYZ + optionally subsample for speed.

    The Demol dataset files are whitespace-separated XYZ with no header.
    """
    pts = np.loadtxt(path)
    if pts.ndim == 1:
        pts = pts.reshape(1, -1)
    pts = pts[:, :3].astype(np.float64)
    if len(pts) > max_points:
        rng = np.random.default_rng(seed=0)
        idx = rng.choice(len(pts), max_points, replace=False)
        pts = pts[idx]
    return pts


def normalize_z(pts: np.ndarray) -> np.ndarray:
    """Shift so min Z ≈ 0 (ground baseline)."""
    out = pts.copy()
    out[:, 2] -= pts[:, 2].min()
    return out


def process_one_tree(tree_name: str, fp: Path, gt: dict) -> dict:
    """Run the pipeline on a single tree and return a results row."""
    t0 = time.time()
    raw_pts = load_point_cloud(fp, max_points=20_000)
    norm_pts = normalize_z(raw_pts)

    # Step 5 — wood/leaf
    labels = wood_leaf_separation.segment_wood_leaf(norm_pts, k_neighbors=15)
    wood_pts = norm_pts[labels == wood_leaf_separation.WOOD]
    wood_frac = len(wood_pts) / max(len(norm_pts), 1)

    # Step 6 — QSM
    qsm_result = qsm.compute_qsm(wood_pts, seed=0)

    elapsed = time.time() - t0

    # Ground-truth conversions
    # CSV columns:
    #   DBH               — diameter at breast height, cm (FELLED MEASUREMENT)
    #   TH_felled         — tree height, m (felled)
    #   Fresh_mass_total_tree_harvested — kg (destructive)
    #   Volume_total_tree_harvested      — kg / dm3 ... unit is ambiguous in dataset
    #                                       — Demol et al. report dm3, so divide by 1000 to get m3
    #   qsm_mean_volume   — Demol's own QSM volume in dm3 → /1000 for m3
    gt_dbh_cm = float(gt["DBH"])
    gt_height_m = float(gt["TH_felled"])
    gt_volume_m3 = float(gt["Volume_total_tree_harvested"]) / 1000.0
    gt_qsm_volume_m3 = float(gt["qsm_mean_volume"]) / 1000.0
    gt_mass_kg = float(gt["Fresh_mass_total_tree_harvested"])

    return {
        "tree": tree_name,
        "species": species_prefix(tree_name),
        "n_points": int(len(raw_pts)),
        "wood_frac": round(wood_frac, 3),
        # Predictions
        "pred_DBH_cm": round(qsm_result.dbh_cm, 2),
        "pred_H_m": round(qsm_result.height_m, 2),
        "pred_V_m3": round(qsm_result.total_volume_m3, 4),
        "pred_fit_quality": round(qsm_result.model_quality, 3),
        # Ground truth (felled / destructive)
        "gt_DBH_cm": round(gt_dbh_cm, 2),
        "gt_H_m": round(gt_height_m, 2),
        "gt_V_destructive_m3": round(gt_volume_m3, 4),
        "gt_V_belgium_qsm_m3": round(gt_qsm_volume_m3, 4),
        "gt_mass_kg": round(gt_mass_kg, 1),
        # Runtime
        "runtime_s": round(elapsed, 2),
    }


def run_all() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing CSV: {CSV_PATH}")
    if not PC_DIR.exists():
        raise FileNotFoundError(f"Missing point cloud dir: {PC_DIR}")

    # Build CSV lookup
    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    csv_lookup = {r["tree_name"]: r for r in rows}

    # Build file mapping (normalize names)
    file_paths = {file_to_csv_name(p.stem): p for p in PC_DIR.glob("*.txt")}
    matched = sorted(set(csv_lookup) & set(file_paths))
    print(f"Matched {len(matched)} / {len(csv_lookup)} trees against {len(file_paths)} files")

    results = []
    for i, name in enumerate(matched, 1):
        try:
            row = process_one_tree(name, file_paths[name], csv_lookup[name])
            results.append(row)
            print(
                f"[{i:2d}/{len(matched)}] {name:<10}  "
                f"DBH pred={row['pred_DBH_cm']:5.1f} gt={row['gt_DBH_cm']:5.1f}  "
                f"H pred={row['pred_H_m']:5.1f} gt={row['gt_H_m']:5.1f}  "
                f"{row['runtime_s']:5.1f}s",
                flush=True,
            )
        except Exception as e:  # noqa: BLE001 — keep going even if one tree fails
            print(f"[{i:2d}/{len(matched)}] {name}: FAILED — {e}", flush=True)

    df = pd.DataFrame(results)
    # Error columns
    df["DBH_err_pct"] = ((df["pred_DBH_cm"] - df["gt_DBH_cm"]) / df["gt_DBH_cm"] * 100).round(1)
    df["H_err_pct"] = ((df["pred_H_m"] - df["gt_H_m"]) / df["gt_H_m"] * 100).round(1)
    df["V_err_pct_vs_destructive"] = (
        (df["pred_V_m3"] - df["gt_V_destructive_m3"]) / df["gt_V_destructive_m3"] * 100
    ).round(1)
    return df


def parity_plot(
    df: pd.DataFrame,
    pred_col: str,
    gt_col: str,
    title: str,
    xlabel: str,
    ylabel: str,
    unit: str,
    save_to: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(7, 6.5))
    species_palette = {
        "FEXC": "#5C3A21",   # ash — brown
        "FSYL": "#2D6A4F",   # beech — green
        "PSYLA": "#74C0FC",  # pine site A — sky
        "PSYLB": "#0369A1",  # pine site B — deep blue
        "LXDC": "#F4A261",   # larch — orange
    }
    for sp in df["species"].unique():
        sub = df[df["species"] == sp]
        ax.scatter(
            sub[gt_col],
            sub[pred_col],
            s=60,
            color=species_palette.get(sp, "#888"),
            edgecolors="white",
            linewidth=0.8,
            label=SPECIES_NAMES.get(sp, sp),
            zorder=3,
        )
    lo = min(df[gt_col].min(), df[pred_col].min()) * 0.9
    hi = max(df[gt_col].max(), df[pred_col].max()) * 1.1
    ax.plot([lo, hi], [lo, hi], color="black", linestyle="--", alpha=0.6, label="y = x", zorder=2)
    ax.fill_between(
        [lo, hi], [lo * 0.9, hi * 0.9], [lo * 1.1, hi * 1.1],
        color="#ccc", alpha=0.3, label="±10%", zorder=1,
    )

    # Stats
    err = (df[pred_col] - df[gt_col]) / df[gt_col] * 100
    mae = (df[pred_col] - df[gt_col]).abs().mean()
    rmse = ((df[pred_col] - df[gt_col]) ** 2).mean() ** 0.5
    bias = (df[pred_col] - df[gt_col]).mean()

    stats_box = (
        f"n = {len(df)}\n"
        f"MAE = {mae:.2f} {unit}\n"
        f"RMSE = {rmse:.2f} {unit}\n"
        f"Mean error = {err.mean():+.1f}%\n"
        f"|Mean error| = {err.abs().mean():.1f}%"
    )
    ax.text(
        0.03, 0.97,
        stats_box,
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=10,
        bbox=dict(facecolor="white", edgecolor="#888", alpha=0.9, boxstyle="round,pad=0.5"),
    )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(loc="lower right", framealpha=0.95, fontsize=8.5)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_to, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"+ wrote {save_to.name}  (MAE={mae:.2f}{unit}, RMSE={rmse:.2f}{unit}, mean err={err.mean():+.1f}%)")


def main() -> None:
    print("=" * 78)
    print("Belgium destructive-biomass validation (Demol et al. 2021)")
    print("=" * 78)

    df = run_all()
    csv_out = FIG_DIR / "belgium_validation.csv"
    df.to_csv(csv_out, index=False)
    print(f"\n+ wrote {csv_out}  ({len(df)} trees)")

    parity_plot(
        df,
        pred_col="pred_DBH_cm",
        gt_col="gt_DBH_cm",
        title="Figure 11 — DBH parity vs. Demol et al. 2021 (felled measurement)",
        xlabel="Ground-truth DBH (felled, cm)",
        ylabel="Predicted DBH (RANSAC, cm)",
        unit="cm",
        save_to=FIG_DIR / "fig11_belgium_dbh_parity.png",
    )
    parity_plot(
        df,
        pred_col="pred_H_m",
        gt_col="gt_H_m",
        title="Figure 12 — Tree-height parity vs. Demol et al. 2021 (felled)",
        xlabel="Ground-truth Height (felled, m)",
        ylabel="Predicted Height (max-Z, m)",
        unit="m",
        save_to=FIG_DIR / "fig12_belgium_height_parity.png",
    )
    parity_plot(
        df,
        pred_col="pred_V_m3",
        gt_col="gt_V_destructive_m3",
        title="Figure 13 — Stem-volume parity vs. Demol et al. 2021 (destructive)",
        xlabel="Destructive stem volume (m³)",
        ylabel="Predicted taper-equation volume (m³)",
        unit="m³",
        save_to=FIG_DIR / "fig13_belgium_volume_parity.png",
    )

    # Summary print
    print("\n" + "=" * 78)
    print("SUMMARY (lower is better)")
    print("=" * 78)
    for col, label in [
        ("DBH_err_pct", "DBH error"),
        ("H_err_pct", "Height error"),
        ("V_err_pct_vs_destructive", "Volume error (vs destructive)"),
    ]:
        s = df[col].abs()
        print(f"  {label:<35}  mean={s.mean():5.1f}%  median={s.median():5.1f}%  max={s.max():5.1f}%")


if __name__ == "__main__":
    main()
