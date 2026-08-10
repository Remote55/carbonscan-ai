"""The constants in qsm.py, and the fit that feeds them.

Two kinds of test live here. Some check the code does what it says. Others
check the *premise* — that the numbers hardcoded in qsm.py still match what the
Demol cohort actually measures. If someone edits a constant without re-deriving
it, or swaps the cohort, the premise tests fail and say so, rather than letting
a stale number keep a comment that cites evidence for it.
"""

from __future__ import annotations

import csv
import math
import statistics as st
from pathlib import Path

import numpy as np
import pytest

from pipeline import qsm

CSV = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "zenodo_belgium"
    / "Destructive_and_qsm_data_DEMOL.csv"
)
needs_cohort = pytest.mark.skipif(not CSV.exists(), reason="Demol cohort not present")


@pytest.fixture(scope="module")
def cohort() -> list[tuple[float, float, float]]:
    """(cylinder_m3, stem_m3, total_m3) per felled tree. Volumes in the CSV are litres."""
    out = []
    with CSV.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                dbh, height = float(row["DBH"]), float(row["TH_felled"])
                stem = float(row["Volume_stem_harvested"]) / 1000.0
                total = float(row["Volume_total_tree_harvested"]) / 1000.0
            except (ValueError, KeyError):
                continue
            if min(dbh, height, stem, total) > 0:
                out.append((math.pi / 4 * (dbh / 100) ** 2 * height, stem, total))
    return out


class TestFormFactorPremise:
    """The constants claim to be measured. Check they still are."""

    @needs_cohort
    def test_stem_form_factor_matches_the_cohort(self, cohort):
        measured = st.mean(stem / cyl for cyl, stem, _ in cohort)
        assert qsm.STEM_FORM_FACTOR == pytest.approx(measured, abs=0.005), (
            f"STEM_FORM_FACTOR is {qsm.STEM_FORM_FACTOR} but the cohort now "
            f"measures {measured:.4f}"
        )

    @needs_cohort
    def test_total_form_factor_matches_the_cohort(self, cohort):
        measured = st.mean(total / cyl for cyl, _, total in cohort)
        assert qsm.TOTAL_TREE_FORM_FACTOR == pytest.approx(measured, abs=0.005)

    @needs_cohort
    def test_the_old_constant_was_wrong_in_both_directions(self, cohort):
        """0.50 overstated the stem and understated the tree. Both, at once."""
        stem_bias = st.mean((cyl * 0.50 - stem) / stem for cyl, stem, _ in cohort)
        total_bias = st.mean((cyl * 0.50 - total) / total for cyl, _, total in cohort)
        assert stem_bias > 0.20, "0.50 should overestimate stem volume"
        assert total_bias < -0.10, "0.50 should underestimate whole-tree volume"

    @needs_cohort
    def test_new_constants_beat_the_old_one_out_of_sample(self, cohort):
        """Refit on all but one tree, score that tree. Never fits what it grades."""
        held_new, held_old = [], []
        for i in range(len(cohort)):
            rest = cohort[:i] + cohort[i + 1 :]
            ff = st.mean(total / cyl for cyl, _, total in rest)
            cyl, _, total = cohort[i]
            held_new.append(abs(cyl * ff - total) / total)
            held_old.append(abs(cyl * 0.50 - total) / total)
        assert st.mean(held_new) < st.mean(held_old) * 0.85


class TestVolumeDecomposition:
    def test_crown_is_no_longer_reported_as_zero(self):
        stem = np.array([[0.05 * math.cos(t), 0.05 * math.sin(t), z]
                         for z in np.linspace(0, 8, 40)
                         for t in np.linspace(0, 2 * math.pi, 16, endpoint=False)])
        r = qsm.compute_qsm(stem)
        assert r.branches_volume_m3 > 0, "a tree with a crown must not report crown volume 0"

    def test_total_is_exactly_stem_plus_branches(self):
        stem = np.array([[0.08 * math.cos(t), 0.08 * math.sin(t), z]
                         for z in np.linspace(0, 12, 40)
                         for t in np.linspace(0, 2 * math.pi, 16, endpoint=False)])
        r = qsm.compute_qsm(stem)
        assert r.total_volume_m3 == pytest.approx(
            r.stem_volume_m3 + r.branches_volume_m3, rel=1e-9
        )

    def test_stem_factor_is_below_total_factor(self):
        assert qsm.STEM_FORM_FACTOR < qsm.TOTAL_TREE_FORM_FACTOR


