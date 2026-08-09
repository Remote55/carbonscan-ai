"""Two models of the same tree, and what their disagreement is worth.

calculate_carbon can cost a tree through Chave 2014 or through its taper volume
times wood density. It is tempting to call the second one mechanistic — volume
times density is what mass is — and this file exists partly to keep that claim
from creeping back in. The volume comes from (π/4)·D²·H·form_factor, so both
models are one-parameter functions of ρ·D²·H and neither is a measurement.

What the second model buys is not a better number. It is an honest interval: two
defensible models landing 15% apart is information a single figure hides.
"""

from __future__ import annotations

import csv
import math
import statistics as st
from pathlib import Path

import pytest

from pipeline.allometric import (
    calculate_agb_chave_pantropical,
    calculate_carbon,
)
from pipeline.qsm import TOTAL_TREE_FORM_FACTOR, estimate_volume_taper

CSV = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "zenodo_belgium"
    / "Destructive_and_qsm_data_DEMOL.csv"
)
needs_cohort = pytest.mark.skipif(not CSV.exists(), reason="Demol cohort not present")


def _taper_volume(dbh_cm: float, height_m: float) -> float:
    return estimate_volume_taper(dbh_cm, height_m, form_factor=TOTAL_TREE_FORM_FACTOR)


class TestNeitherIsAMeasurement:
    """The reason the volume route is not promoted to primary."""

    def test_the_taper_route_is_a_closed_form_in_rho_d2_h(self):
        coefficient = TOTAL_TREE_FORM_FACTOR * math.pi / 4
        for dbh, height, rho in [(10, 8, 400), (30, 20, 600), (55, 34, 850), (80, 45, 500)]:
            through_volume = _taper_volume(dbh, height) * rho
            closed_form = rho * (dbh / 100) ** 2 * height * coefficient
            assert through_volume == pytest.approx(closed_form, rel=1e-12)

    @pytest.mark.parametrize(
        "model",
        [
            lambda d, h, rho: calculate_agb_chave_pantropical(d, h, rho),
            lambda d, h, rho: _taper_volume(d, h) * rho,
        ],
        ids=["chave", "taper"],
    )
    def test_both_models_see_only_the_product_rho_d2_h(self, model):
        """Two different trees with the same ρ·D²·H get the same answer from
        each model. A model that used shape, or the ratio of height to
        diameter, could not do this — which is what makes calling either one
        mechanistic wrong."""
        first = model(30.0, 20.0, 600.0)
        # Halve the height, double D² — same product, different tree.
        second = model(30.0 * math.sqrt(2), 10.0, 600.0)
        assert first == pytest.approx(second, rel=1e-12)


class TestTheSecondEstimate:
    def test_absent_unless_a_volume_is_supplied(self):
        without = calculate_carbon(dbh_cm=30, height_m=20)
        assert without.co2eq_volume_route_kg is None
        assert without.method_disagreement is None

    def test_present_when_one_is(self):
        result = calculate_carbon(dbh_cm=30, height_m=20, volume_m3=_taper_volume(30, 20))
        assert result.co2eq_volume_route_kg is not None
        assert result.method_disagreement is not None
        assert result.co2eq_kg > 0

    def test_a_nonsense_volume_is_ignored_rather_than_reported(self):
        for bad in (0.0, -1.0):
            result = calculate_carbon(dbh_cm=30, height_m=20, volume_m3=bad)
            assert result.co2eq_volume_route_kg is None

    def test_the_basis_names_both_numbers(self):
        result = calculate_carbon(dbh_cm=30, height_m=20, volume_m3=_taper_volume(30, 20))
        assert "ปริมาตร" in result.uncertainty_basis


