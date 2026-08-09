"""The carbon interval, and what it is honest about.

The interval propagates wood density, which this pipeline never measures. These
tests check it does that correctly, and — more importantly — pin down what it
does NOT cover, measured against 65 trees that were weighed after felling. An
interval that quietly fails to contain the truth is worse than no interval,
so the gap is asserted here rather than left in a comment.
"""

from __future__ import annotations

import csv
import statistics as st
from pathlib import Path

import pytest

from pipeline.allometric import (
    CARBON_VALIDATION_NOTE,
    DEFAULT_WOOD_DENSITY_RANGE,
    WOOD_DENSITY_SPREAD_KNOWN_SPECIES,
    calculate_agb_chave_pantropical,
    calculate_carbon,
    calculate_carbon_from_volume,
)

CSV = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "zenodo_belgium"
    / "Destructive_and_qsm_data_DEMOL.csv"
)
needs_cohort = pytest.mark.skipif(not CSV.exists(), reason="Demol cohort not present")


@pytest.fixture(scope="module")
def weighed() -> list[tuple[str, float, float, float, float]]:
    """(site, dbh_cm, height_m, true_agb_kg, measured_density) per felled tree."""
    out = []
    with CSV.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                dbh, height = float(row["DBH"]), float(row["TH_felled"])
                agb = float(row["Fresh_mass_total_tree_harvested"]) * float(
                    row["DMC_base_disc"]
                )
                rho = float(row["WSG_base_disc"]) * 1000.0
            except (ValueError, KeyError):
                continue
            if min(dbh, height, agb, rho) > 0:
                out.append((row["site_name"], dbh, height, agb, rho))
    return out


class TestGroundTruthIsTrustworthy:
    """Two independent routes to dry mass. If they part company, the rest of
    this file is measuring nothing."""

    @needs_cohort
    def test_fresh_mass_route_agrees_with_volume_route(self):
        diffs = []
        with CSV.open(encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                try:
                    a = float(row["Fresh_mass_total_tree_harvested"]) * float(
                        row["DMC_base_disc"]
                    )
                    b = (
                        float(row["Volume_total_tree_harvested"])
                        / 1000.0
                        * float(row["WSG_base_disc"])
                        * 1000.0
                    )
                except (ValueError, KeyError):
                    continue
                diffs.append((b - a) / a)
        assert len(diffs) > 60
        assert abs(st.mean(diffs)) < 0.03, f"routes disagree by {100*st.mean(diffs):.1f}%"
        assert st.pstdev(diffs) < 0.05


class TestIntervalMechanics:
    def test_unknown_species_gets_the_wide_range(self):
        r = calculate_carbon(dbh_cm=30, height_m=20)
        lo, hi = DEFAULT_WOOD_DENSITY_RANGE
        assert r.co2eq_low_kg < r.co2eq_kg < r.co2eq_high_kg
        # Chave is rho^0.976, so the bounds track the density ratio closely.
        assert r.co2eq_high_kg / r.co2eq_low_kg == pytest.approx(
            (hi / lo) ** 0.976, rel=1e-6
        )

    def test_known_species_gets_a_narrower_one(self):
        unknown = calculate_carbon(dbh_cm=30, height_m=20)
        known = calculate_carbon(dbh_cm=30, height_m=20, species_sci="Tectona grandis")
        unknown_width = (unknown.co2eq_high_kg - unknown.co2eq_low_kg) / unknown.co2eq_kg
        known_width = (known.co2eq_high_kg - known.co2eq_low_kg) / known.co2eq_kg
        assert known_width < unknown_width / 2, (
            "naming the species must buy a tighter range than not naming it"
        )
        assert known_width == pytest.approx(
            2 * WOOD_DENSITY_SPREAD_KNOWN_SPECIES, abs=0.02
        )

    def test_the_point_estimate_sits_inside_its_own_bounds(self):
        for dbh, height in [(10, 8), (30, 20), (55, 34), (80, 45)]:
            for species in (None, "Tectona grandis", "Bambusa spp."):
                r = calculate_carbon(dbh_cm=dbh, height_m=height, species_sci=species)
                assert r.co2eq_low_kg <= r.co2eq_kg <= r.co2eq_high_kg

    def test_every_result_says_where_its_bounds_came_from(self):
        for species in (None, "Tectona grandis", "Unknown sp."):
            r = calculate_carbon(dbh_cm=25, height_m=18, species_sci=species)
            assert r.uncertainty_basis, "a bound with no stated basis is decoration"
            assert "kg/m³" in r.uncertainty_basis

    def test_unknown_species_result_admits_the_model_is_unvalidated(self):
        r = calculate_carbon(dbh_cm=25, height_m=18)
        assert CARBON_VALIDATION_NOTE in r.uncertainty_basis

    def test_volume_method_also_carries_bounds(self):
        r = calculate_carbon_from_volume(volume_m3=0.8, wood_density=650)
        assert r.co2eq_low_kg < r.co2eq_kg < r.co2eq_high_kg
        assert r.uncertainty_basis


class TestWhatTheIntervalDoesNotCover:
    """Measured, not assumed. These numbers are quoted in allometric.py; if the
    cohort or the model changes, these fail rather than letting the comment rot.
    """

    @needs_cohort
    def test_shipped_configuration_overestimates_this_cohort(self, weighed):
        biases = [
            (calculate_agb_chave_pantropical(d, h, 600.0) - agb) / agb
            for _, d, h, agb, _ in weighed
        ]
        assert st.mean(biases) > 0.30, (
            f"documented as about +41%, measured {100*st.mean(biases):+.1f}%"
        )

    @needs_cohort
    def test_knowing_the_density_removes_about_half_the_error(self, weighed):
        guessed = st.mean(
            abs(calculate_agb_chave_pantropical(d, h, 600.0) - agb) / agb
            for _, d, h, agb, _ in weighed
        )
        actual = st.mean(
            abs(calculate_agb_chave_pantropical(d, h, rho) - agb) / agb
            for _, d, h, agb, rho in weighed
        )
        assert actual < guessed * 0.6
        assert actual > 0.10, (
            "if the residual ever drops this far the comment in allometric.py "
            "about an 18% out-of-domain bias is stale"
        )

    @needs_cohort
    def test_the_density_range_does_not_cover_most_of_the_cohort(self, weighed):
        """The uncomfortable one, and the reason the basis string says so.

        A range around a centre that is 41% high cannot rescue it. This asserts
        the shortfall so nobody upgrades the wording to "confidence interval".
        """
        lo, hi = DEFAULT_WOOD_DENSITY_RANGE
        covered = sum(
            1
            for _, d, h, agb, _ in weighed
            if calculate_agb_chave_pantropical(d, h, lo)
            <= agb
            <= calculate_agb_chave_pantropical(d, h, hi)
        )
        assert covered < 0.8 * len(weighed), (
            f"coverage is now {covered}/{len(weighed)} — if the model was fixed, "
            "revisit CARBON_VALIDATION_NOTE and this test"
        )