def _ring(radius: float, n: int, *, arc: float = 2 * math.pi, noise: float = 0.0,
          seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, arc, n, endpoint=False)
    xy = np.column_stack([radius * np.cos(t), radius * np.sin(t)])
    return xy + rng.normal(0, noise, xy.shape) if noise else xy


class TestCircleFitStability:
    def test_a_clean_ring_is_stable_to_within_a_millimetre(self):
        xy = _ring(0.15, 300, noise=0.004)
        radii = [
            qsm._ransac_circle_fit(xy, rng=np.random.default_rng(s))[2] for s in range(10)
        ]
        assert max(radii) - min(radii) < 0.001, f"seed-dependent radius: {radii}"

    def test_recovers_a_known_radius(self):
        xy = _ring(0.22, 400, noise=0.003)
        _, _, r, _ = qsm._ransac_circle_fit(xy, rng=np.random.default_rng(1))
        assert r == pytest.approx(0.22, abs=0.01)

    def test_partial_arc_does_not_produce_a_giant_circle(self):
        """A scanner sees one side of a trunk. The algebraic fit alone blows up
        on that; the accept-only-if-better guard is what stops it."""
        xy = _ring(0.18, 200, arc=math.pi / 2, noise=0.002)
        _, _, r, _ = qsm._ransac_circle_fit(xy, rng=np.random.default_rng(3))
        assert r <= 0.6, "radius escaped the plausible-trunk cap"

    def test_refit_never_loses_inliers(self):
        for seed in range(6):
            xy = _ring(0.12, 250, noise=0.006, seed=seed)
            _, _, r, ratio = qsm._ransac_circle_fit(xy, rng=np.random.default_rng(seed))
            assert ratio > 0.5, f"seed {seed} produced a poor consensus ({ratio:.2f})"
            assert r > 0


class TestAlgebraicFit:
    def test_exact_on_a_clean_circle(self):
        got = qsm._algebraic_circle_fit(_ring(0.3, 64))
        assert got is not None
        cx, cy, r = got
        assert (cx, cy, r) == pytest.approx((0.0, 0.0, 0.3), abs=1e-6)

    def test_offset_centre(self):
        got = qsm._algebraic_circle_fit(_ring(0.1, 64) + np.array([5.0, -3.0]))
        assert got is not None
        assert got[:2] == pytest.approx((5.0, -3.0), abs=1e-6)

    def test_too_few_points_returns_none(self):
        assert qsm._algebraic_circle_fit(np.zeros((2, 2))) is None

    def test_collinear_points_answer_confidently_and_wrongly(self):
        """Documents why the refit is guarded rather than trusted.

        Kasa on a straight line is rank-deficient; lstsq still returns the
        minimum-norm solution, here a 30 cm radius that would pass the
        plausible-trunk cap unchallenged.
        """
        collinear = np.column_stack([np.linspace(0, 1, 20), np.zeros(20)])
        got = qsm._algebraic_circle_fit(collinear)
        assert got is not None and 0.01 < got[2] < 0.6

    def test_but_the_caller_reports_nothing_for_a_straight_line(self):
        collinear = np.column_stack([np.linspace(0, 1, 20), np.zeros(20)])
        _, _, r, ratio = qsm._ransac_circle_fit(collinear, rng=np.random.default_rng(0))
        assert r == 0.0 and ratio == 0.0, (
            "a line must not become a trunk — measure_dbh turns r=0 into QSM_INVALID"
        )


CLOUDS = CSV.parent / "pointclouds" / "pointclouds_clean"


def _real_stem(name: str) -> np.ndarray:
    from pipeline.realdata_eval import load_point_cloud

    pts = np.asarray(load_point_cloud(CLOUDS / name), dtype=float)
    pts[:, 2] -= pts[:, 2].min()
    return pts


