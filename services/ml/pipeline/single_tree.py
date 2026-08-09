"""Measure one tree, from a cloud that contains one tree.

The plot pipeline is the wrong tool for this. It classifies ground from a grid,
normalises heights against that surface, builds a canopy model and runs a
watershed to find stems — all of which need a plot. Handed a single tree it
finds one "tree" whose extent is the whole cloud, and the diameter it reports is
several times the truth.

The recipe was already in demol_eval, wrapped in evaluation scaffolding and not
callable from anywhere else. This is that recipe as an ordinary function, plus
the one thing an isolated cloud needs that a plot does not: somewhere to put
z = 0.

Reached by any upload that is one tree rather than a stand.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from pipeline import allometric, qsm, wood_leaf_separation

#: Height bin used when looking for the ground under a single tree.
GROUND_BIN_M = 0.05
#: A bin has to hold at least this share of the cloud, or this many points,
#: before its floor counts as ground rather than as a stray return.
GROUND_MIN_SHARE = 0.0005
GROUND_MIN_POINTS = 5

ExclusionReason = Literal["EMPTY_CLOUD", "WOOD_EMPTY", "QSM_INVALID", "QSM_LOW_FIT_QUALITY"]


@dataclass(frozen=True)
class SingleTreeResult:
    """One tree's measurement, or the reason there isn't one."""

    dbh_cm: float | None
    height_m: float | None
    stem_volume_m3: float | None
    branches_volume_m3: float | None
    total_volume_m3: float | None
    model_quality: float | None
    ground_datum_m: float | None
    point_count: int
    wood_point_count: int
    carbon: allometric.CarbonResult | None
    excluded_reason: ExclusionReason | None = None

    @property
    def measured(self) -> bool:
        return self.excluded_reason is None


def estimate_ground_datum(
    z: np.ndarray,
    *,
    bin_m: float = GROUND_BIN_M,
    min_share: float = GROUND_MIN_SHARE,
    min_points: int = GROUND_MIN_POINTS,
) -> float:
    """The lowest height that has company.

    demol_eval uses ``min(z)``, and on the clean cohort clouds that is the most
    accurate choice there is: DBH error 0.797 cm against 4.5 cm for a rank-based
    datum, because skipping the lowest points on a single tree walks the datum
    up into the root flare and moves the 1.3 m slice with it.

    It is also brittle in exactly one way. Add a single return 1.5 m below the
    trunk — the kind a scanner or a bad SfM point produces — and every one of
    those 21 trees stopped measuring at all: z = 0 sits below the stump, so the
    breast-height slice cuts empty air.

    Taking the floor of the lowest *populated* bin keeps the accuracy and drops
    the brittleness: 0.837 cm clean, 0.839 cm with the ghost return, all 21
    still measured.
    """
    if len(z) == 0:
        raise ValueError("cannot estimate a ground datum from an empty cloud")
    low, high = float(np.min(z)), float(np.max(z))
    if high - low < bin_m:
        return low

    edges = np.arange(low, high + bin_m, bin_m)
    counts, _ = np.histogram(z, bins=edges)
    needed = max(min_points, int(min_share * len(z)))
    populated = np.nonzero(counts >= needed)[0]
    if len(populated) == 0:
        # Nothing anywhere clears the bar - a very sparse cloud. The plain
        # minimum is then the honest answer rather than a refusal.
        return low

    first = int(populated[0])
    in_bin = z[(z >= edges[first]) & (z < edges[first] + bin_m)]
    return float(np.min(in_bin)) if len(in_bin) else float(edges[first])


def measure_single_tree(
    points: np.ndarray,
    *,
    species_sci: str | None = None,
    wood_leaf_backend: str = "tlsep",
    model_path: str | None = None,
    seed: int = 0,
) -> SingleTreeResult:
    """Measure one tree and cost its carbon.

    Args:
        points: (N, 3) XYZ for a single tree, in metres, any vertical offset.
        species_sci: scientific name, if known. Unknown is the normal case and
            costs the tree with Chave at a default density — see
            allometric.CARBON_VALIDATION_NOTE for what that is worth.
        wood_leaf_backend: "tlsep" (default) or "pointnet".
        model_path: checkpoint, required only for the pointnet backend.
        seed: RNG seed for the RANSAC circle fits.

    Returns:
        A SingleTreeResult. Check ``measured`` before reading the numbers: a
        cloud that cannot be measured says so with a reason code rather than
        returning a plausible-looking zero.
    """
    points = np.asarray(points, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"Expected (N, 3) array, got {points.shape}")

    def excluded(reason: ExclusionReason, **extra: object) -> SingleTreeResult:
        base: dict[str, object] = {
            "dbh_cm": None,
            "height_m": None,
            "stem_volume_m3": None,
            "branches_volume_m3": None,
            "total_volume_m3": None,
            "model_quality": None,
            "ground_datum_m": None,
            "point_count": len(points),
            "wood_point_count": 0,
            "carbon": None,
            "excluded_reason": reason,
        }
        base.update(extra)
        return SingleTreeResult(**base)  # type: ignore[arg-type]

    if len(points) == 0:
        return excluded("EMPTY_CLOUD")

    datum = estimate_ground_datum(points[:, 2])
    normalised = points.copy()
    normalised[:, 2] -= datum

    segmenter = wood_leaf_separation.WoodLeafSegmenter(
        model_path=model_path, backend=wood_leaf_backend
    )
    if wood_leaf_backend == "pointnet":
        segmenter.load()
    labels = segmenter.segment(normalised)
    wood = normalised[labels == wood_leaf_separation.WOOD]
    if len(wood) == 0:
        return excluded("WOOD_EMPTY", ground_datum_m=datum)

    measurement = qsm.compute_qsm(wood, seed=seed)
    if measurement.dbh_cm <= 0 or measurement.height_m <= 0:
        return excluded("QSM_INVALID", ground_datum_m=datum, wood_point_count=len(wood))
    if measurement.model_quality < qsm.MIN_DBH_FIT_QUALITY:
        # Same bar as the plot path. A circle that does not describe the stem
        # produces a diameter, and reporting it is how one tree contributes a
        # 90 cm error to a cohort whose typical error is about 1 cm.
        return excluded(
            "QSM_LOW_FIT_QUALITY", ground_datum_m=datum, wood_point_count=len(wood)
        )

    carbon = allometric.calculate_carbon(
        dbh_cm=measurement.dbh_cm,
        height_m=measurement.height_m,
        species_sci=species_sci,
    )
    return SingleTreeResult(
        dbh_cm=measurement.dbh_cm,
        height_m=measurement.height_m,
        stem_volume_m3=measurement.stem_volume_m3,
        branches_volume_m3=measurement.branches_volume_m3,
        total_volume_m3=measurement.total_volume_m3,
        model_quality=measurement.model_quality,
        ground_datum_m=datum,
        point_count=len(points),
        wood_point_count=len(wood),
        carbon=carbon,
    )
