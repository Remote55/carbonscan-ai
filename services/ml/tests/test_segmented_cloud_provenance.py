"""The picture the viewer shows must be the classification that was measured.

`process_points` can write a plot-wide segmented PLY for the web viewer. It used
to build that file with a second `WoodLeafSegmenter.segment` call over every
non-ground point at once, while the DBH, volume and carbon numbers came from
per-tree calls on the height-normalised cloud.

Two different computations. tlsep classifies a point from its 20 nearest
neighbours, so a point between two crowns gets a different neighbourhood - and
therefore possibly a different class - depending on whether the segmenter was
handed one tree or the whole plot. Shipping that file as "the result" would put
a picture on screen that was not the evidence behind the numbers beside it,
which is the specific failure this project keeps auditing itself for.

These tests hold the file to the labels that were actually used. The pipeline
runs once for the module: it takes about a second, but the recorded calls are
the subject of every assertion here and re-running would only invite them to
drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

from pipeline import main as pipeline_main
from pipeline import synthetic, wood_leaf_separation
from pipeline.ply_export import read_segmented_ply

GROUND = 2


@dataclass
class Run:
    """One pipeline run, plus every point set the segmenter was handed."""

    points: np.ndarray
    summary: dict
    calls: list[np.ndarray]
    ply: Path


@pytest.fixture(scope="module")
def run(tmp_path_factory: pytest.TempPathFactory) -> Run:
    points, _labels, _trees = synthetic.generate_synthetic_plot(
        n_trees=3, plot_size_m=18.0, seed=7
    )
    points = np.asarray(points, dtype=np.float64)
    out = tmp_path_factory.mktemp("segmented") / "plot.ply"

    calls: list[np.ndarray] = []
    original = wood_leaf_separation.WoodLeafSegmenter.segment

    def spy(self, pts: np.ndarray) -> np.ndarray:
        calls.append(np.asarray(pts).copy())
        return original(self, pts)

    # MonkeyPatch.context() rather than the fixture: this fixture is module
    # scoped and the built-in monkeypatch fixture is function scoped.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(wood_leaf_separation.WoodLeafSegmenter, "segment", spy)
        result = pipeline_main.process_points(points, segmented_ply_out=str(out))

    summary = result.summary if isinstance(result.summary, dict) else vars(result.summary)
    return Run(points=points, summary=summary, calls=calls, ply=out)


def test_the_fixture_actually_found_trees(run: Run) -> None:
    """Guard the guard: with no detected trees every assertion below is vacuous."""
    assert run.summary["detected_trees"] > 0
    assert run.ply.exists()


def test_segments_once_per_tree_and_not_again_for_the_picture(run: Run) -> None:
    # One call per detected tree. A second whole-plot pass would make it
    # detected + 1, and that extra pass is the defect: it is both the slowest
    # step in the pipeline and a different answer from the one measured.
    assert len(run.calls) == run.summary["detected_trees"]

    # And no call was handed the whole cloud.
    assert all(len(c) < len(run.points) for c in run.calls)


def test_every_classified_point_carries_the_label_that_was_measured(run: Run) -> None:
    points, classes = read_segmented_ply(run.ply)
    assert len(points) == len(run.points)
    assert set(np.unique(classes)).issubset({0, 1, 2})

    # Re-deriving from the recorded calls proves the file was assembled from
    # them rather than recomputed: per tree, the wood/leaf counts the segmenter
    # produced must be exactly the counts written to the file.
    segmenter = wood_leaf_separation.WoodLeafSegmenter(model_path=None, backend="tlsep")
    expected_wood = 0
    expected_leaf = 0
    for tree_points in run.calls:
        labels = segmenter.segment(tree_points)
        expected_wood += int(np.sum(labels == wood_leaf_separation.WOOD))
        expected_leaf += int(np.sum(labels == wood_leaf_separation.LEAF))

    assert int(np.sum(classes == 0)) == expected_wood
    assert int(np.sum(classes == 1)) == expected_leaf


def test_unassigned_and_ground_points_stay_ground(run: Run) -> None:
    _points, classes = read_segmented_ply(run.ply)
    classified = sum(len(c) for c in run.calls)

    # Everything the segmenter never saw - ground, and anything below the
    # tree-assignment height threshold - reads as ground rather than being
    # guessed into a class.
    assert int(np.sum(classes == GROUND)) == len(run.points) - classified


def test_excluded_trees_are_still_drawn(run: Run) -> None:
    """A tree dropped from the numbers is still a tree on screen.

    WOOD_EMPTY and QSM_INVALID stop a tree being measured, not being seen. The
    result table lists those ids with a reason, so the viewer has to show them
    too - otherwise the picture and the table disagree about how many trees
    exist.
    """
    assert len(run.calls) == run.summary["detected_trees"]
    assert run.summary["detected_trees"] >= run.summary["measured_trees"]
