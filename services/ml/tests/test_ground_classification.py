"""Ground classification: correctness, and cost that follows the data.

This module had no test file. It also had a defect that only a test shaped
around cost would catch: the per-cell array was sized from the XY *extent* of
the cloud rather than from the number of points, so four points a hundred
kilometres apart asked for tens of gigabytes while four points a hundred metres
apart asked for under two. Every guard upstream bounds bytes, vertex count or a
200k subsample - none of them bounds extent, so a 200-byte file could take the
machine down.
"""

from __future__ import annotations

import tracemalloc

import numpy as np
import pytest

from pipeline.ground_classification import classify_ground_array


def _flat_plot(span: float, *, n: int = 400, seed: int = 0) -> np.ndarray:
    """A flat ground sheet of `n` points spread over `span` metres."""
    rng = np.random.default_rng(seed)
    xy = rng.uniform(0.0, span, size=(n, 2))
    z = rng.normal(0.0, 0.02, size=n)
    return np.column_stack([xy, z])


def _peak_mb(points: np.ndarray) -> float:
    tracemalloc.start()
    try:
        classify_ground_array(points)
        return tracemalloc.get_traced_memory()[1] / 1048576
    finally:
        tracemalloc.stop()


class TestCost:
    def test_memory_follows_point_count_not_map_extent(self) -> None:
        """Same four points, three plot sizes, comparable cost.

        Before the fix this ran 1.6 MB / 7.7 MB / 68.7 MB for spans of 100 m,
        1 km and 3 km - a 43x spread for identical input - and kept climbing
        with the square of the span.
        """
        corners = [
            np.array([[0, 0, 0], [s, 0, 0], [0, s, 0], [s, s, 1]], dtype=np.float64)
            for s in (100.0, 1_000.0, 10_000.0)
        ]
        peaks = [_peak_mb(c) for c in corners]

        assert max(peaks) < 5.0, f"peaks grew with extent: {peaks}"

    def test_a_tiny_file_spanning_a_country_does_not_allocate_a_country(self) -> None:
        """The reported attack: a handful of points 100 km apart.

        The old grid wanted 1e10 cells - about 75 GB for one float64 array -
        from a file of a few hundred bytes.
        """
        points = np.array(
            [[0.0, 0.0, 0.0], [1e5, 0.0, 0.0], [0.0, 1e5, 0.0], [1e5, 1e5, 1.0]],
            dtype=np.float64,
        )

        assert _peak_mb(points) < 5.0


class TestCorrectness:
    def test_finds_the_ground_sheet(self) -> None:
        ground = _flat_plot(30.0, n=500)
        canopy = ground.copy()
        canopy[:, 2] += 8.0
        points = np.vstack([ground, canopy])

        is_ground = classify_ground_array(points)

        assert is_ground[: len(ground)].all()
        assert not is_ground[len(ground) :].any()

    def test_follows_a_slope_rather_than_one_global_height(self) -> None:
        """A cell-local datum is the whole point: on sloping ground a single
        global minimum would call the uphill end canopy."""
        rng = np.random.default_rng(1)
        xy = rng.uniform(0.0, 40.0, size=(600, 2))
        ground = np.column_stack([xy, xy[:, 0] * 0.25])  # 25% slope
        canopy = ground.copy()
        canopy[:, 2] += 9.0

        is_ground = classify_ground_array(np.vstack([ground, canopy]))

        assert is_ground[:600].mean() > 0.95
        assert is_ground[600:].mean() < 0.05

    def test_result_does_not_move_when_the_survey_is_translated(self) -> None:
        """Shifting a plot to real-world coordinates must not change which
        points are ground - the grid is anchored to the cloud's own minimum."""
        # RUF005 is suppressed on both lines below: each `+` is a numpy
        # broadcast of a shape-(3,) offset over an (N, 3) array, not list
        # concatenation. The suggested `[*array, 0, 0, 7.0]` would build a list
        # of N+3 items instead.
        points = np.vstack([_flat_plot(30.0), _flat_plot(30.0) + [0, 0, 7.0]])  # noqa: RUF005
        shifted = points + [500_000.0, 4_200_000.0, 0.0]  # noqa: RUF005 — UTM-scale offset

        assert np.array_equal(
            classify_ground_array(points), classify_ground_array(shifted)
        )

    @pytest.mark.parametrize("n", [0, 1, 2])
    def test_handles_clouds_too_small_to_form_a_grid(self, n: int) -> None:
        points = np.zeros((n, 3), dtype=np.float64)

        result = classify_ground_array(points)

        assert result.shape == (n,)
        assert result.dtype == bool

    def test_rejects_input_that_is_not_xyz(self) -> None:
        with pytest.raises(ValueError):
            classify_ground_array(np.zeros((5, 2)))
