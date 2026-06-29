"""Convert real labelled TLS plots (Wan 2021) into PointNet++ training samples.

The synthetic trainer (``training.woodleaf_dataset``) makes single-tree samples
of a fixed size, normalised to the unit sphere. Real plots come as huge
``x y z R G B label`` text files (label col 6: 0=wood, 1=leaf). To fine-tune on
them we:

1. seek-sample the giant file (memory-safe) -> XYZ + per-point label
2. tile the plot into ~2.5 m cells (≈ single-tree scale) -> one sample per cell,
   resampled to a fixed point count and normalised to the unit sphere
3. split tiles **spatially** (held-out region with a buffer gap) so no tree
   appears in both train and test — an honest, leakage-free generalisation test

Run the converter LOCALLY (it streams the multi-GB files) -> a tiny ``.npz``
that uploads to Colab for GPU fine-tuning. Output label convention matches
``pipeline.wood_leaf_separation`` (WOOD=0, LEAF=1).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from training.woodleaf_dataset import _resample_indices, normalize_points


def tile_samples(
    points: np.ndarray,
    labels: np.ndarray,
    *,
    tile: float = 2.5,
    n_points: int = 2048,
    min_pts: int = 1024,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Split a plot into ~tile-sized cells; one normalised sample per cell.

    Args:
        points: (N, 3) XYZ
        labels: (N,) per-point class (0=wood, 1=leaf)
        tile: cell size in metres (XY grid)
        n_points: fixed sample size (resampled per cell)
        min_pts: drop cells with fewer raw points than this
        seed: RNG seed for the per-cell resample

    Returns:
        x: (M, n_points, 3) float32, each cell centroid-centered + unit-sphere scaled
        y: (M, n_points) int64 labels
        centers: (M, 2) raw XY centre of each cell (for spatial splitting)
    """
    points = np.asarray(points, dtype=np.float64)
    labels = np.asarray(labels)
    gx = np.floor(points[:, 0] / tile).astype(np.int64)
    gy = np.floor(points[:, 1] / tile).astype(np.int64)
    key = gx * 1_000_003 + gy
    rng = np.random.default_rng(seed)

    xs, ys, centers = [], [], []
    for k in np.unique(key):
        idx = np.where(key == k)[0]
        if len(idx) < min_pts:
            continue
        sel = idx[_resample_indices(len(idx), n_points, rng)]
        xs.append(normalize_points(points[sel]).astype(np.float32))
        ys.append(labels[sel].astype(np.int64))
        centers.append(points[idx, :2].mean(axis=0))

    if not xs:
        return (
            np.zeros((0, n_points, 3), np.float32),
            np.zeros((0, n_points), np.int64),
            np.zeros((0, 2), np.float64),
        )
    return np.stack(xs), np.stack(ys), np.stack(centers)


