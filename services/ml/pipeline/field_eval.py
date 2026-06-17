"""Field ground-truth validation helpers — Sprint P1 / G1.

Dependency-light, plotting-free functions to compare the pipeline's predictions
against hand-measured Thai field data (tape girth → DBH, clinometer height).
Used by ``notebooks/validate_thai.py``. Kept matplotlib-free so the logic is
unit-testable on any machine.

Field ground-truth CSV schema (one row per tree) — see the template at
``data/field/thai_ground_truth_TEMPLATE.csv``:

    tree_id, species_sci, circumference_cm, dbh_cm, height_m, point_cloud_file, notes

Provide either ``circumference_cm`` (tape girth) or ``dbh_cm`` directly.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# Columns the field team should record (documented for the CSV template)
GT_SCHEMA = [
    "tree_id",
    "species_sci",
    "circumference_cm",  # tape girth at 1.3 m (optional if dbh_cm given)
    "dbh_cm",            # diameter at breast height (optional if circumference given)
    "height_m",          # clinometer / Vertex height
    "point_cloud_file",  # filename in the point-cloud dir
    "notes",
]


def circumference_to_dbh(circumference_cm: float) -> float:
    """DBH from a tape-measured girth: DBH = circumference / π (cm)."""
    if circumference_cm <= 0:
        return 0.0
    return float(circumference_cm / np.pi)


def load_point_cloud(path: str | Path, max_points: int = 200_000) -> np.ndarray:
    """Load XYZ from a point-cloud file → (N, 3) float64.

    Supports the formats a mobile photogrammetry / LiDAR workflow produces:
        .txt / .xyz / .asc  — whitespace-separated XYZ
        .csv                — comma-separated XYZ
        .ply                — Open3D reader (COLMAP / OpenMVS output)
        .las / .laz         — laspy reader (TLS / drone LiDAR)
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".txt", ".xyz", ".asc"}:
        pts = np.atleast_2d(np.loadtxt(path))[:, :3].astype(np.float64)
    elif suffix == ".csv":
        pts = np.atleast_2d(np.loadtxt(path, delimiter=","))[:, :3].astype(np.float64)
    elif suffix == ".ply":
        import open3d as o3d  # lazy — heavy import

        pcd = o3d.io.read_point_cloud(str(path))
        pts = np.asarray(pcd.points, dtype=np.float64)
    elif suffix in {".las", ".laz"}:
        import laspy  # lazy

        las = laspy.read(str(path))
        pts = np.column_stack([las.x, las.y, las.z]).astype(np.float64)
    else:
        raise ValueError(f"Unsupported point cloud format: {suffix!r}")

    if len(pts) > max_points:
        rng = np.random.default_rng(0)
        pts = pts[rng.choice(len(pts), max_points, replace=False)]
    return pts


def normalize_ground(points: np.ndarray) -> np.ndarray:
    """Shift Z so the lowest point sits at 0 (ground baseline)."""
    out = np.asarray(points, dtype=np.float64).copy()
    out[:, 2] -= out[:, 2].min()
    return out


def predict_tree(points: np.ndarray, *, k_neighbors: int = 15, seed: int = 0) -> dict:
    """Run wood/leaf separation + QSM on one (normalised) tree cloud.

    Returns a dict with dbh_cm, height_m, volume_m3, fit_quality, wood_frac.
    """
    from pipeline import qsm, wood_leaf_separation

    labels = wood_leaf_separation.segment_wood_leaf(points, k_neighbors=k_neighbors)
    wood = points[labels == wood_leaf_separation.WOOD]
    res = qsm.compute_qsm(wood, seed=seed)
    return {
        "dbh_cm": res.dbh_cm,
        "height_m": res.height_m,
        "volume_m3": res.total_volume_m3,
        "fit_quality": res.model_quality,
        "wood_frac": len(wood) / max(len(points), 1),
    }


def error_metrics(pred: list[float] | np.ndarray, gt: list[float] | np.ndarray) -> dict:
    """Paired error summary: n, MAE, RMSE, signed mean %, absolute mean %."""
    pred = np.asarray(pred, dtype=float)
    gt = np.asarray(gt, dtype=float)
    if len(pred) == 0:
        return {"n": 0, "mae": 0.0, "rmse": 0.0, "mean_pct": 0.0, "abs_mean_pct": 0.0}
    err = pred - gt
    pct = err / gt * 100.0
    return {
        "n": len(pred),
        "mae": float(np.abs(err).mean()),
        "rmse": float(np.sqrt((err**2).mean())),
        "mean_pct": float(pct.mean()),
        "abs_mean_pct": float(np.abs(pct).mean()),
    }
