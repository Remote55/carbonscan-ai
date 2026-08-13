"""Whether PointNet++ should replace tlsep, measured on the production path.

The promotion policy in scripts/sync_truth.py asks for five things:

    verified checkpoint and training provenance, a reproducible independent
    real-data evaluation, improved Wood IoU, non-regressing DBH/height/volume
    errors, and a candidate measurable-tree count at least as high as the
    baseline.

Wood IoU has been measured repeatedly and PointNet++ wins it — 0.32 against
tlsep's 0.19 on the held-out French cohort, with leaf IoU 0.85 against 0.31.
Every argument for promotion so far has rested on that number.

The two criteria about the measurements themselves had never been run. They are
what this file runs, against taped DBH and felled height on the Demol cohort,
and PointNet++ fails both. Wood IoU is a proxy; DBH is the product.

The cost of getting this wrong is concrete: the deployed image was built
deliberately without torch, and promoting the candidate puts roughly 530 MB of
it back for a pipeline that would not measure any better.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "raw" / "zenodo_belgium" / "Destructive_and_qsm_data_DEMOL.csv"
CLOUDS = ROOT / "data" / "raw" / "zenodo_belgium" / "pointclouds" / "pointclouds_clean"
CHECKPOINT = ROOT / "woodleaf_pn2.pt"

torch = pytest.importorskip("torch", reason="candidate backend needs torch")

needs_everything = pytest.mark.skipif(
    not CSV_PATH.exists() or not CLOUDS.exists() or not CHECKPOINT.exists(),
    reason="Demol cohort or candidate checkpoint absent",
)

#: Every fourth tree. The comparison is between two backends on the same trees,
#: so the sample size costs precision on the absolute error, not on the
#: difference — and the full cohort makes this file the slowest in the suite.
STEP = 4
MAX_POINTS = 20_000


def _key(name: str) -> str:
    s = re.sub(r"[^A-Z0-9]", "", name.upper())
    m = re.match(r"^([A-Z]+)(\d+)$", s)
    return f"{m.group(1)}{int(m.group(2)):02d}" if m else s


@pytest.fixture(scope="module")
def measured() -> dict[str, dict[str, float]]:
    """Both backends over the same trees, through the gate production applies."""
    from pipeline import wood_leaf_separation
    from pipeline.qsm import MIN_DBH_FIT_QUALITY, measure_dbh, measure_height
    from pipeline.realdata_eval import load_point_cloud
    from pipeline.single_tree import estimate_ground_datum

    truth = {}
    with CSV_PATH.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            try:
                dbh, height = float(row["DBH"]), float(row["TH_felled"])
            except (ValueError, TypeError, KeyError):
                continue
            if dbh > 0 and height > 0:
                truth[_key(row["tree_name"])] = (dbh, height)

    paths = [p for p in sorted(CLOUDS.glob("*.txt")) if _key(p.stem) in truth][::STEP]
    if not paths:
        pytest.skip("no cohort trees matched the destructive measurements")

    candidate = wood_leaf_separation.WoodLeafSegmenter(
        model_path=str(CHECKPOINT), backend="pointnet"
    )
    candidate.load()
    backends = {
        "tlsep": wood_leaf_separation.WoodLeafSegmenter(backend="tlsep"),
        "pointnet": candidate,
    }

    collected: dict[str, list[dict[str, float]]] = {name: [] for name in backends}
    for path in paths:
        points = np.asarray(load_point_cloud(path), dtype=float)
        if len(points) > MAX_POINTS:
            points = points[
                np.random.default_rng(0).choice(len(points), MAX_POINTS, replace=False)
            ]
        points[:, 2] -= estimate_ground_datum(points[:, 2])
        dbh_true, height_true = truth[_key(path.stem)]

        for name, segmenter in backends.items():
            labels = segmenter.segment(points.copy())
            wood = points[labels == wood_leaf_separation.WOOD]
            if len(wood) < 100:
                continue
            dbh, quality = measure_dbh(wood)
            if quality < MIN_DBH_FIT_QUALITY:
                continue
            collected[name].append(
                {
                    "dbh_error": dbh - dbh_true,
                    "height_error": measure_height(wood) - height_true,
                }
            )

    return {
        name: {
            "reported": float(len(rows)),
            "dbh_mae": float(np.mean([abs(r["dbh_error"]) for r in rows])),
            "height_mae": float(np.mean([abs(r["height_error"]) for r in rows])),
        }
        for name, rows in collected.items()
        if rows
    }


@needs_everything
class TestTheCandidateFailsTheGateItWasBuiltFor:
    def test_dbh_is_unchanged_rather_than_improved(self, measured):
        """The headline measurement. Chave takes DBH, height and density, so a
        wood/leaf backend earns promotion by improving one of those.

        Stated as equivalence, not as an inequality. The two land at 0.73 cm and
        0.75 cm, and a one-sided assertion with a tolerance wide enough to cover
        that gap passes whichever way the values fall — which the first version
        of this test did, and a mutation swapping the two backends did not
        disturb it. What is true and worth pinning is that swapping the backend
        does not move DBH.
        """
        baseline, candidate = measured["tlsep"], measured["pointnet"]
        difference = candidate["dbh_mae"] - baseline["dbh_mae"]

        assert abs(difference) < 0.15, (
            f"DBH MAE now differs by {difference:+.2f} cm "
            f"(tlsep {baseline['dbh_mae']:.2f}, PointNet++ {candidate['dbh_mae']:.2f}) "
            "— the backends are no longer equivalent here, re-measure before "
            "quoting either"
        )

    def test_height_regresses(self, measured):
        """The policy asks for non-regressing DBH/height/volume. Height is where
        this candidate loses: it calls far less of the cloud wood (about 42%
        against tlsep's 80%), and max-Z over a thinner wood set sits lower."""
        baseline, candidate = measured["tlsep"], measured["pointnet"]

        assert candidate["height_mae"] > baseline["height_mae"], (
            f"height no longer regresses ({candidate['height_mae']:.2f} m vs "
            f"{baseline['height_mae']:.2f} m) — re-open the promotion question"
        )

    def test_it_reports_no_more_trees_than_the_baseline(self, measured):
        """The policy's fifth criterion. A backend that measures marginally
        better on fewer trees has not improved the product."""
        baseline, candidate = measured["tlsep"], measured["pointnet"]

        assert candidate["reported"] <= baseline["reported"], (
            f"PointNet++ now reports more trees ({candidate['reported']:.0f} vs "
            f"{baseline['reported']:.0f}) — re-open the promotion question"
        )


@needs_everything
def test_wood_iou_is_a_proxy_and_disagrees_with_the_product(measured):
    """The finding worth keeping.

    PointNet++ wins Wood IoU by 67% relative and leaf IoU by nearly 3x, and
    measures DBH no better and height worse. A metric that improves while the
    measurement it stands in for does not is not evidence for promotion, and
    every case made for this candidate so far has been made on that metric.

    The assertion is on height, because that is where the disagreement is
    directional and large: 0.42 m against 0.59 m is a 40% regression on the
    backend that wins every IoU comparison.
    """
    baseline, candidate = measured["tlsep"], measured["pointnet"]
    regression = candidate["height_mae"] / baseline["height_mae"] - 1.0

    assert regression > 0.15, (
        f"the IoU winner now measures height within {regression:+.0%} of the "
        "baseline — the proxy and the product may have started agreeing, which "
        "would change the promotion answer"
    )
