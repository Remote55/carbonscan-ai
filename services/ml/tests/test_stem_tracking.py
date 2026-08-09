"""Following a stem upward, instead of fitting whatever lands in each slice.

estimate_volume_sectional integrates every slice independently and overestimates
harvested stem volume by 4.5x to 19x — 934% MAPE. The radius profiles say why,
and it is not the reason the code used to give. On FEXC1, taped radius 13.7 cm,
the slices read 18, 14, 13, 13, 12, 12, 11, 9, 9, 8 cm up to 13.5 m: an
excellent taper. Then 15.0 m reads 59 cm.

The stem is measured well. The crown is measured as a stem. Better wood/leaf
separation cannot fix that, because branches *are* wood — which is why this is a
tracking problem and not a classification one.
"""

from __future__ import annotations

import csv
import math
import re
import statistics as st
from pathlib import Path

import numpy as np
import pytest

from pipeline import qsm
from pipeline.qsm import compute_qsm, estimate_volume_sectional, track_stem

ROOT = Path(__file__).resolve().parent.parent / "data" / "raw" / "zenodo_belgium"
CSV = ROOT / "Destructive_and_qsm_data_DEMOL.csv"
CLOUDS = ROOT / "pointclouds" / "pointclouds_clean"
needs_cohort = pytest.mark.skipif(
    not CSV.exists() or not CLOUDS.exists(), reason="Demol cohort not present"
)


def _cone(base_radius: float, top_radius: float, height: float, *, n: int = 6000,
          lean: float = 0.0, seed: int = 0) -> np.ndarray:
    """A tapering trunk, optionally leaning, with points only on its surface."""
    rng = np.random.default_rng(seed)
    z = rng.uniform(0, height, n)
    r = base_radius + (top_radius - base_radius) * (z / height)
    theta = rng.uniform(0, 2 * math.pi, n)
    x = r * np.cos(theta) + lean * z
    y = r * np.sin(theta)
    return np.column_stack([x, y, z])


def _branch_spray(at_height: float, reach: float, *, n: int = 3000, seed: int = 1) -> np.ndarray:
    """Wood that is not stem: branches radiating out at one height."""
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2 * math.pi, n)
    radius = rng.uniform(0.3, reach, n)
    z = at_height + rng.uniform(0, 4.0, n)
    return np.column_stack([radius * np.cos(theta), radius * np.sin(theta), z])


class TestOnAKnownShape:
    def test_recovers_the_volume_of_a_clean_cone(self):
        # Frustum volume: (pi*h/3)(R^2 + Rr + r^2)
        base, top, height = 0.20, 0.05, 12.0
        expected = math.pi * height / 3 * (base**2 + base * top + top**2)

        profile = track_stem(_cone(base, top, height))

        assert profile.volume_m3 == pytest.approx(expected, rel=0.15)
        assert profile.n_cylinders > 20

    def test_follows_a_leaning_trunk(self):
        upright = track_stem(_cone(0.18, 0.06, 12.0))
        leaning = track_stem(_cone(0.18, 0.06, 12.0, lean=0.06))

        assert leaning.volume_m3 == pytest.approx(upright.volume_m3, rel=0.2)
        assert leaning.n_cylinders > 20

    def test_stops_where_the_crown_starts(self):
        """The whole point. A stem to 10 m with branches above it must not be
        integrated as though the branches were trunk."""
        stem = _cone(0.18, 0.08, 10.0)
        crown = _branch_spray(at_height=10.0, reach=3.0)

        profile = track_stem(np.vstack([stem, crown]))

        assert profile.crown_base_m < 12.0, "tracking ran on into the crown"
        assert profile.volume_m3 < 2.0 * track_stem(stem).volume_m3

    def test_the_old_integrator_does_not(self):
        """Kept as the contrast, so the reason this module exists stays visible
        rather than becoming folklore in a comment."""
        stem = _cone(0.18, 0.08, 10.0)
        crown = _branch_spray(at_height=10.0, reach=3.0)
        together = np.vstack([stem, crown])

        tracked = track_stem(together).volume_m3
        per_slice, _ = estimate_volume_sectional(together)

        assert per_slice > tracked * 2, (
            "the per-slice integrator no longer overestimates; if that is real, "
            "this module's justification needs rewriting"
        )


