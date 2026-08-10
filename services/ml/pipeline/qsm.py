"""Step 6: Quantitative Structure Model — DBH + volume from wood points.

Implementation (this file):
- DBH via RANSAC circle fit on a 1.3 m horizontal slice of wood points
- Height = max Z of all points (or wood points if leaves were excluded)
- Stem volume by following the trunk upward disc by disc (`track_stem`) and
  integrating what is there. No constant fitted to any cohort.
- Whole-tree volume still via the taper equation V = (π/4) × DBH² × H ×
  form_factor, whose total factor was calibrated against harvested whole trees.
  Branch volume is the residual between the two.

So the stem is measured and the crown is estimated, because nothing here models
a branch. `estimate_volume_sectional` is the older per-slice integrator kept for
comparison; it fits every slice independently and overestimates real stems by
4.5x to 19x, which is what track_stem exists to fix.
Future work: full branch-level cylinder QSM with cover sets (Raumonen 2013).

References:
- Raumonen et al. 2013 — TreeQSM (Remote Sensing, 5(2), 491-520)
- Cao et al. 2019 — Wood volume from taper equations (review)
"""

from __future__ import annotations

import math
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

# The RANSAC inlier ratio a breast-height circle must reach to be reported.
#
# This was 0.20, argued as the floor below which a circle describes nothing: at
# 0.20 four out of five points sit off it, so the radius is not a measurement of
# anything. That argument is still correct, and it is still the wrong threshold,
# because a floor is not a detector. "Is this a circle at all" and "is this
# circle good enough to trust" are different questions, and the product needs
# the second one answered.
#
# Measured on the single-tree path (compute_qsm calls measure_dbh with the same
# arguments, so this is that path's own distribution) - 65 Demol trees x 3 seeds
# x 3 point densities of 200k, 12k and 4k per tree, spanning a single-tree upload
# down to one tree's share of a 50-tree plot. 585 fits against taped DBH:
#
#     gate    kept   good lost   bad kept    MAE cm   worst cm
#     0.20     584           0         13      1.56      64.67
#     0.70     564          11          4      1.14      59.74
#     0.78     557          14          0      0.98       3.41
#     0.80     552          19          0      0.97       3.41
#     0.90     510          61          0      0.95       3.41
#
# "bad" is an error over 5 cm. At 0.20 thirteen of them are reported as results,
# the worst reading 64.67 cm out on a taped stem - because a slice holding few
# points is EASY to fit: with fifteen points a circle can pass near all of them
# and still be the wrong circle. The ratio RISES as the measurement becomes
# meaningless, which is why the old gate went quiet exactly where it was needed.
#
# 0.78 is where the last bad fit is caught, and that is precisely why it is not
# the value used. It sits on the boundary of the worst case these 65 trees happen
# to contain (LXDC5 at 0.750, FEXC14 at 0.778); a 66th tree would move it. 0.80
# clears that boundary with a margin for 5 further fits out of 571 - 0.9%.
#
# The plot path is a different computation - a grid ground classifier, KNN-IDW
# normalisation and a watershed all run first - so it was measured separately, on
# a plot built the way tests/test_plot_pipeline_real_trees.py builds one: 16 real
# Demol scans stood at 14 m spacing on a sloped ground plane, 447,089 points,
# every stage running for real. All 16 detected and measured, and fit quality is
# bimodal: fifteen fits between 0.913 and 1.000, and FEXC14 at 0.537 reading
# 25.6 cm against a taped 39.8. Any gate from 0.60 to 0.90 drops that one and
# nothing else, moving plot MAE from 1.61 cm to 0.77 cm and worst-case error from
# 14.18 cm to 1.60 cm. On a real plot this threshold costs nothing at all.
#
# Feeding ONE tree to the plot path looks far worse - good and bad fits overlap
# between 0.10 and 0.69 there - but that is the misuse single_tree.py exists to
# replace, not evidence about this constant.
#
# The honest downgrade: 0.20 was a statement about arithmetic, true anywhere.
# 0.80 is fitted to 65 temperate trees and inherits every limit that cohort has
# - see allometric.CARBON_VALIDATION_NOTE.
#
# What it costs: two trees are now refused outright rather than measured. FEXC14
# is refused correctly - it reads 25-26 cm against a taped 39.8 on every seed,
# density and path, and was the single worst fit on the plot too. LXDC4 is the
# real loss: 22.6-23.6 cm against a taped 23.6, accurate, and gone, because its
# slice is messy enough that no fit explains much of it. An excluded tree is
# reported as excluded with its reason code in
# PipelineDiagnostics.excluded_segments. A tree that is 14 cm wrong is reported
# as a measurement.
MIN_DBH_FIT_QUALITY = 0.80

