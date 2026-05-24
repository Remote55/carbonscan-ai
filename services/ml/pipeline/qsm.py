"""Step 6: Quantitative Structure Model — DBH + volume from wood points.

Phase 1 implementation (this file):
- DBH via RANSAC circle fit on a 1.3 m horizontal slice of wood points
- Height = max Z of all points (or wood points if leaves were excluded)
- Volume via simple taper equation: V = (π/4) × DBH² × H × form_factor

Phase 2 will add full cylinder-tree QSM (Raumonen et al. 2013) for accurate
branch-level volume. For now the taper-equation estimate is the same form
used in operational forest inventory (~10-15% RMSE on real trees).

References:
- Raumonen et al. 2013 — TreeQSM (Remote Sensing, 5(2), 491-520)
- Cao et al. 2019 — Wood volume from taper equations (review)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Default form factor for tropical hardwood stems (FAO 2003 Forest Inventory)
# V_actual / V_cylinder ≈ 0.45-0.55 — we use the midpoint
DEFAULT_FORM_FACTOR = 0.50


@dataclass
class QsmResult:
    """QSM output for a single tree."""

    dbh_cm: float
    height_m: float
    stem_volume_m3: float
    branches_volume_m3: float
    total_volume_m3: float
    n_cylinders: int  # placeholder for Phase 2 — currently 1 (taper)
    model_quality: float  # 0-1 fit quality (RANSAC inlier ratio for DBH)


def _ransac_circle_fit(
    xy: np.ndarray,
    *,
    n_iterations: int = 200,
    inlier_tolerance: float = 0.02,
    max_radius_m: float = 0.6,
    rng: np.random.Generator | None = None,
) -> tuple[float, float, float, float]:
    """RANSAC circle fit on 2D points.

    Args:
        xy: (N, 2) 2D points
        n_iterations: Number of RANSAC iterations
        inlier_tolerance: Max residual (m) to count as inlier
        max_radius_m: Maximum plausible trunk radius (60 cm → DBH ≤ 120 cm)
        rng: RNG (seed reproducibility)

    Returns:
        (cx, cy, radius, inlier_ratio)
    """
    if rng is None:
        rng = np.random.default_rng(0)
    n = len(xy)
    if n < 3:
        return float(xy[:, 0].mean()), float(xy[:, 1].mean()), 0.0, 0.0

    best_inliers = 0
    best = (float(xy[:, 0].mean()), float(xy[:, 1].mean()), 0.0)
    for _ in range(n_iterations):
        idx = rng.choice(n, size=3, replace=False)
        p1, p2, p3 = xy[idx]
        # Circumcircle of 3 points
        a = p2 - p1
        b = p3 - p1
        d = 2 * (a[0] * b[1] - a[1] * b[0])
        if abs(d) < 1e-9:
            continue
        ux = (b[1] * (a[0] ** 2 + a[1] ** 2) - a[1] * (b[0] ** 2 + b[1] ** 2)) / d
        uy = (a[0] * (b[0] ** 2 + b[1] ** 2) - b[0] * (a[0] ** 2 + a[1] ** 2)) / d
        cx = p1[0] + ux
        cy = p1[1] + uy
        r = np.hypot(ux, uy)
        # Skip degenerate / unrealistic radii — real trunks: 1 cm to 60 cm radius
        if r > max_radius_m or r < 0.01:
            continue
        # Count inliers
        residuals = np.abs(np.hypot(xy[:, 0] - cx, xy[:, 1] - cy) - r)
        inliers = int((residuals < inlier_tolerance).sum())
        if inliers > best_inliers:
            best_inliers = inliers
            best = (cx, cy, r)

    return best[0], best[1], best[2], best_inliers / max(n, 1)


def measure_dbh(
    wood_points: np.ndarray,
    *,
    target_height_m: float = 1.3,
    slice_thickness_m: float = 0.3,
    seed: int = 0,
) -> tuple[float, float]:
    """Measure DBH via circle fit on a horizontal slice at breast height.

    Args:
        wood_points: (N, 3) array, Z already normalized so 0 = ground
        target_height_m: Sampling height (default 1.3 m = breast height)
        slice_thickness_m: Total slice thickness (±half)
        seed: RNG seed for RANSAC reproducibility

    Returns:
        (dbh_cm, fit_quality 0-1)
    """
    if wood_points.ndim != 2 or wood_points.shape[1] != 3:
        raise ValueError(f"Expected (N, 3) array, got {wood_points.shape}")

    half = slice_thickness_m / 2.0
    slice_mask = (
        (wood_points[:, 2] >= target_height_m - half)
        & (wood_points[:, 2] <= target_height_m + half)
    )
    slice_xy = wood_points[slice_mask, :2]
    if len(slice_xy) < 5:
        return 0.0, 0.0

    # If watershed over-segmented and this "tree" actually spans multiple real
    # trunks, the slice will be spatially multi-modal. Restrict the slice to
    # points within ~1 m of the densest cluster (median is robust to outliers)
    # before fitting — this picks out a single trunk.
    median_xy = np.median(slice_xy, axis=0)
    near_mask = np.hypot(slice_xy[:, 0] - median_xy[0], slice_xy[:, 1] - median_xy[1]) < 1.0
    if int(near_mask.sum()) >= 5:
        slice_xy = slice_xy[near_mask]

    rng = np.random.default_rng(seed)
    _, _, radius_m, inlier_ratio = _ransac_circle_fit(slice_xy, rng=rng)
    dbh_cm = radius_m * 2.0 * 100.0  # m → cm, diameter = 2r
    # Final sanity clip (real trunks rarely exceed 120 cm DBH at breast height
    # for the species in scope) — protects downstream allometric.
    dbh_cm = float(np.clip(dbh_cm, 0.0, 120.0))
    return dbh_cm, float(inlier_ratio)


def measure_height(points: np.ndarray) -> float:
    """Return the maximum Z (assumed height-above-ground) in meters."""
    if len(points) == 0:
        return 0.0
    return float(points[:, 2].max())


def estimate_volume_taper(
    dbh_cm: float,
    height_m: float,
    *,
    form_factor: float = DEFAULT_FORM_FACTOR,
) -> float:
    """Stem volume via taper equation: V = (π/4) × DBH² × H × form_factor.

    Returns volume in m³.
    """
    if dbh_cm <= 0 or height_m <= 0:
        return 0.0
    dbh_m = dbh_cm / 100.0
    return float(np.pi / 4.0 * dbh_m**2 * height_m * form_factor)


def compute_qsm(
    wood_points: np.ndarray,
    *,
    seed: int = 0,
) -> QsmResult:
    """Compute DBH + height + volume for one tree from its wood points.

    Args:
        wood_points: (N, 3) wood-only points, height-normalized

    Returns:
        QsmResult with DBH (cm), height (m), volumes (m³), fit quality.
    """
    if len(wood_points) == 0:
        return QsmResult(0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0)

    dbh_cm, fit_q = measure_dbh(wood_points, seed=seed)
    height_m = measure_height(wood_points)
    stem_vol = estimate_volume_taper(dbh_cm, height_m)
    # Phase 1: ignore separate branch volume — combined into stem taper
    branches_vol = 0.0
    return QsmResult(
        dbh_cm=dbh_cm,
        height_m=height_m,
        stem_volume_m3=stem_vol,
        branches_volume_m3=branches_vol,
        total_volume_m3=stem_vol + branches_vol,
        n_cylinders=1,
        model_quality=fit_q,
    )