class TestTheIntervalCoversBothModels:
    def test_the_other_estimate_is_never_outside_the_band(self):
        for dbh, height in [(12, 9), (30, 20), (55, 34), (80, 45)]:
            for species in (None, "Tectona grandis", "Afzelia xylocarpa"):
                result = calculate_carbon(
                    dbh_cm=dbh,
                    height_m=height,
                    species_sci=species,
                    volume_m3=_taper_volume(dbh, height),
                )
                assert result.co2eq_volume_route_kg is not None
                assert result.co2eq_low_kg <= result.co2eq_volume_route_kg
                assert result.co2eq_volume_route_kg <= result.co2eq_high_kg

    def test_naming_a_species_still_narrows_the_band_a_lot(self):
        unknown = calculate_carbon(dbh_cm=30, height_m=20, volume_m3=_taper_volume(30, 20))
        known = calculate_carbon(
            dbh_cm=30,
            height_m=20,
            species_sci="Tectona grandis",
            volume_m3=_taper_volume(30, 20),
        )

        def width(r):
            return (r.co2eq_high_kg - r.co2eq_low_kg) / r.co2eq_kg

        assert width(known) < width(unknown) / 2

    def test_but_not_as_far_as_density_alone_would_suggest(self):
        """Once density stops dominating, the model disagreement becomes
        visible. A band that ignored it would be narrower than what is known."""
        density_only = calculate_carbon(dbh_cm=30, height_m=20, species_sci="Tectona grandis")
        both = calculate_carbon(
            dbh_cm=30,
            height_m=20,
            species_sci="Tectona grandis",
            volume_m3=_taper_volume(30, 20),
        )
        assert both.co2eq_low_kg < density_only.co2eq_low_kg


@needs_cohort
class TestTheNumbersInTheComments:
    """The figures quoted in allometric.py, checked against the cohort so they
    cannot rot into folklore."""

    @pytest.fixture(scope="class")
    def cohort(self):
        trees = []
        with CSV.open(encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                try:
                    dbh, height = float(row["DBH"]), float(row["TH_felled"])
                    agb = float(row["Fresh_mass_total_tree_harvested"]) * float(
                        row["DMC_base_disc"]
                    )
                    rho = float(row["WSG_base_disc"]) * 1000.0
                except (ValueError, KeyError):
                    continue
                if min(dbh, height, agb, rho) > 0:
                    trees.append((dbh, height, agb, rho))
        return trees

    def test_the_two_models_disagree_by_about_fifteen_percent(self, cohort):
        gaps = [
            abs(_taper_volume(d, h) * rho - calculate_agb_chave_pantropical(d, h, rho))
            / calculate_agb_chave_pantropical(d, h, rho)
            for d, h, _agb, rho in cohort
        ]
        assert st.mean(gaps) == pytest.approx(0.149, abs=0.02)

    def test_chave_runs_high_and_the_taper_route_does_not(self, cohort):
        chave_bias = st.mean(
            (calculate_agb_chave_pantropical(d, h, rho) - agb) / agb for d, h, agb, rho in cohort
        )
        taper_bias = st.mean(
            (_taper_volume(d, h) * rho - agb) / agb for d, h, agb, rho in cohort
        )
        assert chave_bias > 0.15, f"documented as +18%, measured {chave_bias:+.1%}"
        assert abs(taper_bias) < 0.05, f"documented as near zero, measured {taper_bias:+.1%}"

    def test_chaves_bias_is_size_dependent_so_no_constant_repairs_it(self, cohort):
        """The finding that matters: it is the functional form, not a scale."""
        by_diameter = sorted(cohort, key=lambda t: t[0])
        quarter = len(by_diameter) // 4
        smallest = by_diameter[:quarter]
        largest = by_diameter[-quarter:]

        def bias(chunk):
            return st.mean(
                (calculate_agb_chave_pantropical(d, h, rho) - agb) / agb
                for d, h, agb, rho in chunk
            )

        assert bias(smallest) > bias(largest) + 0.05, (
            "the bias no longer varies with diameter; the comment in "
            "allometric.py about functional form needs revisiting"
        )
