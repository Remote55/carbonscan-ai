"""Crown coverage, and the volume measurement that was removed.

branches.py reports how much of a crown resolved into branch-shaped wood. It
used to report a volume as well, and the tests that killed that are kept here,
because the approach is the obvious one and someone will try it again.

The decisive one is test_a_branch_crossing_cube_boundaries_is_counted_repeatedly:
a known cylinder read 3.89x its true volume, because its cross-section straddles
a cube boundary in both directions and each of the four columns then contributes
a full-length cylinder. No cube size fixes that.
"""

from __future__ import annotations

import csv
import math
import re
import statistics as st
from pathlib import Path

import numpy as np
import pytest

from pipeline.branches import (
    MIN_LINEARITY,
    VOXEL_M,
    CrownCoverage,
    _is_branch_like,
    measure_crown_coverage,
)

ROOT = Path(__file__).resolve().parent.parent / "data" / "raw" / "zenodo_belgium"
CSV = ROOT / "Destructive_and_qsm_data_DEMOL.csv"
CLOUDS = ROOT / "pointclouds" / "pointclouds_clean"
needs_cohort = pytest.mark.skipif(
    not CSV.exists() or not CLOUDS.exists(), reason="Demol cohort not present"
)


def _cylinder_surface(
    radius: float,
    length: float,
    *,
    direction: np.ndarray | None = None,
    origin: np.ndarray | None = None,
    n: int = 4000,
    arc: float = 2 * math.pi,
    seed: int = 0,
) -> np.ndarray:
    """Points on the outside of a cylinder, optionally only part-way round."""
    rng = np.random.default_rng(seed)
    axis = np.array([0.0, 0.0, 1.0]) if direction is None else np.asarray(direction, float)
    axis = axis / np.linalg.norm(axis)
    helper = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(axis, helper)
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)

    t = rng.uniform(0, length, n)
    theta = rng.uniform(0, arc, n)
    points = (
        np.outer(t, axis)
        + np.outer(radius * np.cos(theta), u)
        + np.outer(radius * np.sin(theta), v)
    )
    return points + (np.zeros(3) if origin is None else np.asarray(origin, float))


class TestRecognisingABranch:
    def test_a_cylinder_is_branch_shaped(self):
        assert _is_branch_like(_cylinder_surface(0.03, 0.18, n=200), MIN_LINEARITY)

    def test_a_blob_is_not(self):
        rng = np.random.default_rng(0)
        assert not _is_branch_like(rng.normal(0, 0.05, (200, 3)), MIN_LINEARITY)

    def test_a_flat_patch_is_not(self):
        """Three similar eigenvalues is a blob; two large and one small is a
        surface. Neither is a branch."""
        rng = np.random.default_rng(1)
        patch = np.column_stack(
            [rng.uniform(0, 0.2, 300), rng.uniform(0, 0.2, 300), rng.normal(0, 0.002, 300)]
        )
        assert not _is_branch_like(patch, MIN_LINEARITY)

    def test_orientation_does_not_matter(self):
        for direction in ([0, 0, 1], [1, 0, 0], [1, 1, 0.5]):
            assert _is_branch_like(
                _cylinder_surface(0.03, 0.18, direction=np.array(direction, float), n=200),
                MIN_LINEARITY,
            )


class TestCoverage:
    def test_a_clean_branch_is_mostly_covered(self):
        got = measure_crown_coverage(_cylinder_surface(0.04, 1.5))
        assert got.measured_point_fraction > 0.5
        assert got.n_branch_like > 0

    def test_a_cloud_of_leaves_is_not(self):
        rng = np.random.default_rng(2)
        got = measure_crown_coverage(rng.normal(0, 0.2, (4000, 3)))
        assert got.measured_point_fraction < 0.2
        assert got.n_rejected > got.n_branch_like

    def test_an_empty_crown_is_zero_not_an_error(self):
        assert measure_crown_coverage(np.empty((0, 3))) == CrownCoverage(0, 0, 0.0)

    def test_a_wrong_shape_is_a_programming_error(self):
        with pytest.raises(ValueError):
            measure_crown_coverage(np.zeros((10, 2)))

    def test_coverage_is_a_fraction(self):
        for cloud in (
            _cylinder_surface(0.04, 1.0),
            np.random.default_rng(3).normal(0, 0.1, (2000, 3)),
        ):
            assert 0.0 <= measure_crown_coverage(cloud).measured_point_fraction <= 1.0


