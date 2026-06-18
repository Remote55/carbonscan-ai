"""Compare PointNet++ vs PCA wood-leaf segmentation on held-out trees (G2).

Answers the G2 acceptance question: does the trained deep model actually beat
the rule-based PCA baseline? Both are scored on the SAME held-out synthetic
trees (true labels known). Produces a table + bar chart for the Final Report.

    # PCA baseline only — runs anytime, no model needed
    python notebooks/compare_woodleaf.py

    # full comparison once you've trained a checkpoint (e.g. on Colab)
    python notebooks/compare_woodleaf.py --model woodleaf_pn2.pt

Outputs (to --out-dir, default docs/proposal/figures):
    woodleaf_comparison.csv
    fig17_woodleaf_pca_vs_pointnet.png

NOTE: held-out trees are still synthetic, so this measures the *relative*
PCA-vs-PointNet++ gain, not real-world accuracy. Real numbers need the
manually-labelled tree test set (see docs/P1_SPRINT_PLAN.md, G2).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

ML_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ML_ROOT))

from pipeline.wood_leaf_separation import WoodLeafSegmenter, segment_wood_leaf  # noqa: E402
from training.eval_woodleaf import (  # noqa: E402
    evaluate_segmenter,
    make_test_samples,
    read_comparison_csv,
)

DEFAULT_OUT = ML_ROOT.parent.parent / "docs" / "proposal" / "figures"


def _pca_labeler(points: np.ndarray) -> np.ndarray:
    return segment_wood_leaf(points, k_neighbors=15)


def run(model_path: str | None, n_test: int, n_points: int, out_dir: Path) -> dict:
    samples = make_test_samples(n_test=n_test, n_points=n_points)
    print(f"Built {len(samples)} held-out test trees (n_points={n_points})")

    results: dict[str, list[float]] = {"PCA (Phase 1)": evaluate_segmenter(_pca_labeler, samples)}

    if model_path:
        seg = WoodLeafSegmenter(model_path=str(model_path), backend="pointnet")
        seg.load()
        results["PointNet++ (Phase 2)"] = evaluate_segmenter(seg.segment, samples)
    else:
        print("(no --model given — PCA baseline only; pass a .pt for the full comparison)")

    _print_table(results)
    _write_csv(results, out_dir / "woodleaf_comparison.csv")
    _bar_chart(results, out_dir / "fig17_woodleaf_pca_vs_pointnet.png")
    return results


def _print_table(results: dict[str, list[float]]) -> None:
    print("\n" + "=" * 56)
    print(f"{'method':<24}{'mean IoU':>10}{'min':>8}{'max':>8}")
    print("-" * 56)
    for name, ious in results.items():
        a = np.array(ious)
        print(f"{name:<24}{a.mean():>10.4f}{a.min():>8.3f}{a.max():>8.3f}")
    if len(results) == 2:
        keys = list(results)
        delta = float(np.mean(results[keys[1]]) - np.mean(results[keys[0]]))
        print("-" * 56)
        print(f"PointNet++ - PCA  =  {delta:+.4f} IoU")
    print("(target: PointNet++ mean IoU >= 0.70 and > PCA)")


def _write_csv(results: dict[str, list[float]], out: Path) -> None:
    keys = list(results)
    n = len(results[keys[0]])
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tree_idx", *keys])
        for i in range(n):
            w.writerow([i, *[f"{results[k][i]:.4f}" for k in keys]])
    print(f"+ wrote {out}")


def _bar_chart(results: dict[str, list[float]], out: Path) -> None:
    import matplotlib.pyplot as plt

    forest, sky = "#2D6A4F", "#74C0FC"
    names = list(results)
    means = [float(np.mean(results[k])) for k in names]
    colors = [forest, sky][: len(names)]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    bars = ax.bar(names, means, color=colors, edgecolor="white", width=0.55, zorder=3)
    jitter = np.random.default_rng(0)
    for i, k in enumerate(names):
        ys = results[k]
        xs = np.full(len(ys), i) + jitter.uniform(-0.12, 0.12, len(ys))
        ax.scatter(xs, ys, color="#14140F", alpha=0.5, s=22, zorder=4)
    ax.axhline(0.70, color="#E63946", linestyle="--", label="target IoU = 0.70", zorder=2)
    for b, m in zip(bars, means, strict=True):
        ax.text(b.get_x() + b.get_width() / 2, m + 0.02, f"{m:.3f}", ha="center", fontweight="bold")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Wood IoU (held-out synthetic trees)")
    ax.set_title("Figure 17 — Wood-Leaf Segmentation: PCA vs PointNet++")
    ax.legend(loc="lower right")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"+ wrote {out}")


def main() -> None:
    p = argparse.ArgumentParser(description="Compare PCA vs PointNet++ wood-leaf (G2)")
    p.add_argument("--model", type=str, default=None, help="path to PointNet++ .pt (omit = PCA only)")
    p.add_argument("--from-csv", type=str, default=None,
                   help="re-plot fig17 from an existing woodleaf_comparison.csv (no model needed)")
    p.add_argument("--n-test", type=int, default=12)
    p.add_argument("--n-points", type=int, default=4096)
    p.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT))
    args = p.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.from_csv:
        results = read_comparison_csv(args.from_csv)
        _print_table(results)
        _bar_chart(results, out_dir / "fig17_woodleaf_pca_vs_pointnet.png")
        return

    run(args.model, args.n_test, args.n_points, out_dir)


if __name__ == "__main__":
    main()
