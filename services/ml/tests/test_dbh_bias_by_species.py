"""The DBH under-read is bark, and these tests say so in a way that can fail.

TreeQ reads stems 0.80 cm small on average over the 65 Demol trees. That is
systematic -- 50 of 65 read low -- and carbon goes as roughly the square of
diameter, so it is the most consequential known error in the product.

`docs/ml/DBH_BIAS_AND_BARK.md` establishes what it is: not point density (ten
times the points does not move it), not tree size (within a species the
correlation has no consistent sign), but bark. Sorted by error the four species
come out in exactly the order of how deeply fissured they are, and the cohort
authors' own published QSM shows the same ordering slightly larger.

Two things are pinned here.

The species structure reads the committed artefact, so it runs on CI. That is
unusual for a ground-truth check in this repository -- every other one skips for
want of the 691 MB cohort -- and it works because
`docs/evidence/demol_65/result.json` carries the per-tree predictions beside the
per-tree truth.

The reference-QSM control reads `qsm_DBHqsm` out of the cohort CSV and skips
where the cohort is absent. It is the assertion that matters most, because it is
what separates "TLS disagrees with a tape on rough bark" from "this repository
has a bug in its circle fit".

Every assertion is written to fail if the effect goes away. If it does, the
finding changed and the document has to change with it.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np
import pytest

ML_ROOT = Path(__file__).resolve().parent.parent
ARTEFACT = ML_ROOT.parent.parent / "docs" / "evidence" / "demol_65" / "result.json"
COHORT_CSV = (
    ML_ROOT / "data" / "raw" / "zenodo_belgium" / "Destructive_and_qsm_data_DEMOL.csv"
)

#: Tree-id prefix to species, and the bark each one has. The order of this
#: mapping is the claim: roughest bark first.
SPECIES = {
    "PSYL": ("Pinus sylvestris", "thick, deeply fissured, plated"),
    "LXDC": ("Larix decidua", "thick, scaly, fissured"),
    "FEXC": ("Fraxinus excelsior", "moderately fissured"),
    "FSYL": ("Fagus sylvatica", "thin, smooth, unfissured"),
}


def _species(tree_id: str) -> str:
    """`PSYLA-07` and `PSYLB-07` are both Scots pine, from two sites."""
    match = re.match(r"^([A-Z]+?)[AB]?-\d+$", tree_id)
    return (match.group(1) if match else tree_id)[:4]


@pytest.fixture(scope="module")
def per_tree() -> list[dict[str, float]]:
    return json.loads(ARTEFACT.read_text(encoding="utf-8"))["per_tree"]


@pytest.fixture(scope="module")
def relative_bias(per_tree) -> dict[str, float]:
    """Mean signed relative DBH error, per species, as a percentage."""
    grouped: dict[str, list[float]] = {}
    for row in per_tree:
        error = (row["pred_dbh_cm"] - row["gt_dbh_cm"]) / row["gt_dbh_cm"] * 100.0
        grouped.setdefault(_species(row["tree_id"]), []).append(error)
    return {name: float(np.mean(values)) for name, values in grouped.items()}


class TestTheUnderReadIsStructuredBySpecies:
    def test_the_cohort_holds_the_four_species_the_finding_is_about(self, relative_bias):
        assert set(relative_bias) == set(SPECIES), (
            f"the artefact now covers {sorted(relative_bias)}, and the bark "
            f"finding was measured on {sorted(SPECIES)} -- re-read "
            "docs/ml/DBH_BIAS_AND_BARK.md before trusting either"
        )

    def test_every_species_reads_low(self, relative_bias):
        """The direction is one-sided. An uncertainty band drawn symmetrically
        about the estimate is describing a different pipeline."""
        reading_high = {n: b for n, b in relative_bias.items() if b >= 0}

        assert not reading_high, (
            f"{reading_high} now read high. The under-read was the finding; if "
            "a species has crossed over, the bark explanation needs re-testing"
        )

    def test_the_ordering_follows_bark_roughness(self, relative_bias):
        """The whole argument. Sorted by error, the species come out in the
        order of how fissured their bark is -- pine, larch, ash, beech."""
        measured = sorted(relative_bias, key=lambda name: relative_bias[name])

        assert measured == list(SPECIES), (
            f"species now rank {measured}, and the bark hypothesis predicts "
            f"{list(SPECIES)}. One of the two is wrong now"
        )

    def test_smooth_bark_is_several_times_better_than_rough(self, relative_bias):
        """Beech against pine. 0.67% against 4.06% when this was written -- the
        gap is the effect, and a threshold well inside it catches the effect
        weakening without failing on ordinary movement."""
        ratio = relative_bias["PSYL"] / relative_bias["FSYL"]

        assert ratio > 3.0, (
            f"pine is now only {ratio:.1f}x worse than beech (was 6.1x). Either "
            "the fit improved on rough bark or the cohort changed"
        )

    def test_the_headline_figure_describes_a_mixture_not_a_tree(self, per_tree):
        """0.898 cm is the number the proposal quotes. It is 1.32 cm for pine
        and 0.25 cm for beech, and no tree in the cohort is the average."""
        error = {}
        for row in per_tree:
            error.setdefault(_species(row["tree_id"]), []).append(
                abs(row["pred_dbh_cm"] - row["gt_dbh_cm"])
            )
        cohort = float(np.mean([abs(r["pred_dbh_cm"] - r["gt_dbh_cm"]) for r in per_tree]))
        worst = max(float(np.mean(v)) for v in error.values())
        best = min(float(np.mean(v)) for v in error.values())

        assert best < cohort < worst and worst > 3 * best, (
            f"per-species MAE now spans {best:.3f}-{worst:.3f} cm around a "
            f"cohort figure of {cohort:.3f}. The claim that the headline hides "
            "a species spread is what this checks"
        )


@pytest.mark.skipif(
    not COHORT_CSV.is_file(), reason="Demol cohort not present (691 MB, not in git)"
)
class TestAnIndependentImplementationReadsLowToo:
    """The control. `qsm_DBHqsm` is the cohort authors' own QSM DBH for these
    trees, run by other people against the same tape. If the under-read were
    this repository's circle fit, that column would not show it."""

    @staticmethod
    def _reference() -> dict[str, float]:
        """Their QSM DBH in centimetres, keyed by tree id."""
        reference = {}
        with COHORT_CSV.open(encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                try:
                    # Theirs is metres where the taped column is centimetres.
                    qsm = float(row["qsm_DBHqsm"]) * 100.0
                except (ValueError, TypeError, KeyError):
                    continue
                if qsm > 0:
                    reference[row["tree_name"].strip()] = qsm
        return reference

    def test_it_reads_low_on_every_species_as_well(self, per_tree):
        """A statement about their data, not about this pipeline.

        Nothing this repository changes can make it fail -- mutating our own
        predictions leaves it green, which was checked. It fires if the CSV is
        replaced, if `qsm_DBHqsm` stops being metres, or if the tree ids stop
        lining up, and it is here because the bark argument rests on this column
        saying what the document claims it says.
        """
        reference = self._reference()
        grouped: dict[str, list[float]] = {}
        for row in per_tree:
            error = (reference[row["tree_id"]] - row["gt_dbh_cm"]) / row["gt_dbh_cm"] * 100.0
            grouped.setdefault(_species(row["tree_id"]), []).append(error)
        high = {n: float(np.mean(v)) for n, v in grouped.items() if np.mean(v) >= 0}

        assert not high, (
            f"the reference QSM now reads high on {high} -- the control for the "
            "bark explanation has stopped agreeing with it"
        )

    def test_the_two_implementations_fail_on_the_same_trees(self, per_tree):
        """+0.78 when this was written. Independent code, same clouds, same
        tape: agreement this strong is a property of the data, not of either
        implementation."""
        reference = self._reference()
        ours = np.array(
            [(r["pred_dbh_cm"] - r["gt_dbh_cm"]) / r["gt_dbh_cm"] * 100.0 for r in per_tree]
        )
        theirs = np.array(
            [(reference[r["tree_id"]] - r["gt_dbh_cm"]) / r["gt_dbh_cm"] * 100.0 for r in per_tree]
        )
        correlation = float(np.corrcoef(ours, theirs)[0, 1])

        assert correlation > 0.5, (
            f"per-tree errors now correlate at {correlation:+.3f}. Below this "
            "the two implementations are failing on different trees, which "
            "would point back at the algorithm rather than the bark"
        )

    def test_this_pipeline_is_no_worse_than_the_published_reference(self, per_tree):
        """0.898 cm against 1.095 cm, closer on 42 of 65 trees.

        Not a matched experiment -- their figure comes from their own processing
        at settings this repository cannot reproduce. It is the number a reader
        would otherwise take as what this data supports, so being behind it
        would need saying out loud."""
        reference = self._reference()
        ours = float(np.mean([abs(r["pred_dbh_cm"] - r["gt_dbh_cm"]) for r in per_tree]))
        theirs = float(
            np.mean([abs(reference[r["tree_id"]] - r["gt_dbh_cm"]) for r in per_tree])
        )

        assert ours <= theirs, (
            f"TreeQ DBH MAE {ours:.3f} cm is now worse than the reference "
            f"{theirs:.3f} cm -- docs/ml/DBH_BIAS_AND_BARK.md claims otherwise"
        )


class TestTheCaveatReachesTheCaller:
    """A finding that stops at a markdown file has not reached anyone.

    Every carbon figure this pipeline produces rests on a diameter that reads
    low, one-sidedly, by an amount nobody has measured for a tropical species.
    `uncertainty_basis` is the field a caller reads to find out what the number
    is worth, so the caveat has to be in it on every route through
    `calculate_carbon` -- including the species-specific branch, which no
    shipped row can currently reach and which would silently lose the note.
    """

    def test_a_known_species_is_told(self):
        from pipeline.allometric import DBH_BIAS_NOTE, calculate_carbon

        result = calculate_carbon(dbh_cm=30, height_m=20, species_sci="Tectona grandis")

        assert DBH_BIAS_NOTE in result.uncertainty_basis

    def test_an_unknown_species_is_told(self):
        from pipeline.allometric import DBH_BIAS_NOTE, calculate_carbon

        result = calculate_carbon(dbh_cm=30, height_m=20, species_sci=None)

        assert DBH_BIAS_NOTE in result.uncertainty_basis

    def test_the_species_equation_route_is_told_too(self, monkeypatch):
        """Unreachable today -- every row is coefficients_verified=no, so this
        branch never runs and a note dropped from it would fail nothing. Forced
        into the state it exists for, the way test_equation_plausibility does."""
        from dataclasses import replace

        from pipeline import allometric
        from pipeline.allometric import DBH_BIAS_NOTE, calculate_carbon, load_species_db

        db = dict(load_species_db())
        db["Tectona grandis"] = replace(db["Tectona grandis"], coefficients_verified=True)
        monkeypatch.setattr(allometric, "load_species_db", lambda *a, **k: db)

        result = calculate_carbon(dbh_cm=30, height_m=20, species_sci="Tectona grandis")

        assert result.method == "species_specific", (
            "the species-specific branch was not reached, so this asserts nothing"
        )
        assert DBH_BIAS_NOTE in result.uncertainty_basis

    def test_the_note_says_which_direction(self):
        """A caveat that says 'uncertain' where the truth is 'always low' lets a
        reader draw a symmetric band around a one-sided error."""
        from pipeline.allometric import DBH_BIAS_NOTE

        assert "ต่ำกว่า" in DBH_BIAS_NOTE and "เสมอ" in DBH_BIAS_NOTE
