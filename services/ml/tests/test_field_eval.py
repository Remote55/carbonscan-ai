"""Tests for Thai field ground-truth validation helpers (Sprint P1 / G1).

Pure logic only (no matplotlib) so it runs on any machine. The plotting +
CLI live in notebooks/validate_thai.py.
"""

from __future__ import annotations

import numpy as np

from pipeline.field_eval import (
    circumference_to_dbh,
    error_metrics,
    load_point_cloud,
    load_point_cloud_with_source_count,
    normalize_ground,
    predict_tree,
)

# --- circumference_to_dbh --------------------------------------------------


def test_circumference_to_dbh():
    # tape girth of a 20 cm-DBH stem is π·20 ≈ 62.83 cm
    assert abs(circumference_to_dbh(np.pi * 20.0) - 20.0) < 1e-9


def test_circumference_to_dbh_zero_or_negative():
    assert circumference_to_dbh(0.0) == 0.0
    assert circumference_to_dbh(-5.0) == 0.0


# --- error_metrics ---------------------------------------------------------


def test_error_metrics_perfect():
    m = error_metrics([10.0, 20.0], [10.0, 20.0])
    assert m["n"] == 2
    assert m["mae"] == 0.0
    assert m["rmse"] == 0.0
    assert m["abs_mean_pct"] == 0.0


def test_error_metrics_known_values():
    # pred 11 vs gt 10 -> +1 (+10%);  pred 18 vs gt 20 -> -2 (-10%)
    m = error_metrics([11.0, 18.0], [10.0, 20.0])
    assert abs(m["mae"] - 1.5) < 1e-9          # (|+1| + |-2|) / 2
    assert abs(m["rmse"] - np.sqrt((1 + 4) / 2)) < 1e-9
    assert abs(m["abs_mean_pct"] - 10.0) < 1e-9  # (10 + 10) / 2
    assert abs(m["mean_pct"] - 0.0) < 1e-9       # (+10 - 10) / 2


def test_error_metrics_empty():
    m = error_metrics([], [])
    assert m["n"] == 0


# --- load_point_cloud / normalize_ground -----------------------------------


def test_load_point_cloud_txt(tmp_path):
    p = tmp_path / "tree.txt"
    np.savetxt(p, np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]], dtype=float))
    pts = load_point_cloud(p)
    assert pts.shape == (3, 3)
    assert pts.dtype == np.float64


def test_load_point_cloud_unsupported(tmp_path):
    p = tmp_path / "tree.weird"
    p.write_text("nope")
    try:
        load_point_cloud(p)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


class TestTheDiscardedPointsAreCounted:
    """A thinned cloud has to say it was thinned.

    load_point_cloud drops everything over max_points by uniform random choice,
    and process_points reported len(points) as `n_input_points`. A
    five-million-point scan was therefore published as a 200,000-point one,
    with nothing in the result recording that 96% of the file never reached a
    measurement — a number that is true about the array and wrong about the
    file.
    """

    @staticmethod
    def _cloud(tmp_path, n):
        path = tmp_path / "plot.txt"
        rng = np.random.default_rng(0)
        np.savetxt(path, rng.uniform(0, 10, (n, 3)))
        return path

    def test_the_source_count_survives_the_thinning(self, tmp_path):
        path = self._cloud(tmp_path, 500)

        points, source = load_point_cloud_with_source_count(path, max_points=100)

        assert len(points) == 100
        assert source == 500, "the file's own size was lost"

    def test_an_untouched_cloud_reports_its_own_length(self, tmp_path):
        path = self._cloud(tmp_path, 40)

        points, source = load_point_cloud_with_source_count(path, max_points=100)

        assert len(points) == 40
        assert source == 40

    def test_the_old_signature_still_returns_just_the_array(self, tmp_path):
        """Every existing caller passes this straight into numpy."""
        path = self._cloud(tmp_path, 40)

        points = load_point_cloud(path, max_points=100)

        assert isinstance(points, np.ndarray)
        assert points.shape == (40, 3)


def test_normalize_ground_sets_min_z_zero():
    pts = np.array([[0, 0, 5.0], [1, 1, 7.0], [2, 2, 6.0]])
    out = normalize_ground(pts)
    assert abs(out[:, 2].min()) < 1e-9


# --- predict_tree (integration on a synthetic tree) ------------------------


def test_predict_tree_on_synthetic_is_plausible():
    from pipeline.synthetic import generate_synthetic_plot

    pts, _, _ = generate_synthetic_plot(n_trees=1, seed=1)
    pred = predict_tree(normalize_ground(pts))
    assert set(pred) >= {"dbh_cm", "height_m", "volume_m3", "fit_quality"}
    assert pred["dbh_cm"] > 0
    assert 5.0 < pred["height_m"] < 30.0
    assert pred["volume_m3"] > 0
