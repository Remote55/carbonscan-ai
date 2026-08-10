"""The crown tracer: right on geometry it can see, wrong on real crowns.

Both halves are pinned here. The synthetic tests say the algorithm is sound —
including the one-sided case a laser scan actually produces — and the cohort
test says it still loses to the equation it was built to replace. If someone
improves the input rather than the algorithm, the cohort test is what will tell
them when it finally wins.
"""

from __future__ import annotations

import csv
import math
import re
import statistics as st
from pathlib import Path

import numpy as np
import pytest

from pipeline.skeleton import (
    MAX_BRANCH_RADIUS_M,
    Skeleton,
    _geometric_circle_radius,
    build_cover_sets,
    trace_crown,
)

ROOT = Path(__file__).resolve().parent.parent / "data" / "raw" / "zenodo_belgium"
CSV = ROOT / "Destructive_and_qsm_data_DEMOL.csv"
CLOUDS = ROOT / "pointclouds" / "pointclouds_clean"
needs_cohort = pytest.mark.skipif(
    not CSV.exists() or not CLOUDS.exists(), reason="Demol cohort not present"
)


def _cylinder(
    radius: float,
    length: float,
    *,
    n: int = 6000,
    arc: float = 2 * math.pi,
    origin=(0.0, 0.0, 0.0),
    direction=(0.0, 0.0, 1.0),
    seed: int = 0,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    axis = np.asarray(direction, float)
    axis /= np.linalg.norm(axis)
    helper = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(axis, helper)
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    t = rng.uniform(0, length, n)
    theta = rng.uniform(0, arc, n)
    return (
        np.outer(t, axis)
        + np.outer(radius * np.cos(theta), u)
        + np.outer(radius * np.sin(theta), v)
        + np.asarray(origin, float)
    )


def _base_of(points: np.ndarray) -> np.ndarray:
    return np.array(
        [float(points[:, 0].mean()), float(points[:, 1].mean()), float(points[:, 2].min())]
    )


class TestOnGeometryItCanSee:
    def test_recovers_a_known_cylinder(self):
        points = _cylinder(0.04, 2.0)
        expected = math.pi * 0.04**2 * 2.0

        traced = trace_crown(points, root_xyz=np.array([0.0, 0.0, 0.0]))

        assert traced.volume_m3 == pytest.approx(expected, rel=0.2)
        assert traced.length_m == pytest.approx(2.0, rel=0.2)

    @pytest.mark.parametrize("arc", [2 * math.pi, math.pi, math.pi / 2], ids=["full", "half", "quarter"])
    def test_a_one_sided_scan_measures_the_same_branch(self, arc):
        """The case that matters. A scanner sees one side, and the section
        centroid then sits about 0.64 radii off the axis — which read 0.49x on a
        half arc and 0.14x on a quarter until the axis position was solved for
        instead of assumed."""
        expected = math.pi * 0.04**2 * 2.0

        traced = trace_crown(
            _cylinder(0.04, 2.0, arc=arc), root_xyz=np.array([0.0, 0.0, 0.0])
        )

        assert traced.volume_m3 == pytest.approx(expected, rel=0.35)

    def test_moving_it_off_the_grid_changes_nothing(self):
        """What the cube-based attempt could not do. A branch straddling a cube
        boundary was split across four columns and counted four times; cover
        sets follow the wood, so position is irrelevant."""
        at_origin = trace_crown(_cylinder(0.04, 2.0), root_xyz=np.array([0.0, 0.0, 0.0]))
        moved = trace_crown(
            _cylinder(0.04, 2.0, origin=(0.1, 0.13, 0.0)),
            root_xyz=np.array([0.1, 0.13, 0.0]),
        )

        assert moved.volume_m3 == pytest.approx(at_origin.volume_m3, rel=0.02)

    def test_a_fork_is_measured_once_per_branch(self):
        trunk = _cylinder(0.05, 1.0, n=3000)
        left = _cylinder(0.03, 1.0, n=2000, origin=(0, 0, 1.0), direction=(1, 0, 1), seed=2)
        right = _cylinder(0.03, 1.0, n=2000, origin=(0, 0, 1.0), direction=(-1, 0, 1), seed=3)
        expected = math.pi * 0.05**2 * 1.0 + 2 * math.pi * 0.03**2 * 1.0

        traced = trace_crown(
            np.vstack([trunk, left, right]), root_xyz=np.array([0.0, 0.0, 0.0])
        )

        assert traced.volume_m3 == pytest.approx(expected, rel=0.3)
        assert traced.length_m == pytest.approx(3.0, rel=0.25)

    def test_orientation_does_not_matter(self):
        upright = trace_crown(_cylinder(0.04, 2.0), root_xyz=np.array([0.0, 0.0, 0.0]))
        tilted_points = _cylinder(0.04, 2.0, direction=(1, 1, 1))
        tilted = trace_crown(tilted_points, root_xyz=tilted_points[np.argmin(tilted_points[:, 2])])

        assert tilted.volume_m3 == pytest.approx(upright.volume_m3, rel=0.3)


class TestTheCircleFit:
    def test_recovers_a_full_circle(self):
        theta = np.linspace(0, 2 * math.pi, 200, endpoint=False)
        circle = np.column_stack([0.05 * np.cos(theta), 0.05 * np.sin(theta)])
        assert _geometric_circle_radius(circle) == pytest.approx(0.05, rel=1e-3)

    def test_recovers_a_short_arc_too(self):
        """Where the algebraic fit fails. Kasa answers a short arc with an
        enormous circle — the same trap already guarded against in
        qsm._ransac_circle_fit — so this iterates on the geometry instead."""
        theta = np.linspace(0, math.pi / 3, 120)
        arc = np.column_stack([0.05 * np.cos(theta), 0.05 * np.sin(theta)])
        assert _geometric_circle_radius(arc) == pytest.approx(0.05, rel=0.25)

    def test_finds_a_circle_that_is_not_at_the_origin(self):
        theta = np.linspace(0, math.pi, 150)
        arc = np.column_stack([0.04 * np.cos(theta) + 3.0, 0.04 * np.sin(theta) - 2.0])
        assert _geometric_circle_radius(arc) == pytest.approx(0.04, rel=0.2)

    def test_too_few_points_is_refused(self):
        assert _geometric_circle_radius(np.zeros((2, 2))) is None


class TestCoverSets:
    def test_every_point_gets_exactly_one_set(self):
        points = _cylinder(0.04, 2.0, n=2000)
        labels, centres = build_cover_sets(points)

        assert len(labels) == len(points)
        assert labels.min() >= 0
        assert labels.max() == len(centres) - 1

    def test_patches_are_smaller_than_the_branch_is_long(self):
        points = _cylinder(0.04, 3.0, n=3000)
        _labels, centres = build_cover_sets(points)
        assert len(centres) > 5


class TestRefusals:
    def test_an_empty_crown_is_zero_not_an_error(self):
        assert trace_crown(np.empty((0, 3))) == Skeleton(0.0, 0, 0.0, 0.0, 0)

    def test_a_wrong_shape_is_a_programming_error(self):
        with pytest.raises(ValueError):
            trace_crown(np.zeros((10, 2)))

    def test_a_blob_traces_almost_nothing(self):
        """Foliage that survived the wood/leaf split has no axis to follow, and
        any circle fitted through it is wider than a branch."""
        rng = np.random.default_rng(0)
        traced = trace_crown(rng.normal(0, 0.3, (4000, 3)))
        assert traced.traced_point_fraction < 0.3

    def test_an_implausible_radius_is_dropped(self):
        assert MAX_BRANCH_RADIUS_M < 0.5, "a 50 cm branch is a trunk"


@needs_cohort
class TestTheNegativeResultOnRealCrowns:
    """Why the volume is not used. If these invert, revisit compute_qsm."""

    @pytest.fixture(scope="class")
    def crowns(self):
        from pipeline import wood_leaf_separation
        from pipeline.qsm import (
            TOTAL_TREE_FORM_FACTOR,
            estimate_volume_taper,
            measure_dbh,
            measure_height,
            track_stem,
        )
        from pipeline.realdata_eval import load_point_cloud
        from pipeline.single_tree import estimate_ground_datum

        def key(name: str) -> str:
            s = re.sub(r"[^A-Z0-9]", "", name.upper())
            m = re.match(r"^([A-Z]+)(\d+)$", s)
            return f"{m.group(1)}{int(m.group(2)):02d}" if m else s

        truth = {}
        with CSV.open(encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                try:
                    stem = float(row["Volume_stem_harvested"]) / 1000.0
                    total = float(row["Volume_total_tree_harvested"]) / 1000.0
                except ValueError:
                    continue
                if total > stem:
                    truth[key(row["tree_name"])] = total - stem

        out = []
        for path in sorted(CLOUDS.glob("*.txt"))[::8]:
            expected = truth.get(key(path.stem))
            if expected is None:
                continue
            points = np.asarray(load_point_cloud(path), dtype=float)
            if len(points) > 20_000:
                points = points[
                    np.random.default_rng(0).choice(len(points), 20_000, replace=False)
                ]
            points[:, 2] -= estimate_ground_datum(points[:, 2])
            labels = wood_leaf_separation.WoodLeafSegmenter(backend="tlsep").segment(points)
            wood = points[labels == wood_leaf_separation.WOOD]
            if len(wood) < 100:
                continue
            profile = track_stem(wood)
            crown = wood[wood[:, 2] > profile.crown_base_m]
            if len(crown) < 50:
                continue
            dbh, _q = measure_dbh(wood)
            estimated = max(
                0.0,
                estimate_volume_taper(
                    dbh, measure_height(wood), form_factor=TOTAL_TREE_FORM_FACTOR
                )
                - profile.volume_m3,
            )
            out.append((path.stem, crown, expected, estimated))
        return out

    def test_tracing_still_loses_to_the_equation(self, crowns):
        assert crowns, "no crowns loaded"
        traced_error = st.mean(
            abs(trace_crown(crown, root_xyz=_base_of(crown)).volume_m3 - expected) / expected
            for _n, crown, expected, _e in crowns
        )
        estimated_error = st.mean(
            abs(estimated - expected) / expected for _n, _c, expected, estimated in crowns
        )
        assert traced_error > estimated_error, (
            f"tracing now beats the equation ({traced_error:.1%} vs "
            f"{estimated_error:.1%}) — compute_qsm should stop treating this as "
            "a diagnostic only"
        )

    def test_the_traced_fraction_varies_enough_to_be_worth_reporting(self, crowns):
        """The part that ships. It says how much of a crown holds together as
        followable wood, which is a fact about the scan."""
        fractions = [
            trace_crown(crown, root_xyz=_base_of(crown)).traced_point_fraction
            for _n, crown, _e, _x in crowns
        ]
        assert min(fractions) < 0.3
        assert max(fractions) > 0.4
