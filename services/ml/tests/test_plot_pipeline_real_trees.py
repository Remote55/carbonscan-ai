"""Stages 1-4 against real tree geometry.

test_synthetic_pipeline.py already covers these stages, but against clouds this
repository generates: trunks are cylinders and crowns are blobs, so it checks
that the pipeline finds cylinders and blobs. Its tolerances say as much —
watershed passes while detecting three times the true tree count, and DBH
passes at 40% error.

Here the trees are real TLS scans with tape-measured DBH and height, dropped at
known positions onto a sloped ground plane. Ground truth is exact by
construction: which points are ground, which tree each point belongs to, and
what each tree actually measures.

This configuration found a defect the synthetic suite could not. See
TestGroundCandidateIsRobust for the mechanism.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np
import pytest

from pipeline import (
    canopy_height_model,
    ground_classification,
    height_normalization,
    qsm,
    tree_segmentation,
    wood_leaf_separation,
)

ROOT = Path(__file__).resolve().parent.parent / "data" / "raw" / "zenodo_belgium"
CSV = ROOT / "Destructive_and_qsm_data_DEMOL.csv"
CLOUDS = ROOT / "pointclouds" / "pointclouds_clean"

TREES = ["FEXC16", "FEXC10", "FSYL1", "PSYLA5"]
SPACING_M = 14.0
POINTS_PER_TREE = 40_000
SLOPE = 0.05

needs_data = pytest.mark.skipif(
    not CSV.exists() or not all((CLOUDS / f"{n}.txt").exists() for n in TREES),
    reason="Demol cohort not present",
)


def _norm(name: str) -> str:
    s = re.sub(r"[^A-Z0-9]", "", name.upper())
    m = re.match(r"^([A-Z]+)(\d+)$", s)
    return f"{m.group(1)}{int(m.group(2)):02d}" if m else s


class Plot:
    """A plot of real trees, and the truth about it."""

    def __init__(self) -> None:
        from pipeline.realdata_eval import load_point_cloud

        taped = {}
        with CSV.open(encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                try:
                    taped[_norm(row["tree_name"])] = (
                        float(row["DBH"]),
                        float(row["TH_felled"]),
                    )
                except ValueError:
                    pass

        parts, labels = [], []
        self.truth: list[tuple[str, float, float]] = []
        for i, name in enumerate(TREES):
            pts = np.asarray(load_point_cloud(CLOUDS / f"{name}.txt"), dtype=float)
            rng = np.random.default_rng(i)
            if len(pts) > POINTS_PER_TREE:
                pts = pts[rng.choice(len(pts), POINTS_PER_TREE, replace=False)]
            pts = pts - [pts[:, 0].mean(), pts[:, 1].mean(), pts[:, 2].min()]
            ox, oy = (i % 2) * SPACING_M, (i // 2) * SPACING_M
            pts[:, 0] += ox
            pts[:, 1] += oy
            pts[:, 2] += SLOPE * ox  # stand it on the slope, not through it
            parts.append(pts)
            labels.append(np.full(len(pts), i, dtype=int))
            dbh, height = taped[_norm(name)]
            self.truth.append((name, dbh, height))

        gx, gy = np.meshgrid(
            np.linspace(-6, SPACING_M + 6, 190), np.linspace(-6, SPACING_M + 6, 190)
        )
        ground = np.column_stack([gx.ravel(), gy.ravel(), SLOPE * gx.ravel()])
        ground[:, 2] += np.random.default_rng(99).normal(0, 0.02, len(ground))

        self.points = np.vstack([ground, *parts])
        self.source = np.concatenate([np.full(len(ground), -1), *labels])
        self.is_ground = self.source == -1

        self.ground_mask = ground_classification.classify_ground_array(self.points)
        self.normalised = height_normalization.normalize_height_array(
            self.points, self.ground_mask
        )
        chm, transform = canopy_height_model.compute_chm_array(
            self.normalised, resolution=0.5, min_height=0.5
        )
        self.chm = chm
        labels_2d = tree_segmentation.watershed_segmentation(
            chm, min_height=3.0, min_distance=5
        )
        self.tree_ids = tree_segmentation.assign_points_to_trees(
            self.normalised, labels_2d, transform, min_height=0.2
        )
        self.clouds = tree_segmentation.extract_tree_points(self.normalised, self.tree_ids)


@pytest.fixture(scope="module")
def plot() -> Plot:
    return Plot()


@needs_data
class TestStage1Ground:
    def test_finds_all_the_ground(self, plot):
        tp = int((plot.ground_mask & plot.is_ground).sum())
        fn = int((~plot.ground_mask & plot.is_ground).sum())
        assert tp / (tp + fn) > 0.99

    def test_does_not_swallow_the_trees(self, plot):
        """The failure that broke DBH. At a percentile-based candidate this was
        0.758, and the 24% of tree points wrongly called ground lifted the
        interpolated surface about a metre under every stem."""
        tp = int((plot.ground_mask & plot.is_ground).sum())
        fp = int((plot.ground_mask & ~plot.is_ground).sum())
        assert tp / (tp + fp) > 0.95, "tree points are being classified as ground"


@needs_data
class TestStage2HeightNormalisation:
    def test_ground_ends_up_at_zero(self, plot):
        gz = plot.normalised[plot.is_ground, 2]
        assert abs(gz.mean()) < 0.05
        assert np.abs(gz).max() < 0.5

    def test_each_trunk_base_ends_up_at_zero(self, plot):
        """Not the same claim as the above. The ground can average out to zero
        across the plot while sitting a metre high underneath the trees, which
        is exactly what used to happen and what moves the 1.3 m slice."""
        for i, (name, _, _) in enumerate(plot.truth):
            base = plot.normalised[plot.source == i, 2].min()
            assert abs(base) < 0.30, f"{name} base sits at {base:+.2f} m"

    def test_heights_match_the_tape(self, plot):
        for i, (name, _, height) in enumerate(plot.truth):
            got = plot.normalised[plot.source == i, 2].max()
            assert abs(got - height) / height < 0.10, f"{name}: {got:.1f} vs {height:.1f}"


@needs_data
class TestStage3Chm:
    def test_peaks_at_the_tallest_tree(self, plot):
        tallest = max(h for _, _, h in plot.truth)
        assert abs(float(np.nanmax(plot.chm)) - tallest) / tallest < 0.10


@needs_data
class TestStage4Segmentation:
    def test_finds_exactly_the_trees_that_are_there(self, plot):
        """Exactly. The synthetic suite accepts up to three times the truth."""
        assert len(plot.clouds) == len(TREES)

    def test_each_segment_is_one_tree(self, plot):
        for tid, _cloud in plot.clouds.items():
            src = plot.source[plot.tree_ids == tid]
            src = src[src >= 0]
            assert len(src) > 0, f"segment {tid} is entirely ground"
            _, counts = np.unique(src, return_counts=True)
            assert counts.max() / len(src) > 0.98, f"segment {tid} mixes trees"

    def test_no_tree_is_split_across_segments(self, plot):
        owners = {}
        for tid in plot.clouds:
            src = plot.source[plot.tree_ids == tid]
            src = src[src >= 0]
            vals, counts = np.unique(src, return_counts=True)
            owners.setdefault(vals[counts.argmax()], []).append(tid)
        for tree, segs in owners.items():
            assert len(segs) == 1, f"tree {plot.truth[tree][0]} split into {segs}"


@needs_data
class TestEndToEndDbhThroughThePlot:
    """The measurement that matters, and the one the stage-by-stage checks exist
    to protect. Every one of these trees measures correctly in isolation; before
    the ground fix, two of the four did not measure correctly here."""

    def test_every_tree_measures_within_ten_percent_of_its_tape(self, plot):
        errors = {}
        for tid, cloud in plot.clouds.items():
            src = plot.source[plot.tree_ids == tid]
            src = src[src >= 0]
            vals, counts = np.unique(src, return_counts=True)
            name, dbh, _ = plot.truth[vals[counts.argmax()]]
            seg = wood_leaf_separation.WoodLeafSegmenter(backend="tlsep")
            wood = cloud[seg.segment(cloud) == wood_leaf_separation.WOOD]
            assert len(wood) > 0, f"{name}: no wood points"
            q = qsm.compute_qsm(wood, seed=tid)
            errors[name] = (q.dbh_cm, dbh, q.model_quality)
        for name, (got, taped, quality) in errors.items():
            assert abs(got - taped) / taped < 0.10, (
                f"{name}: {got:.1f} cm through the plot vs {taped:.1f} taped"
            )
            assert quality > 0.8, f"{name}: fit quality {quality:.2f}"


class TestGroundCandidateIsRobust:
    """The unit-level version, with no data files needed.

    A percentile answers "how far up are 5% of this cell's points", which is the
    ground only when the cell is mostly ground. Beneath a stem it is not.
    """

    def _cell(self, n_ground: int, n_tree: int) -> np.ndarray:
        rng = np.random.default_rng(0)
        ground = np.column_stack([
            rng.uniform(0, 1, n_ground),
            rng.uniform(0, 1, n_ground),
            rng.normal(0, 0.02, n_ground),
        ])
        trunk = np.column_stack([
            rng.normal(0.5, 0.05, n_tree),
            rng.normal(0.5, 0.05, n_tree),
            rng.uniform(0.5, 20.0, n_tree),
        ])
        return np.vstack([ground, trunk])

    def test_ground_is_found_under_a_dense_stem(self):
        points = self._cell(n_ground=50, n_tree=10_000)
        mask = ground_classification.classify_ground_array(points)
        found = points[mask, 2]
        assert len(found) > 0
        assert found.max() < 0.5, (
            f"ground candidate landed at {found.max():.2f} m — the estimator is "
            "tracking the trunk, not the floor"
        )

    def test_the_ratio_of_tree_to_ground_does_not_move_the_answer(self):
        levels = []
        for n_tree in (10, 100, 1_000, 10_000):
            points = self._cell(n_ground=50, n_tree=n_tree)
            mask = ground_classification.classify_ground_array(points)
            levels.append(float(points[mask, 2].max()))
        assert max(levels) - min(levels) < 0.2, f"ground level drifted: {levels}"

    def test_a_cell_holding_two_points_still_finds_the_lower_one(self):
        """The rank has to shrink on sparse cells and only shrink.

        A sweep can leave one ground and one canopy return in a cell. Asking
        for the 3rd lowest there returns the canopy — which is how the first
        version of this fix broke the sparse-plot tests.
        """
        rng = np.random.default_rng(4)
        xy = rng.uniform(0.0, 40.0, size=(600, 2))
        ground = np.column_stack([xy, xy[:, 0] * 0.25])
        # RUF005 suppressed: a numpy broadcast of a shape-(3,) offset over an
        # (N, 3) array, not list concatenation.
        canopy = ground + [0.0, 0.0, 9.0]  # noqa: RUF005
        mask = ground_classification.classify_ground_array(np.vstack([ground, canopy]))
        assert mask[:600].mean() > 0.95
        assert mask[600:].mean() < 0.05, "canopy in a two-point cell was called ground"

    def test_one_low_outlier_does_not_drag_the_cell_down(self):
        points = self._cell(n_ground=50, n_tree=200)
        points = np.vstack([points, [[0.5, 0.5, -5.0]]])
        mask = ground_classification.classify_ground_array(points)
        kept = points[mask, 2]
        assert kept.max() > -1.0, "a single ghost return took the whole cell with it"
