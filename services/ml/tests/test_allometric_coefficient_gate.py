"""Unverified species coefficients must not be used silently.

Four of the five equations in species_db.csv return 1.4x to 3.5x what Chave 2014
returns for the same tree at the same wood density, and the ratio climbs with
diameter - x1.49 to x2.14 across 10-80 cm - so the exponent disagrees, not just
the scale. species_db lists b = 2.15 to 2.42 against Chave's effective 1.952.
Only Tectona grandis stays inside 10% of the reference.

Four out of five wrong in the same direction is not what independent published
equations look like; it is what a unit error or a transcription from a different
functional form looks like. Nobody has checked them against Tsutsumi 1983,
Ogawa 1965, Yiping 2010, Chiarucci 2014 or the TGO 2017 guideline, and until
somebody does, a carbon figure computed from them is a number we cannot defend.

So the gate: a species equation is used only when its coefficients are marked
verified. Otherwise the tree is costed with Chave 2014 and that species' own
wood density - a published, low-variance quantity we do have grounds for - and
the result says so.
"""

from __future__ import annotations

import numpy as np
import pytest

from pipeline.allometric import (
    calculate_agb_chave_pantropical,
    calculate_carbon,
    load_species_db,
)

# Every species currently in the database, none of which is verified yet.
SPECIES = sorted(load_species_db())


class TestTheGate:
    @pytest.mark.parametrize("name", SPECIES)
    def test_an_unverified_species_is_costed_with_chave(self, name: str) -> None:
        species = load_species_db()[name]
        if species.coefficients_verified:
            pytest.skip(f"{name} has been verified; the gate does not apply")

        result = calculate_carbon(30.0, 22.0, name)

        assert result.method == "chave_pantropical"

    @pytest.mark.parametrize("name", SPECIES)
    def test_it_still_uses_that_species_own_wood_density(self, name: str) -> None:
        """The equation is in doubt; the density is not. Falling back to the
        generic 600 would throw away the one parameter we have grounds for."""
        species = load_species_db()[name]

        result = calculate_carbon(30.0, 22.0, name)

        assert result.wood_density == species.wood_density

    @pytest.mark.parametrize("name", SPECIES)
    def test_the_result_says_the_equation_was_not_used(self, name: str) -> None:
        species = load_species_db()[name]
        if species.coefficients_verified:
            pytest.skip(f"{name} has been verified; the gate does not apply")

        result = calculate_carbon(30.0, 22.0, name)

        # A reader of the output must be able to tell that the species equation
        # was skipped, without knowing this gate exists.
        assert "ยังไม่ตรวจสอบ" in result.source or "unverified" in result.source.lower()
        assert species.agb_source in result.source, "the original citation is still owed"

    def test_an_unknown_species_is_not_silently_given_a_known_one(self) -> None:
        result = calculate_carbon(30.0, 22.0, "Quercus imaginaria")

        assert result.method == "chave_pantropical"
        assert result.species_sci == "Quercus imaginaria"


class TestNumbers:
    @pytest.mark.parametrize("name", SPECIES)
    def test_the_gated_figure_equals_chave_at_that_density(self, name: str) -> None:
        species = load_species_db()[name]
        if species.coefficients_verified:
            pytest.skip(f"{name} has been verified; the gate does not apply")

        result = calculate_carbon(30.0, 22.0, name)
        expected = calculate_agb_chave_pantropical(30.0, 22.0, species.wood_density)

        assert result.agb_kg == pytest.approx(expected, rel=1e-9)

    def test_the_divergence_this_gate_exists_for_is_real(self) -> None:
        """Guards the premise rather than the fix: if someone corrects the
        coefficients and they stop disagreeing with Chave, this test fails and
        whoever did the work is told to revisit the gate."""
        db = load_species_db()
        diverging = []
        for name, sp in db.items():
            ratios = []
            for dbh in (10.0, 30.0, 80.0):
                height = 1.3 + 25.0 * (1.0 - np.exp(-0.06 * dbh))
                own = sp.agb_a * (dbh**sp.agb_b) * (height**sp.agb_c)
                ratios.append(own / calculate_agb_chave_pantropical(dbh, height, sp.wood_density))
            if max(ratios) > 1.15:
                diverging.append(name)

        assert len(diverging) == 4, f"expected four diverging species, got {diverging}"
        assert "Tectona grandis" not in diverging


class TestVerifiedSpeciesStillWork:
    def test_a_verified_species_uses_its_own_equation(self) -> None:
        """The gate is a gate, not a wall. Marking a row verified must restore
        the species equation - otherwise doing the source-checking work would
        change nothing and nobody would do it."""
        db = load_species_db()
        name = "Tectona grandis"
        species = db[name]
        object.__setattr__(species, "coefficients_verified", True)
        try:
            result = calculate_carbon(30.0, 22.0, name)

            assert result.method == "species_specific"
            expected = species.agb_a * (30.0**species.agb_b) * (22.0**species.agb_c)
            assert result.agb_kg == pytest.approx(expected, rel=1e-9)
        finally:
            object.__setattr__(species, "coefficients_verified", False)
            load_species_db.cache_clear()
