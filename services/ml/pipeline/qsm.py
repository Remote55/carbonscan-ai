"""Step 6: Quantitative Structure Model — DBH + volume from wood points.

Implementation (this file):
- DBH via RANSAC circle fit on a 1.3 m horizontal slice of wood points
- Height = max Z of all points (or wood points if leaves were excluded)
- Volume via the taper equation V = (π/4) × DBH² × H × form_factor, once with a
  stem-calibrated factor and once with a whole-tree one; the crown is reported
  as their difference. `estimate_volume_sectional` implements stacked-cylinder
  integration and is more faithful in principle, but is NOT what runs — see the
  note in compute_qsm for why.

Nothing here models a branch. Crown volume is an allometric expansion of the
stem cylinder, so it does not respond to what a particular crown looks like.
Future work: full branch-level cylinder QSM with cover sets (Raumonen 2013).

References:
- Raumonen et al. 2013 — TreeQSM (Remote Sensing, 5(2), 491-520)
- Cao et al. 2019 — Wood volume from taper equations (review)
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

import numpy as np

# Form factors: V_actual / V_cylinder, where V_cylinder = (π/4)·DBH²·H.
#
# Both are measured from the 65 destructively harvested trees in
# data/raw/zenodo_belgium (Demol et al.) — cylinder computed from the felled
# tree's own tape-measured DBH and height, so neither constant absorbs any
# error this pipeline makes. Leave-one-site-out, refitting on four sites and
# scoring the fifth, gives 12.8% MAPE for the stem factor and 10.6% for the
# total: the value is stable across sites (0.393-0.412 and 0.573-0.601), so it
# transfers rather than memorising a site.
#
# The previous single constant 0.50 was cited to an FAO range and matched
# neither quantity. It sat above 63 of 65 measured stem factors while the
# evaluation scored it against whole-tree volume, where it ran 13.4% low. Two
# errors in opposite directions, partially cancelling, reported as one number.
#
# ⚠️ Belgium: ash, beech, larch, Scots pine. No tropical hardwood has been
#    measured this way here. These are the best numbers we have, not universal
#    ones, and a Thai validation cohort should re-derive them.
STEM_FORM_FACTOR = 0.403
TOTAL_TREE_FORM_FACTOR = 0.587

# Below this RANSAC inlier ratio the circle does not describe the slice: at 0.20
# four out of five points sit off the fitted circle, so the radius it reports is
# not a measurement of anything. Not a percentile of some cohort - a statement
# about the fit. Over 65 Demol trees x 3 seeds the only measurement that fell
# below it was LXDC4 at ratio 0.160, which read 116.4 cm against a taped 23.6 cm.
# Median ratio across those 195 was 0.990 and the next lowest was 0.596, so the
# rule excludes failures and leaves difficult-but-real trees alone. Dropping
# that one measurement moves cohort MAE from 1.546 cm to 1.076 cm and worst-case
# error from 92.84 cm to 16.86 cm.
MIN_DBH_FIT_QUALITY = 0.20

# Kept so existing callers keep resolving; the stem factor is what it meant.
DEFAULT_FORM_FACTOR = STEM_FORM_FACTOR


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
    best_residual = float("inf")
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
        # Ties are common - many samples of 3 points describe near-identical
        # circles - and taking the first one made the result depend on draw
        # order. Break them on total residual, which does not.
        residual_sum = float(residuals.sum())
        if inliers > best_inliers or (inliers == best_inliers and residual_sum < best_residual):
            best_inliers = inliers
            best_residual = residual_sum
            best = (cx, cy, r)

    if best_inliers >= 3:
        # Refit on the consensus set. Without this the returned radius is the
        # circumcircle of the 3 sampled points - three points out of hundreds
        # decide the answer, so a different seed gives a different DBH. Measured
        # over 12 Demol trees x 8 seeds, that spread averaged 1.545 cm against a
        # reported cohort MAE of 1.167 cm: the noise was wider than the error it
        # was being judged by. Refitting is the standard final RANSAC step
        # (Fischler & Bolles 1981); sampling only has to find the inliers.
        cx, cy, r = best
        residuals = np.abs(np.hypot(xy[:, 0] - cx, xy[:, 1] - cy) - r)
        consensus = xy[residuals < inlier_tolerance]
        refined = _algebraic_circle_fit(consensus)
        if refined is not None and 0.01 <= refined[2] <= max_radius_m:
            # Accept only on evidence. The algebraic fit is biased when the
            # points cover a short arc, which is the normal TLS case - a scanner
            # sees one side of a trunk - and it answers such a set with an
            # enormous circle. Taking it on trust turned one tree into a 92 cm
            # DBH error on seed 2. Keeping it only when it explains at least as
            # many points means the refit can sharpen the estimate but never
            # replace a good one with a worse one.
            refined_residuals = np.abs(
                np.hypot(xy[:, 0] - refined[0], xy[:, 1] - refined[1]) - refined[2]
            )
            refined_inliers = int((refined_residuals < inlier_tolerance).sum())
            if refined_inliers >= best_inliers:
                best = refined
                best_inliers = refined_inliers

    return best[0], best[1], best[2], best_inliers / max(n, 1)


def _algebraic_circle_fit(xy: np.ndarray) -> tuple[float, float, float] | None:
    """Least-squares circle through all given points (Kasa). Closed form.

    Minimises Σ(x² + y² + Dx + Ey + F)², which is linear in D, E, F, so there
    is no iteration and no randomness. Returns None when the points are
    collinear or too few, leaving the caller's RANSAC estimate in place.
    """
    if len(xy) < 3:
        return None
    x, y = xy[:, 0], xy[:, 1]
    a = np.column_stack([x, y, np.ones(len(xy))])
    b = x**2 + y**2
    try:
        sol, *_ = np.linalg.lstsq(a, b, rcond=None)
    except np.linalg.LinAlgError:
        return None
    cx, cy = sol[0] / 2.0, sol[1] / 2.0
    disc = sol[2] + cx**2 + cy**2
    if not np.isfinite(disc) or disc <= 0:
        return None
    return float(cx), float(cy), float(np.sqrt(disc))


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


def estimate_volume_sectional(
    wood_points: np.ndarray,
    *,
    slice_thickness_m: float = 0.3,
    min_points_per_slice: int = 8,
    max_radius_m: float = 0.6,
    cluster_radius_m: float = 1.0,
    seed: int = 0,
) -> tuple[float, int]:
    """Sectional (stacked-cylinder) stem volume — TreeQSM-style.

    Slice the wood points into horizontal height bins, fit a robust circle to
    each bin to recover its radius, and sum the cylinder volumes
    ``V = Σ π · r_i² · Δh``. This follows the real taper profile up the stem
    instead of collapsing it into a single form factor, and so is markedly more
    accurate on tapered trees (cf. Raumonen et al. 2013).

    Args:
        wood_points: (N, 3) wood-only points, Z normalized so 0 = ground
        slice_thickness_m: vertical bin height (Δh)
        min_points_per_slice: skip bins with fewer points than this
        max_radius_m: maximum plausible trunk radius (passed to the circle fit)
        cluster_radius_m: keep only points within this distance of the slice
            median, so a single trunk is fitted even if stray branch points share
            the bin
        seed: RNG seed for the RANSAC circle fits (reproducible)

    Returns:
        (volume_m3, n_cylinders) — n_cylinders is the number of slices that
        produced a valid circle fit.
    """
    if wood_points.ndim != 2 or wood_points.shape[1] != 3:
        raise ValueError(f"Expected (N, 3) array, got {wood_points.shape}")
    if len(wood_points) == 0:
        return 0.0, 0

    z = wood_points[:, 2]
    z_min, z_max = float(z.min()), float(z.max())
    if z_max - z_min < slice_thickness_m:
        return 0.0, 0

    rng = np.random.default_rng(seed)
    edges = np.arange(z_min, z_max + slice_thickness_m, slice_thickness_m)
    volume = 0.0
    n_cyl = 0
    for lo, hi in pairwise(edges):
        mask = (z >= lo) & (z < hi)
        if int(mask.sum()) < min_points_per_slice:
            continue
        xy = wood_points[mask, :2]
        # Keep the densest cluster only → fit a single trunk per slice
        median_xy = np.median(xy, axis=0)
        near = np.hypot(xy[:, 0] - median_xy[0], xy[:, 1] - median_xy[1]) < cluster_radius_m
        if int(near.sum()) >= min_points_per_slice:
            xy = xy[near]
        _, _, r, _ = _ransac_circle_fit(xy, max_radius_m=max_radius_m, rng=rng)
        if r > 0:
            volume += float(np.pi * r * r * (hi - lo))
            n_cyl += 1
    return volume, n_cyl


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

    # Volume = two taper equations against the same cylinder, one calibrated to
    # harvested stem volume and one to harvested whole-tree volume. The crown is
    # their difference: this pipeline does not model branches, so what is
    # reported for them is an allometric expansion, not anything measured off
    # this tree's points. It replaces a hardcoded 0.0, which claimed the crown
    # had no volume — in the Demol cohort the crown is 30.3% of the tree.
    #
    # That expansion is a cohort mean over a quantity that ranges from 8% to
    # 56% (sd 12.9pp), so per-tree it is weak. It is right on average and can be
    # badly wrong on one tree, which is why `n_cylinders` stays 1: nothing here
    # was fitted to this tree's crown.
    #
    # NOTE: `estimate_volume_sectional` (stacked cylinders) is more accurate on
    # CLEAN stems (see its unit tests) but grossly overestimates on real TLS
    # whose rule-based wood/leaf split still leaves crown/branch points — each
    # high slice then fits a large "branch blob" circle. Adopting it as the
    # default needs (a) clean wood points from the trained PointNet++ (G2) and
    # (b) per-branch cylinder modelling. Tracked in docs/P1_SPRINT_PLAN.md (G3).
    stem_vol = estimate_volume_taper(dbh_cm, height_m, form_factor=STEM_FORM_FACTOR)
    total_vol = estimate_volume_taper(dbh_cm, height_m, form_factor=TOTAL_TREE_FORM_FACTOR)
    n_cylinders = 1
    branches_vol = max(0.0, total_vol - stem_vol)
    return QsmResult(
        dbh_cm=dbh_cm,
        height_m=height_m,
        stem_volume_m3=stem_vol,
        branches_volume_m3=branches_vol,
        total_volume_m3=stem_vol + branches_vol,
        n_cylinders=n_cylinders,
        model_quality=fit_q,
    )
