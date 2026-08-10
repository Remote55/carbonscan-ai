"""measure_single_tree, against trees whose diameter was measured with a tape.

Two claims are checked here rather than repeated: that the plot pipeline is the
wrong tool for one tree, and that the ground datum this module uses survives a
stray low return without giving up the accuracy of a plain minimum.
"""

from __future__ import annotations

import csv
import re
import statistics as st
from pathlib import Path

import numpy as np
import pytest

from pipeline.single_tree import estimate_ground_datum, measure_single_tree

ROOT = Path(__file__).resolve().parent.parent / "data" / "raw" / "zenodo_belgium"
CSV = ROOT / "Destructive_and_qsm_data_DEMOL.csv"
CLOUDS = ROOT / "pointclouds" / "pointclouds_clean"

needs_data = pytest.mark.skipif(
    not CSV.exists() or not CLOUDS.exists(), reason="Demol cohort not present"
)


def _norm(name: str) -> str:
    s = re.sub(r"[^A-Z0-9]", "", name.upper())
    m = re.match(r"^([A-Z]+)(\d+)$", s)
    return f"{m.group(1)}{int(m.group(2)):02d}" if m else s


@pytest.fixture(scope="module")
def taped() -> dict[str, float]:
    out: dict[str, float] = {}
    with CSV.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                out[_norm(row["tree_name"])] = float(row["DBH"])
            except ValueError:
                pass
    return out


@pytest.fixture(scope="module")
def sample_trees(taped) -> list[tuple[str, np.ndarray, float]]:
    """A handful of real clouds, subsampled so the suite stays quick."""
    from pipeline.realdata_eval import load_point_cloud

    picked: list[tuple[str, np.ndarray, float]] = []
    for name in ("FEXC16", "FEXC10", "FSYL1", "PSYLA5"):
        path = CLOUDS / f"{name}.txt"
        if not path.exists() or _norm(name) not in taped:
            continue
        pts = np.asarray(load_point_cloud(path), dtype=float)
        if len(pts) > 25_000:
            pts = pts[np.random.default_rng(0).choice(len(pts), 25_000, replace=False)]
        picked.append((name, pts, taped[_norm(name)]))
    return picked


class TestGroundDatum:
    def test_a_clean_cloud_lands_on_its_own_minimum(self):
        rng = np.random.default_rng(0)
        z = np.concatenate([rng.normal(0.0, 0.01, 500), rng.uniform(1.0, 15.0, 5_000)])
        assert estimate_ground_datum(z) == pytest.approx(float(z.min()), abs=0.02)

    def test_a_lone_return_below_the_stump_is_ignored(self):
        """The failure mode of min(z). One ghost point put z = 0 below the
        trunk base, so the 1.3 m slice cut empty air and every tree in the
        sample stopped measuring."""
        rng = np.random.default_rng(1)
        z = np.concatenate([rng.normal(0.0, 0.01, 500), rng.uniform(1.0, 15.0, 5_000)])
        with_ghost = np.append(z, -1.5)
        assert estimate_ground_datum(with_ghost) == pytest.approx(
            estimate_ground_datum(z), abs=0.02
        )

    def test_a_handful_of_ghosts_are_still_ignored(self):
        rng = np.random.default_rng(2)
        z = np.concatenate([rng.normal(0.0, 0.01, 500), rng.uniform(1.0, 15.0, 5_000)])
        assert estimate_ground_datum(np.append(z, [-2.0, -1.7, -1.2])) == pytest.approx(
            estimate_ground_datum(z), abs=0.02
        )

    def test_a_real_low_surface_is_not_mistaken_for_a_ghost(self):
        """Sloping ground is a populated band, not a stray point. The datum has
        to follow it down, or a tree on a slope reads short."""
        rng = np.random.default_rng(3)
        z = np.concatenate([rng.uniform(-0.6, 0.0, 800), rng.uniform(1.0, 15.0, 5_000)])
        assert estimate_ground_datum(z) < -0.5

    def test_an_empty_cloud_is_refused_rather_than_guessed(self):
        with pytest.raises(ValueError):
            estimate_ground_datum(np.array([]))