class TestTheFailureThisGateExistsFor:
    """LXDC4 is the one tree in the cohort where the circle fit collapses.

    Its taped DBH is 23.6 cm. Most seeds recover about 23 cm; seed 2 returns
    116.4 cm — the fit latched onto something that is not the stem. This is not
    hypothetical and it is not new: the same seed produced the same failure
    before any of these changes. What is new is that the pipeline now refuses
    the number instead of averaging it into a cohort whose MAE is about 1 cm.
    """

    @pytest.mark.skipif(not (CLOUDS / "LXDC4.txt").exists(), reason="cohort clouds absent")
    def test_the_bad_fit_is_wrong_and_admits_it(self):
        pts = _real_stem("LXDC4.txt")
        dbh, quality = qsm.measure_dbh(pts, seed=2)
        assert dbh > 100, f"expected the known blow-up, got {dbh:.1f} cm"
        assert quality < qsm.MIN_DBH_FIT_QUALITY, (
            f"the gate misses its own motivating case: quality {quality:.3f}"
        )

    @pytest.mark.skipif(not (CLOUDS / "LXDC4.txt").exists(), reason="cohort clouds absent")
    def test_this_tree_is_now_refused_on_every_seed_and_that_is_the_price(self):
        """What raising the gate to 0.80 costs, recorded rather than glossed.

        This test used to assert the opposite — that seeds 0, 1, 3 and 4 were
        kept — under a 0.20 gate, on the principle that a gate should reject a
        failed fit and not a difficult tree. The principle is sound and the
        threshold could not deliver it: the same 0.20 that kept LXDC4 also kept
        thirteen measurements that were more than 5 cm wrong, one of them by
        64.67 cm, because a sparse slice is easy to fit and the inlier ratio
        goes UP as the measurement becomes meaningless.

        So LXDC4 is now refused on every seed, and these are accurate numbers
        being thrown away. That is the trade, and it is only defensible because
        the pipeline reports the refusal: the tree appears in
        PipelineDiagnostics.excluded_segments with reason QSM_LOW_FIT_QUALITY,
        not as a missing row.

        If a later change recovers this tree without letting the 64 cm failures
        back in, this test is the one to delete.
        """
        pts = _real_stem("LXDC4.txt")
        for seed in (0, 1, 3, 4):
            dbh, quality = qsm.measure_dbh(pts, seed=seed)
            assert 20 < dbh < 27, (
                f"seed {seed} gave {dbh:.1f} cm against a taped 23.6 — the point of "
                "this test is that an ACCURATE measurement is being refused"
            )
            assert quality < qsm.MIN_DBH_FIT_QUALITY, (
                f"seed {seed} now passes the gate at quality {quality:.3f}; if that "
                "is intended, the cost recorded here no longer applies"
            )

    @pytest.mark.skipif(not (CLOUDS / "FEXC16.txt").exists(), reason="cohort clouds absent")
    def test_a_healthy_stem_is_nowhere_near_the_gate(self):
        pts = _real_stem("FEXC16.txt")
        for seed in range(4):
            dbh, quality = qsm.measure_dbh(pts, seed=seed)
            assert quality > 0.9, f"seed {seed} quality {quality:.3f}"
            assert 22 < dbh < 24


class TestFitQualityGate:
    def test_threshold_sits_below_a_healthy_fit(self):
        """A clean stem must clear the gate with room to spare.

        Expressed as an absolute margin, not as a multiple of the gate: this
        assertion read ``ratio > MIN_DBH_FIT_QUALITY * 2``, which stops being
        satisfiable at all above 0.5 because an inlier ratio cannot exceed 1.0.
        A test that cannot fail for the right reason is not a check.
        """
        xy = _ring(0.15, 300, noise=0.004)
        _, _, _, ratio = qsm._ransac_circle_fit(xy, rng=np.random.default_rng(0))
        assert ratio > 0.95, f"a clean ring fitted at only {ratio:.3f}"
        assert qsm.MIN_DBH_FIT_QUALITY <= 0.90, (
            "the gate must leave headroom above it for real stems, which are "
            "noisier than this synthetic ring"
        )

    def test_noise_alone_does_not_reach_the_threshold(self):
        rng = np.random.default_rng(11)
        xy = rng.uniform(-0.3, 0.3, (300, 2))
        _, _, _, ratio = qsm._ransac_circle_fit(xy, rng=np.random.default_rng(0))
        assert ratio < 0.9, f"random points scored {ratio:.2f} as a circle"
