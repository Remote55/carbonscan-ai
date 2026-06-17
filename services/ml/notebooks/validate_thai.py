"""Validate the pipeline against Thai field ground truth — Sprint P1 / G1.

Two modes:

    # 1) DEMO — no field data needed. Proves the whole flow works today,
    #    using synthetic trees as stand-in ground truth.
    python notebooks/validate_thai.py --demo

    # 2) REAL — your hand-measured field data + per-tree point clouds.
    python notebooks/validate_thai.py \
        --gt-csv data/field/thai_ground_truth.csv \
        --pc-dir data/field/pointclouds

Field CSV schema: see data/field/thai_ground_truth_TEMPLATE.csv

Outputs (to --out-dir, default docs/proposal/figures):
    thai_validation.csv      per-tree predicted vs measured + % errors
    fig16_thai_parity.png    DBH + Height parity plots (Thai labels)

Prints are ASCII-safe (uses "m3") so it runs on a default Windows console.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from pipeline.field_eval import (  # noqa: E402
    circumference_to_dbh,
    error_metrics,
    load_point_cloud,
    normalize_ground,
    predict_tree,
)

DEFAULT_OUT = ML_ROOT.parent.parent / "docs" / "proposal" / "figures"

ROW_FIELDS = [
    "tree_id", "species_sci",
    "gt_dbh_cm", "gt_height_m",
    "pred_dbh_cm", "pred_height_m", "pred_volume_m3",
    "wood_frac", "fit_quality",
    "dbh_err_pct", "height_err_pct",
]


def _setup_thai_font() -> str | None:
    """Pick a Thai-capable font (same approach as make_diagrams.py)."""
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    available = {f.name for f in font_manager.fontManager.ttflist}
    for f in ["Tahoma", "Leelawadee UI", "Sarabun", "Noto Sans Thai", "Microsoft Sans Serif"]:
        if f in available:
            plt.rcParams["font.family"] = f
            plt.rcParams["font.sans-serif"] = [f, "DejaVu Sans"]
            return f
    return None


def run_demo(n_trees: int = 6, seed0: int = 1) -> list[dict]:
    """Run on synthetic single-tree clouds whose true DBH/height are known."""
    from pipeline.synthetic import generate_synthetic_plot

    rows = []
    for i in range(n_trees):
        # Small, gently-undulating plot ≈ a tight single-tree photogrammetry
        # scan (what G1 field capture produces) — not a 30 m forest plot, whose
        # terrain would contaminate the breast-height slice.
        pts, _, trees = generate_synthetic_plot(
            n_trees=1, plot_size_m=8.0, ground_z_variation=0.3, seed=seed0 + i
        )
        t = trees[0]
        pred = predict_tree(normalize_ground(pts))
        rows.append(_row(f"DEMO-{i + 1:02d}", t.species_sci, t.dbh_cm, t.height, pred))
        print(f"  [{i + 1}/{n_trees}] DEMO-{i + 1:02d}  "
              f"DBH pred={pred['dbh_cm']:5.1f} gt={t.dbh_cm:5.1f}  "
              f"H pred={pred['height_m']:5.1f} gt={t.height:5.1f}", flush=True)
    return rows


def run_from_csv(gt_csv: Path, pc_dir: Path) -> list[dict]:
    """Run on real field data: hand-measured CSV + per-tree point clouds."""
    rows = []
    with Path(gt_csv).open(encoding="utf-8-sig") as f:
        records = list(csv.DictReader(f))
    for r in records:
        dbh_cm = (
            float(r["dbh_cm"]) if r.get("dbh_cm") else circumference_to_dbh(float(r["circumference_cm"]))
        )
        pc_path = Path(pc_dir) / r["point_cloud_file"]
        if not pc_path.exists():
            print(f"  ! missing point cloud: {pc_path}  (skipped)", flush=True)
            continue
        pred = predict_tree(normalize_ground(load_point_cloud(pc_path)))
        rows.append(_row(r["tree_id"], r.get("species_sci", ""), dbh_cm, float(r["height_m"]), pred))
        print(f"  {r['tree_id']:<10}  DBH pred={pred['dbh_cm']:5.1f} gt={dbh_cm:5.1f}  "
              f"H pred={pred['height_m']:5.1f} gt={float(r['height_m']):5.1f}", flush=True)
    return rows


def _row(tree_id: str, species: str, gt_dbh: float, gt_height: float, pred: dict) -> dict:
    return {
        "tree_id": tree_id,
        "species_sci": species,
        "gt_dbh_cm": round(gt_dbh, 2),
        "gt_height_m": round(gt_height, 2),
        "pred_dbh_cm": round(pred["dbh_cm"], 2),
        "pred_height_m": round(pred["height_m"], 2),
        "pred_volume_m3": round(pred["volume_m3"], 4),
        "wood_frac": round(pred["wood_frac"], 3),
        "fit_quality": round(pred["fit_quality"], 3),
        "dbh_err_pct": round((pred["dbh_cm"] - gt_dbh) / gt_dbh * 100, 1) if gt_dbh else 0.0,
        "height_err_pct": round((pred["height_m"] - gt_height) / gt_height * 100, 1) if gt_height else 0.0,
    }


def write_csv(rows: list[dict], out_path: Path) -> None:
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ROW_FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"+ wrote {out_path}  ({len(rows)} trees)")


def _subplot_parity(ax, rows, gt_key, pred_key, title, unit):
    gt = np.array([r[gt_key] for r in rows], float)
    pred = np.array([r[pred_key] for r in rows], float)
    ax.scatter(gt, pred, s=60, color="#2D6A4F", edgecolors="white", linewidth=0.8, zorder=3)
    lo = float(min(gt.min(), pred.min())) * 0.9
    hi = float(max(gt.max(), pred.max())) * 1.1
    ax.plot([lo, hi], [lo, hi], "k--", alpha=0.6, label="y = x", zorder=2)
    ax.fill_between([lo, hi], [lo * 0.9, hi * 0.9], [lo * 1.1, hi * 1.1],
                    color="#ccc", alpha=0.3, label="±10%", zorder=1)
    m = error_metrics(pred, gt)
    ax.text(0.03, 0.97,
            f"n = {m['n']}\nMAE = {m['mae']:.2f} {unit}\n"
            f"RMSE = {m['rmse']:.2f} {unit}\nMean err = {m['mean_pct']:+.1f}%",
            transform=ax.transAxes, ha="left", va="top", fontsize=10,
            bbox={"facecolor": "white", "edgecolor": "#888", "alpha": 0.9, "boxstyle": "round,pad=0.5"})
    ax.set_title(title)
    ax.set_xlabel(f"ค่าวัดจริงภาคสนาม ({unit})")
    ax.set_ylabel(f"ค่าที่ระบบทำนาย ({unit})")
    ax.legend(loc="lower right", fontsize=8.5)
    ax.grid(alpha=0.3)


def parity_plot(rows: list[dict], out_png: Path, *, demo: bool) -> None:
    import matplotlib.pyplot as plt

    _setup_thai_font()
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    tag = " (DEMO — synthetic)" if demo else ""
    _subplot_parity(axes[0], rows, "gt_dbh_cm", "pred_dbh_cm",
                    f"Figure 16a — DBH parity: ไม้ไทย{tag}", "cm")
    _subplot_parity(axes[1], rows, "gt_height_m", "pred_height_m",
                    f"Figure 16b — Height parity: ไม้ไทย{tag}", "m")
    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"+ wrote {out_png}")


def print_summary(rows: list[dict]) -> None:
    dbh = error_metrics([r["pred_dbh_cm"] for r in rows], [r["gt_dbh_cm"] for r in rows])
    h = error_metrics([r["pred_height_m"] for r in rows], [r["gt_height_m"] for r in rows])
    print("\n" + "=" * 60)
    print("SUMMARY — Thai field validation (lower is better)")
    print("=" * 60)
    print(f"  DBH     MAE={dbh['mae']:.2f} cm   mean err={dbh['mean_pct']:+.1f}%   |mean|={dbh['abs_mean_pct']:.1f}%")
    print(f"  Height  MAE={h['mae']:.2f} m    mean err={h['mean_pct']:+.1f}%   |mean|={h['abs_mean_pct']:.1f}%")
    print("\nNote: DEMO uses synthetic trees. For real proof, collect 5-10 Thai")
    print("trees (tape DBH + clinometer height) and run with --gt-csv/--pc-dir.")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate pipeline on Thai field ground truth (G1)")
    p.add_argument("--demo", action="store_true", help="run on synthetic trees (no field data)")
    p.add_argument("--n-demo", type=int, default=6)
    p.add_argument("--gt-csv", type=str, help="hand-measured ground-truth CSV")
    p.add_argument("--pc-dir", type=str, help="directory of per-tree point clouds")
    p.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT))
    return p


def main() -> None:
    args = build_arg_parser().parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    if args.demo:
        print("Thai field validation — DEMO mode (synthetic trees)")
        rows = run_demo(n_trees=args.n_demo)
    else:
        if not args.gt_csv or not args.pc_dir:
            raise SystemExit("Provide --demo, OR both --gt-csv and --pc-dir")
        print(f"Thai field validation — {args.gt_csv}")
        rows = run_from_csv(Path(args.gt_csv), Path(args.pc_dir))

    if not rows:
        raise SystemExit("No trees processed — check inputs.")

    write_csv(rows, out_dir / "thai_validation.csv")
    parity_plot(rows, out_dir / "fig16_thai_parity.png", demo=args.demo)
    print_summary(rows)


if __name__ == "__main__":
    main()