class TestRefusals:
    def test_an_empty_cloud_yields_nothing_rather_than_raising(self):
        profile = track_stem(np.empty((0, 3)))
        assert profile.volume_m3 == 0.0
        assert profile.n_cylinders == 0

    def test_a_flat_sheet_has_no_stem(self):
        rng = np.random.default_rng(0)
        sheet = np.column_stack(
            [rng.uniform(0, 4, 2000), rng.uniform(0, 4, 2000), rng.normal(0, 0.01, 2000)]
        )
        assert track_stem(sheet).n_cylinders == 0

    def test_a_wrong_shape_is_a_programming_error(self):
        with pytest.raises(ValueError):
            track_stem(np.zeros((10, 2)))

    def test_a_stem_too_short_to_track_falls_back_in_compute_qsm(self):
        """A sapling still gets a volume, from the taper equation, and says so
        by reporting a single cylinder."""
        stub = _cone(0.05, 0.04, 0.4, n=400)
        result = compute_qsm(stub)
        assert result.n_cylinders == 1
        assert result.stem_volume_m3 >= 0.0


class TestPlausibilityRules:
    def test_the_axis_rule_stops_tracking_hopping_to_a_neighbour(self):
        """Behaviour, not a threshold. The search window alone is not enough:
        it looks three radii out, which on a 15 cm stem reaches 45 cm, and a
        circle fitted inside that can sit well off the trunk. The axis rule is
        what keeps the walk on one stem."""
        stem = _cone(0.15, 0.06, 12.0, seed=0)
        neighbour = _cone(0.15, 0.06, 12.0, seed=1) + np.array([0.6, 0.0, 0.0])
        together = np.vstack([stem, neighbour])

        alone = track_stem(stem)
        crowded = track_stem(together)

        # Tracking one stem in company must not measure both of them.
        assert crowded.volume_m3 < alone.volume_m3 * 1.6

    def test_a_radius_may_not_balloon_going_up(self):
        assert qsm.MAX_RADIUS_GROWTH < 1.5, "a stem that widens by half is not a stem"

    def test_the_axis_may_lean_but_not_jump(self):
        assert qsm.MAX_AXIS_SHIFT_PER_SLICE_M < 0.5

    def test_one_bad_slice_is_an_occlusion_not_the_crown(self):
        assert qsm.CROWN_BASE_PATIENCE >= 2


@needs_cohort
class TestAgainstFelledTrees:
    """Measured against Volume_stem_harvested. These numbers are quoted in
    qsm.py; pinning them here stops them rotting into folklore."""

    @pytest.fixture(scope="class")
    def measured(self):
        from pipeline import wood_leaf_separation
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
                    truth[key(row["tree_name"])] = float(row["Volume_stem_harvested"]) / 1000.0
                except ValueError:
                    pass

        out = []
        for path in sorted(CLOUDS.glob("*.txt"))[::6]:
            expected = truth.get(key(path.stem))
            if expected is None:
                continue
            points = np.asarray(load_point_cloud(path), dtype=float)
            if len(points) > 25_000:
                points = points[
                    np.random.default_rng(0).choice(len(points), 25_000, replace=False)
                ]
            points[:, 2] -= estimate_ground_datum(points[:, 2])
            labels = wood_leaf_separation.WoodLeafSegmenter(backend="tlsep").segment(points)
            wood = points[labels == wood_leaf_separation.WOOD]
            if len(wood) >= 100:
                out.append((path.stem, wood, expected))
        return out

    def test_stem_volume_lands_within_about_fifteen_percent(self, measured):
        assert measured, "no clouds loaded"
        errors = [
            abs(track_stem(wood).volume_m3 - expected) / expected
            for _name, wood, expected in measured
        ]
        assert st.mean(errors) < 0.20, f"documented as about 12.7%, measured {st.mean(errors):.1%}"

    def test_and_the_per_slice_integrator_is_an_order_of_magnitude_worse(self, measured):
        tracked = st.mean(
            abs(track_stem(wood).volume_m3 - expected) / expected
            for _name, wood, expected in measured
        )
        per_slice = st.mean(
            abs(estimate_volume_sectional(wood)[0] - expected) / expected
            for _name, wood, expected in measured
        )
        assert per_slice > tracked * 10

    def test_most_real_trees_are_actually_tracked(self, measured):
        """If the fallback fires everywhere, the measurement is not happening
        and the reported accuracy belongs to the taper equation."""
        tracked = sum(
            1 for _name, wood, _ in measured if compute_qsm(wood).n_cylinders > 1
        )
        assert tracked >= 0.8 * len(measured)
