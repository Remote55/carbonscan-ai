"""G3 confounded historical experiment; not promotion evidence.

For each Belgium tree, compare predicted stem volume to the destructive ground
truth two ways:
    A) tlsep/PCA segmentation + taper volume (current default, ~18.8% MAPE)
    B) PointNet++ segmentation + sectional-cylinders volume

Both segmentation and volume method changed between A and B. Any volume
difference therefore cannot be causally attributed to PointNet segmentation and
cannot satisfy the evidence gate. This is a confounded historical experiment,
not promotion evidence; its local result is a within-script historical
comparison only, not an adoption or promotion decision.

    python notebooks/experiment_g3_pointnet_volume.py --model woodleaf_pn2.pt

Prints ASCII only ("m3") so it runs on a default Windows console.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import numpy as np

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from pipeline import qsm, wood_leaf_separation  # noqa: E402
from pipeline.field_eval import load_point_cloud, normalize_ground  # noqa: E402
from pipeline.wood_leaf_separation import WoodLeafSegmenter  # noqa: E402

DATA_DIR = ML_ROOT / "data" / "raw" / "zenodo_belgium"
PC_DIR = DATA_DIR / "pointclouds" / "pointclouds_clean"
CSV_PATH = DATA_DIR / "Destructive_and_qsm_data_DEMOL.csv"


def file_to_csv_name(stem: str) -> str:
    m = re.match(r"^([A-Z]+)(\d+)$", stem)
    return f"{m.group(1)}-{int(m.group(2)):02d}" if m else stem


def main() -> None:
    ap = argparse.ArgumentParser(description="G3 experiment: PointNet++ wood + sectional volume")
    ap.add_argument("--model", required=True, help="path to trained PointNet++ .pt")
    ap.add_argument("--max-points", type=int, default=8192, help="subsample per tree (speed)")
    ap.add_argument("--n-trees", type=int, default=0, help="0 = all matched trees")
    args = ap.parse_args()

    with CSV_PATH.open(encoding="utf-8") as f:
        gt = {r["tree_name"]: r for r in csv.DictReader(f)}
    files = {file_to_csv_name(p.stem): p for p in PC_DIR.glob("*.txt")}
    matched = sorted(set(gt) & set(files))
    if args.n_trees:
        matched = matched[: args.n_trees]
    print(f"Matched {len(matched)} trees; max_points={args.max_points}")

    seg = WoodLeafSegmenter(model_path=args.model, backend="pointnet")
    seg.load()

    errs_taper, errs_sect = [], []
    for name in matched:
        pts = normalize_ground(load_point_cloud(files[name], max_points=args.max_points))
        gt_vol = float(gt[name]["Volume_total_tree_harvested"]) / 1000.0  # dm3 -> m3

        # A) baseline: PCA wood + taper (compute_qsm default)
        pca_wood = pts[wood_leaf_separation.segment_wood_leaf(pts, k_neighbors=15)
                       == wood_leaf_separation.WOOD]
        taper_vol = qsm.compute_qsm(pca_wood).total_volume_m3

        # B) hypothesis: PointNet++ wood + sectional cylinders
        pn_wood = pts[seg.segment(pts) == wood_leaf_separation.WOOD]
        sect_vol, ncyl = qsm.estimate_volume_sectional(pn_wood)

        e_t = abs(taper_vol - gt_vol) / gt_vol * 100
        e_s = abs(sect_vol - gt_vol) / gt_vol * 100
        errs_taper.append(e_t)
        errs_sect.append(e_s)
        print(f"{name:<10} gt={gt_vol:5.3f}  taper={taper_vol:5.3f} ({e_t:4.0f}%)  "
              f"pn+sect={sect_vol:5.3f} ({e_s:4.0f}%)  ncyl={ncyl}", flush=True)

    t, s = np.array(errs_taper), np.array(errs_sect)
    print("\n" + "=" * 60)
    print(f"Baseline  PCA + taper        : mean |err| {t.mean():5.1f}%   median {np.median(t):5.1f}%")
    print(f"Experiment PointNet++ + sect : mean |err| {s.mean():5.1f}%   median {np.median(s):5.1f}%")
    print("=" * 60)
    verdict = (
        "sectional has lower mean error in this local comparison"
        if s.mean() < t.mean()
        else "taper has lower mean error in this local comparison"
    )
    print(
        "Historical comparison verdict (within-script historical comparison only; "
        f"not an adoption or promotion decision): {verdict}"
    )


if __name__ == "__main__":
    main()
