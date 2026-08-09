"""Step 6b: how much of a crown a scan actually resolved into branches.

This module reports coverage, not volume. It once returned a volume, and the
reason it no longer does is worth keeping, because the attempt is the obvious
one and someone will make it again.

WHY CROWN VOLUME IS NOT MEASURED HERE

Crown volume is the last quantity in this pipeline that no point touches. It is
reported as a fitted whole-tree equation minus the measured stem, which scores
54.2% MAPE against the felled trees: unbiased on average at -1.8% and close to
useless per tree, landing between 0.21x and 3.24x the truth. Meanwhile the
clouds carry 1,251 to 27,571 wood points above the crown base. There was plenty
to measure.

The approach tried here was cover sets: chop the crown into 20 cm cubes, find
each cube's local axis by PCA, recover a radius, and integrate. It measured
89.6% MAPE against harvested crown volume — worse than the estimate it was meant
to replace.

Two things are wrong with it, and only the first is the one you would guess.

Where a crown is dense, one cube holds several branches. PCA finds a single axis
through all of them and one fat cylinder replaces several thin ones. Requiring
the distances to cluster, as a single cylinder's would, does not rescue it:
tightening that test walks the bias from +30% to -20% to -66% to -98% without
ever finding a stable middle. A sweep with no plateau is a method measuring the
wrong thing.

The larger error is structural, and a test on a known cylinder is what exposed
it. A 4 cm cylinder straddles a cube boundary in both x and y, so its
cross-section is split across four columns of cubes — and each column then
contributes a cylinder of the *full* 20 cm length. The volume comes out four
times over. Measured: a full-arc cylinder read 3.89x its true volume. No cube
size fixes this, because a branch that crosses a boundary is the normal case,
not the exception.

Doing it properly means what TreeQSM (Raumonen 2013) does: extract a skeleton,
trace each branch as one object, and fit cylinders along its own axis so that
nothing is ever counted twice or merged with its neighbour. That is a project of
its own, and the literature is candid that TLS branch volume stays hard even
after it.

WHAT IS KEPT

Whether a cube's points look like a branch at all is a sound question, and the
answer is independent of the volume bookkeeping that was wrong. Across the
reference trees, the share of crown points that resolve into branch-shaped wood
runs from 3% to 79%. That is a fact about the scan, not the tree, and a crown at
3% is one whose ~30% share of the tree's volume rests entirely on an equation.
compute_qsm reports it beside the numbers so the difference is visible.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: Edge length of the cubes the crown is chopped into before each is examined.
#:
#: Small enough that a branch inside one is close to straight, large enough to
#: hold the points needed to find its axis.
VOXEL_M = 0.20

#: A cube with fewer points than this cannot say where its axis points.
MIN_POINTS_PER_VOXEL = 8

#: How elongated a cube's points must be before they count as branch-shaped.
#:
#: PCA on a cylinder gives one long eigenvalue and two short ones. A leaf clump,
#: a scan artefact, or the interior of a dense crown gives three similar ones.
#: Same linearity test the wood/leaf split uses, asked for a different purpose:
#: not "is this wood" but "is this wood shaped like a branch".
MIN_LINEARITY = 0.45


@dataclass(frozen=True)
class CrownCoverage:
    """How much of a crown resolved into branch-shaped wood."""

    #: Cubes whose points look like a branch.
    n_branch_like: int
    #: Cubes that held points but were too sparse or too blobby.
    n_rejected: int
    #: Share of crown points inside a branch-like cube. Low means the scan did
    #: not resolve this crown, whatever the estimated volume says.
    measured_point_fraction: float


def _is_branch_like(points: np.ndarray, min_linearity: float) -> bool:
    """Do these points lie along one direction, the way a branch does?"""
    if len(points) < 3:
        return False
    centred = points - points.mean(axis=0)
    try:
        _, singular, _ = np.linalg.svd(centred, full_matrices=False)
    except np.linalg.LinAlgError:  # pragma: no cover - numerical pathology
        return False
    if singular[0] <= 0:
        return False
    eigenvalues = singular**2 / max(len(points) - 1, 1)
    if eigenvalues[0] <= 0:
        return False
    linearity = float((eigenvalues[0] - eigenvalues[1]) / eigenvalues[0])
    return linearity >= min_linearity


def measure_crown_coverage(
    crown_points: np.ndarray,
    *,
    voxel_m: float = VOXEL_M,
    min_points_per_voxel: int = MIN_POINTS_PER_VOXEL,
    min_linearity: float = MIN_LINEARITY,
) -> CrownCoverage:
    """How much of this crown the scan resolved into branch-shaped wood.

    Args:
        crown_points: (N, 3) wood points above the stem. Leaves must already be
            gone; this looks at whatever it is given.

    Returns:
        CrownCoverage. Deliberately no volume — see the module docstring.
    """
    points = np.asarray(crown_points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"Expected (N, 3) array, got {points.shape}")
    if len(points) == 0:
        return CrownCoverage(0, 0, 0.0)

    keys = np.floor(points / voxel_m).astype(np.int64)
    _, inverse = np.unique(keys, axis=0, return_inverse=True)
    order = np.argsort(inverse, kind="stable")
    sorted_cells = inverse[order]
    boundaries = np.concatenate(
        [[0], np.where(np.diff(sorted_cells) != 0)[0] + 1, [len(sorted_cells)]]
    )

    branch_like = 0
    rejected = 0
    covered_points = 0
    for start, end in zip(boundaries[:-1], boundaries[1:], strict=True):
        member = order[start:end]
        if len(member) < min_points_per_voxel or not _is_branch_like(
            points[member], min_linearity
        ):
            rejected += 1
            continue
        branch_like += 1
        covered_points += len(member)

    return CrownCoverage(
        n_branch_like=branch_like,
        n_rejected=rejected,
        measured_point_fraction=float(covered_points / len(points)),
    )