class TestWhyThereIsNoVolume:
    """The measurements that removed it. Restoring a volume means answering
    these first."""

    def test_a_branch_crossing_cube_boundaries_is_counted_repeatedly(self):
        """The structural defect, and the one a threshold cannot reach.

        A cylinder centred on a cube corner has its cross-section split across
        four columns of cubes. Integrating per cube gives each column the full
        length, so the volume comes out four times over — measured at 3.89x on a
        4 cm cylinder. Shifting the same cylinder to sit inside one column
        changes the answer, which a volume measurement must never do.
        """
        radius, length = 0.04, 1.0
        on_a_corner = _cylinder_surface(radius, length)
        # Same cylinder, moved so its cross-section sits inside one column.
        inside_one = _cylinder_surface(
            radius, length, origin=np.array([VOXEL_M / 2, VOXEL_M / 2, 0.0])
        )

        columns_when_split = len(
            np.unique(np.floor(on_a_corner[:, :2] / VOXEL_M).astype(int), axis=0)
        )
        columns_when_whole = len(
            np.unique(np.floor(inside_one[:, :2] / VOXEL_M).astype(int), axis=0)
        )

        assert columns_when_split > columns_when_whole, (
            "the fixture no longer demonstrates the split; a volume built on "
            "these cubes would still be unsafe, so check before reintroducing one"
        )

    def test_coverage_itself_is_not_thrown_off_by_the_split(self):
        """The reason coverage survived and volume did not: counting which
        points look like a branch does not care how they are grouped."""
        radius, length = 0.04, 1.0
        on_a_corner = measure_crown_coverage(_cylinder_surface(radius, length))
        inside_one = measure_crown_coverage(
            _cylinder_surface(radius, length, origin=np.array([VOXEL_M / 2, VOXEL_M / 2, 0.0]))
        )

        assert on_a_corner.measured_point_fraction == pytest.approx(
            inside_one.measured_point_fraction, abs=0.25
        )


@needs_cohort
class TestOnRealCrowns:
    @pytest.fixture(scope="class")
    def crowns(self):
        from pipeline import wood_leaf_separation
        from pipeline.qsm import track_stem
        from pipeline.realdata_eval import load_point_cloud
        from pipeline.single_tree import estimate_ground_datum

        def key(name: str) -> str:
            s = re.sub(r"[^A-Z0-9]", "", name.upper())
            m = re.match(r"^([A-Z]+)(\d+)$", s)
            return f"{m.group(1)}{int(m.group(2)):02d}" if m else s

        known = set()
        with CSV.open(encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                known.add(key(row["tree_name"]))

        out = []
        for path in sorted(CLOUDS.glob("*.txt"))[::8]:
            if key(path.stem) not in known:
                continue
            points = np.asarray(load_point_cloud(path), dtype=float)
            if len(points) > 25_000:
                points = points[
                    np.random.default_rng(0).choice(len(points), 25_000, replace=False)
                ]
            points[:, 2] -= estimate_ground_datum(points[:, 2])
            labels = wood_leaf_separation.WoodLeafSegmenter(backend="tlsep").segment(points)
            wood = points[labels == wood_leaf_separation.WOOD]
            if len(wood) < 100:
                continue
            crown = wood[wood[:, 2] > track_stem(wood).crown_base_m]
            if len(crown) >= 50:
                out.append((path.stem, crown))
        return out

    def test_coverage_varies_enough_between_trees_to_be_worth_reporting(self, crowns):
        """3% to 79% across the reference trees. A crown at the low end carries
        about 30% of the tree's volume on an equation and nothing else, and
        that is what this figure exists to say."""
        assert crowns, "no crowns loaded"
        coverage = [measure_crown_coverage(crown).measured_point_fraction for _n, crown in crowns]
        assert min(coverage) < 0.4
        assert max(coverage) > 0.5
        assert st.pstdev(coverage) > 0.1