#: Crown volume as a multiple of stem volume, used only when the taper equation
#: contradicts the measurement.
#:
#: In the Demol cohort a whole tree is 1.489x its harvested stem, so the crown is
#: 0.489 stems. Between sites that runs 1.351 to 1.638 and between individuals
#: the crown is 8% to 56% of the tree, so it is a cohort mean, not a property of
#: any one tree. It is the fallback rather than the main route because expanding
#: a measured stem this way scores 17.7% against harvested whole-tree volume
#: where the taper equation scores 10.0%.
CROWN_EXPANSION = 0.489

#: Fewer discs than this and the stem was not really followed — a sapling, or a
#: scan too occluded to track. The taper equation answers instead, from DBH and
#: height alone.
MIN_TRACKED_CYLINDERS = 5

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
    n_cylinders: int  # discs integrated up the stem; 1 means the taper fallback
    model_quality: float  # 0-1 fit quality (RANSAC inlier ratio for DBH)
    #: Share of crown points that can be traced back to the trunk as branches.
    #:
    #: Not used to compute anything. pipeline/skeleton.py measures crown volume
    #: correctly on synthetic cylinders and is 1490% out on real crowns, because
    #: branches in a real crown cannot be told apart at this point density —
    #: which is why the volume stays with the equation. What the trace does say
    #: is how much of a crown holds together as followable wood at all: 0% to
    #: 73% across the reference trees. A crown at the low end is one whose ~30%
    #: share of the tree rests on an equation and nothing else.
    crown_resolved_fraction: float | None = None


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


# --- Stem tracking ---------------------------------------------------------
#
# How far a slice's centre may sit from where the slice below predicts it. A
# stem leans and sways; it does not teleport. Generous enough for a bent trunk,
# tight enough that a branch two metres out is not mistaken for it.
MAX_AXIS_SHIFT_PER_SLICE_M = 0.10
#: A stem tapers. Allowing a little growth absorbs noise and buttress flare;
#: allowing a lot lets the first branch whorl become the trunk.
MAX_RADIUS_GROWTH = 1.15
#: Consecutive unusable slices before the stem is declared finished. One bad
#: slice is an occlusion; three in a row is the crown.
CROWN_BASE_PATIENCE = 3
#: A slice's circle must explain at least this much of what it was given.
MIN_SLICE_FIT_QUALITY = 0.30


@dataclass
class StemProfile:
    """The stem as a stack of measured discs, and where it stopped being one."""

    volume_m3: float
    n_cylinders: int
    #: Height above ground where tracking gave up — the crown base, in effect.
    crown_base_m: float
    #: Radius at each accepted slice, bottom to top, in metres.
    radii_m: list[float]
    #: Fraction of the tree's height that was successfully tracked.
    tracked_fraction: float