def spatial_split(
    x: np.ndarray,
    y: np.ndarray,
    centers: np.ndarray,
    *,
    frac: float = 0.7,
    buffer: float = 2.5,
    axis: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Split samples into train/test by a spatial cut with a buffer gap.

    Tiles whose centre falls in the buffer band around the cut line are dropped,
    guaranteeing train and test regions are spatially disjoint (no shared tree).

    Returns:
        (x_train, y_train, x_test, y_test)
    """
    c = centers[:, axis]
    lo, hi = float(c.min()), float(c.max())
    cut = lo + frac * (hi - lo)
    train = c < (cut - buffer / 2.0)
    test = c > (cut + buffer / 2.0)
    return x[train], y[train], x[test], y[test]


def load_wan_plot(
    path: str | Path,
    *,
    label_col: int = 6,
    n_off: int = 3000,
    per: int = 1000,
) -> tuple[np.ndarray, np.ndarray]:
    """Seek-sample a huge Wan plot text file -> (points (N,3), labels (N,)).

    Reads ``per`` contiguous lines at ``n_off`` offsets spread across the file
    (covers the whole plot spatially + both class blocks proportionally) without
    loading all ~30M points. Format: ``x y z R G B label``.
    """
    path = Path(path)
    size = path.stat().st_size
    xyz: list[tuple[float, float, float]] = []
    lab: list[int] = []
    with path.open("rb") as f:
        for k in range(n_off):
            f.seek(int(size * k / n_off))
            if k > 0:
                f.readline()  # drop partial line
            for _ in range(per):
                line = f.readline()
                if not line:
                    break
                p = line.split()
                if len(p) < label_col + 1:
                    continue
                try:
                    xyz.append((float(p[0]), float(p[1]), float(p[2])))
                    lab.append(int(float(p[label_col])))
                except ValueError:
                    continue
    return np.asarray(xyz, np.float64), np.asarray(lab, np.uint8)


def build(
    plot_paths: list[str | Path],
    out_train: str | Path,
    out_test: str | Path,
    *,
    tile: float = 2.5,
    n_points: int = 2048,
    min_pts: int = 1024,
    frac: float = 0.7,
    buffer: float = 2.5,
    label_col: int = 6,
    n_off: int = 3000,
    per: int = 1000,
) -> dict:
    """Convert plots -> per-plot spatial split -> concatenated train/test .npz."""
    xtr_l, ytr_l, xte_l, yte_l = [], [], [], []
    per_plot = {}
    for path in plot_paths:
        pts, lab = load_wan_plot(path, label_col=label_col, n_off=n_off, per=per)
        x, y, centers = tile_samples(
            pts, lab, tile=tile, n_points=n_points, min_pts=min_pts
        )
        xtr, ytr, xte, yte = spatial_split(x, y, centers, frac=frac, buffer=buffer)
        xtr_l.append(xtr)
        ytr_l.append(ytr)
        xte_l.append(xte)
        yte_l.append(yte)
        per_plot[Path(path).stem] = {"tiles": len(x), "train": len(xtr), "test": len(xte)}

    x_train, y_train = np.concatenate(xtr_l), np.concatenate(ytr_l)
    x_test, y_test = np.concatenate(xte_l), np.concatenate(yte_l)
    np.savez_compressed(out_train, x=x_train, y=y_train)
    np.savez_compressed(out_test, x=x_test, y=y_test)
    return {
        "per_plot": per_plot,
        "train_samples": len(x_train),
        "test_samples": len(x_test),
        "train_wood_frac": round(float(np.mean(y_train == 0)), 4) if len(y_train) else 0.0,
        "test_wood_frac": round(float(np.mean(y_test == 0)), 4) if len(y_test) else 0.0,
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Convert Wan plots -> PointNet++ train/test .npz")
    p.add_argument("--plots", nargs="+", required=True, help="Wan plot .txt files")
    p.add_argument("--out-train", default="wan_train.npz")
    p.add_argument("--out-test", default="wan_test.npz")
    p.add_argument("--tile", type=float, default=2.5)
    p.add_argument("--n-points", type=int, default=2048)
    p.add_argument("--min-pts", type=int, default=1024)
    p.add_argument("--frac", type=float, default=0.7, help="train fraction along the spatial cut")
    p.add_argument("--buffer", type=float, default=2.5, help="held-out gap (m) between train/test")
    p.add_argument("--label-col", type=int, default=6)
    p.add_argument("--n-off", type=int, default=3000, help="seek offsets across each plot file")
    p.add_argument("--per", type=int, default=1000, help="contiguous lines read per offset")
    return p


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()
    stats = build(
        args.plots, args.out_train, args.out_test,
        tile=args.tile, n_points=args.n_points, min_pts=args.min_pts,
        frac=args.frac, buffer=args.buffer, label_col=args.label_col,
        n_off=args.n_off, per=args.per,
    )
    print(stats)
    print(f"wrote {args.out_train} + {args.out_test}")