@needs_data
class TestAgainstTapeMeasurements:
    def test_every_sampled_tree_measures_within_ten_percent(self, sample_trees):
        assert sample_trees, "no clouds loaded"
        for name, points, truth in sample_trees:
            result = measure_single_tree(points)
            assert result.measured, f"{name}: {result.excluded_reason}"
            assert abs(result.dbh_cm - truth) / truth < 0.10, (
                f"{name}: {result.dbh_cm:.1f} cm against a taped {truth:.1f}"
            )

    def test_the_plot_pipeline_cannot_measure_one_tree(self, sample_trees):
        """The reason this module exists, measured rather than asserted.

        process_points classifies ground from a grid and runs a watershed to
        find stems. Given one tree there is no plot for either step to work with.

        This asserted, until MIN_DBH_FIT_QUALITY was raised to 0.80, that the
        plot path answered with a diameter several times the truth. It no longer
        answers: two of these clouds are invisible to the watershed, and on the
        other two the breast-height circle explains so little of its slice
        (quality 0.31 and 0.41) that the gate refuses it. Both of those refused
        fits were in fact close - 2.5% and 8.3% out - which is the cost recorded
        in qsm.MIN_DBH_FIT_QUALITY, not an argument against the gate: on the
        population the plot path is actually for, a 16-tree plot, the same
        threshold drops one 14 cm error and no accurate measurement at all.

        Refusing is the better failure, because an exclusion is reported as an
        exclusion. It is still a failure, and it is still why this module exists.
        """
        from pipeline.main import process_points

        single_errors, plot_errors = [], []
        for _name, points, truth in sample_trees:
            single = measure_single_tree(points)
            if single.measured:
                single_errors.append(abs(single.dbh_cm - truth) / truth)
            plot = process_points(points)
            for tree in plot.trees:
                plot_errors.append(abs(tree.dbh_cm - truth) / truth)

        assert len(single_errors) == len(sample_trees), (
            f"the single-tree path measured {len(single_errors)} of "
            f"{len(sample_trees)} clouds"
        )
        assert st.mean(single_errors) < 0.10
        assert len(plot_errors) < len(single_errors), (
            f"the plot path measured {len(plot_errors)} of these single-tree "
            f"clouds against the single-tree path's {len(single_errors)} — if it "
            "has caught up, this module may no longer be needed"
        )

    def test_a_ghost_return_does_not_stop_a_measurement(self, sample_trees):
        for name, points, truth in sample_trees:
            haunted = np.vstack(
                [points, [points[:, 0].mean(), points[:, 1].mean(), points[:, 2].min() - 1.5]]
            )
            result = measure_single_tree(haunted)
            assert result.measured, f"{name} stopped measuring: {result.excluded_reason}"
            assert abs(result.dbh_cm - truth) / truth < 0.10


class TestRefusals:
    def test_an_empty_cloud_reports_why(self):
        result = measure_single_tree(np.empty((0, 3)))
        assert not result.measured
        assert result.excluded_reason == "EMPTY_CLOUD"
        assert result.dbh_cm is None, "a refusal must not look like a measurement of zero"

    def test_a_flat_sheet_has_no_stem_to_measure(self):
        rng = np.random.default_rng(4)
        sheet = np.column_stack(
            [rng.uniform(0, 5, 3_000), rng.uniform(0, 5, 3_000), rng.normal(0, 0.01, 3_000)]
        )
        result = measure_single_tree(sheet)
        assert not result.measured
        assert result.carbon is None

    def test_a_wrong_shape_is_a_programming_error_not_a_refusal(self):
        with pytest.raises(ValueError):
            measure_single_tree(np.zeros((10, 2)))


@needs_data
class TestCarbon:
    def test_carbon_comes_back_with_its_uncertainty(self, sample_trees):
        _name, points, _truth = sample_trees[0]
        result = measure_single_tree(points)
        assert result.measured and result.carbon is not None
        assert result.carbon.co2eq_low_kg < result.carbon.co2eq_kg < result.carbon.co2eq_high_kg
        assert result.carbon.uncertainty_basis

    def test_naming_the_species_narrows_the_range(self, sample_trees):
        _name, points, _truth = sample_trees[0]
        unknown = measure_single_tree(points).carbon
        known = measure_single_tree(points, species_sci="Tectona grandis").carbon
        assert unknown is not None and known is not None
        unknown_width = (unknown.co2eq_high_kg - unknown.co2eq_low_kg) / unknown.co2eq_kg
        known_width = (known.co2eq_high_kg - known.co2eq_low_kg) / known.co2eq_kg
        assert known_width < unknown_width