def track_stem(
    wood_points: np.ndarray,
    *,
    slice_thickness_m: float = 0.3,
    min_points_per_slice: int = 8,
    max_radius_m: float = 0.6,
    seed: int = 0,
) -> StemProfile:
    """Follow one stem upward and integrate it, stopping where it becomes crown.

    ``estimate_volume_sectional`` fits each slice independently and sums
    everything. Measured on real TLS that overestimates harvested stem volume by
    4.5x to 19x — 934% MAPE against the taper equation's 11%.

    The radius profiles say exactly why, and it is not what the code used to
    claim. On FEXC1, taped radius 13.7 cm, the slices read 18, 14, 13, 13, 12,
    12, 11, 9, 9, 8 cm from the ground to 13.5 m: an excellent taper, tracking
    the truth to within a centimetre or two. Then 15.0 m reads 59 cm, and 18.0 m
    reads 53. The stem is measured well; the crown is measured as a stem.

    Better wood/leaf separation cannot fix this, because branches *are* wood. No
    classifier removes them. What is missing is the knowledge that a stem is one
    connected, roughly vertical, tapering thing:

    * its centre moves a little between slices, never metres
    * its radius shrinks going up, give or take noise
    * it ends, and above that end the tree is a crown, not a wider trunk

    So this starts at the base where the stem is unambiguous, and walks up
    predicting each slice from the one below. A slice that disagrees is not
    integrated, and enough disagreement in a row means the stem has finished.
    """
    if wood_points.ndim != 2 or wood_points.shape[1] != 3:
        raise ValueError(f"Expected (N, 3) array, got {wood_points.shape}")
    if len(wood_points) == 0:
        return StemProfile(0.0, 0, 0.0, [], 0.0)

    z = wood_points[:, 2]
    z_min, z_max = float(z.min()), float(z.max())
    tree_height = z_max - z_min
    if tree_height < slice_thickness_m:
        return StemProfile(0.0, 0, 0.0, [], 0.0)

    rng = np.random.default_rng(seed)
    edges = np.arange(z_min, z_max + slice_thickness_m, slice_thickness_m)

    centre: tuple[float, float] | None = None
    last_radius: float | None = None
    volume = 0.0
    radii: list[float] = []
    misses = 0
    crown_base = z_max

    for lo, hi in pairwise(edges):
        mask = (z >= lo) & (z < hi)
        if int(mask.sum()) < min_points_per_slice:
            misses += 1
            if last_radius is not None and misses >= CROWN_BASE_PATIENCE:
                crown_base = lo
                break
            continue

        xy = wood_points[mask, :2]
        if centre is None:
            # The first slice has nothing below it to be predicted from, so the
            # densest cluster is the best available guess at which blob is stem.
            anchor = np.median(xy, axis=0)
            window = max_radius_m
        else:
            anchor = np.array(centre)
            # Look only where the stem can plausibly be. Three radii out covers
            # lean and noise; it does not reach the next branch over.
            window = max(3.0 * (last_radius or max_radius_m), 0.15)

        near = np.hypot(xy[:, 0] - anchor[0], xy[:, 1] - anchor[1]) <= window
        if int(near.sum()) < min_points_per_slice:
            misses += 1
            if last_radius is not None and misses >= CROWN_BASE_PATIENCE:
                crown_base = lo
                break
            continue

        cx, cy, r, quality = _ransac_circle_fit(
            xy[near], max_radius_m=max_radius_m, rng=rng
        )

        plausible = (
            r > 0
            and quality >= MIN_SLICE_FIT_QUALITY
            and (last_radius is None or r <= last_radius * MAX_RADIUS_GROWTH)
            and (
                centre is None
                or math.hypot(cx - centre[0], cy - centre[1]) <= MAX_AXIS_SHIFT_PER_SLICE_M
            )
        )
        if not plausible:
            misses += 1
            if last_radius is not None and misses >= CROWN_BASE_PATIENCE:
                crown_base = lo
                break
            continue

        misses = 0
        centre = (cx, cy)
        last_radius = r
        radii.append(r)
        volume += float(np.pi * r * r * (hi - lo))

    tracked = (crown_base - z_min) / tree_height if tree_height > 0 else 0.0
    return StemProfile(
        volume_m3=volume,
        n_cylinders=len(radii),
        crown_base_m=float(crown_base - z_min),
        radii_m=radii,
        tracked_fraction=float(min(max(tracked, 0.0), 1.0)),
    )


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

    # Stem volume is measured, not assumed, whenever the stem can be followed.
    #
    # track_stem walks the trunk upward disc by disc and integrates what it
    # finds, so unlike the taper equation it has no constant fitted to any
    # cohort. On the 17 Demol trees checked it reaches 12.3% MAPE against
    # harvested stem volume, next to 11.1% for the taper equation whose form
    # factor was fitted to those same trees — a method with nothing fitted,
    # matching one that was, is the stronger of the two.
    #
    # That is the reason to prefer it, and it is not about this cohort. The form
    # factor is derived from four temperate genera and would have to be
    # re-derived from a destructive tropical harvest before it could be trusted
    # in the forests this product is aimed at. A measurement carries no such
    # debt.
    profile = track_stem(wood_points, seed=seed)
    tracked = profile.n_cylinders >= MIN_TRACKED_CYLINDERS and profile.volume_m3 > 0
    if tracked:
        stem_vol = profile.volume_m3
        n_cylinders = profile.n_cylinders
    else:
        # Too sparse or too short to follow — a young tree, a heavily occluded
        # scan. The taper equation needs only DBH and height, so it still
        # answers. n_cylinders stays 1 to mark which route produced this.
        stem_vol = estimate_volume_taper(dbh_cm, height_m, form_factor=STEM_FORM_FACTOR)
        n_cylinders = 1

    # Whole-tree volume stays with the taper equation, and the two quantities
    # come from different routes on purpose.
    #
    # Tracking the stem beats the taper equation at the stem — 12.7% MAPE
    # against harvested stem volume, with nothing fitted. Multiplying that stem
    # by a crown factor to reach a whole tree does not: 17.7% against 10.5% for
    # the taper equation, because the crown expansion amplifies the stem's error
    # and adds its own, while the total form factor was calibrated against
    # whole-tree volume directly.
    #
    # Which is the honest summary of where this pipeline stands: the stem can be
    # measured now, and the crown still cannot be measured at all. Nothing here
    # models a branch.
    #
    # Branch volume is therefore the residual — what the whole tree is estimated
    # to be, less what the stem was measured to be. On the reference trees the
    # tracked stem never exceeded the estimated total, and their ratio averaged
    # 0.708 against a harvested 0.672, so the decomposition holds together.
    # How much of the crown can be traced back to the trunk at all. A
    # diagnostic, not an input: the skeleton's volume is exact on synthetic
    # cylinders and 1490% out on real crowns, because branches in a real crown
    # cannot be told apart at this point density. See pipeline/skeleton.py.
    crown_points = wood_points[wood_points[:, 2] > profile.crown_base_m]
    crown_resolved: float | None = None
    if len(crown_points) >= 50:
        from pipeline.skeleton import trace_crown

        crown_resolved = trace_crown(
            crown_points,
            root_xyz=np.array(
                [
                    float(crown_points[:, 0].mean()),
                    float(crown_points[:, 1].mean()),
                    float(crown_points[:, 2].min()),
                ]
            ),
        ).traced_point_fraction

    total_vol = estimate_volume_taper(dbh_cm, height_m, form_factor=TOTAL_TREE_FORM_FACTOR)
    if total_vol > stem_vol:
        branches_vol = total_vol - stem_vol
    else:
        # The measured stem came out larger than the equation's whole tree,
        # which means this trunk is nothing like the shape that equation
        # describes — a near-cylinder, a pollard, a stem measured through
        # a fixture rather than a forest.
        #
        # Clamping the difference at zero would answer "this tree has no crown",
        # which is never true and never checked. Trust the measurement and
        # expand it by the cohort ratio instead. Rare in practice: across 21
        # reference trees the tracked stem never exceeded the estimated total.
        branches_vol = stem_vol * CROWN_EXPANSION
        total_vol = stem_vol + branches_vol
    return QsmResult(
        dbh_cm=dbh_cm,
        height_m=height_m,
        stem_volume_m3=stem_vol,
        branches_volume_m3=branches_vol,
        total_volume_m3=stem_vol + branches_vol,
        n_cylinders=n_cylinders,
        model_quality=fit_q,
        crown_resolved_fraction=crown_resolved,
    )
