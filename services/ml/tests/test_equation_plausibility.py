"""An allometric equation may not predict a mass the tree cannot have.

`coefficients_verified` records that a human read the cited paper. It is a
promise, and species_db.csv is data — it ships inside the Docker image and an
operator can flip a row to `yes` without touching code, so that promise never
passes through CI. This is the check that runs regardless.

The bound is physical, not statistical. A tree cannot weigh more than its own
volume times the density of its wood:

    ceiling = (π/4) · D² · H · TOTAL_TREE_FORM_FACTOR · ρ

with the form factor measured on the 65 destructively harvested Demol trees.
Above-ground biomass should sit at or below that, since the volume covers the
whole above-ground tree and AGB excludes roots.

Four of the five rows in species_db exceed it by 2.3x to 3.3x.
"""

from __future__ import annotations

import math

import pytest

from pipeline.allometric import (
    MAX_AGB_OVER_PHYSICAL_CEILING,
    SpeciesParams,
    calculate_agb_chave_pantropical,
    calculate_agb_species_specific,
    calculate_carbon,
    load_species_db,
    physical_mass_ceiling_kg,
    species_equation_is_physically_possible,
)
from pipeline.qsm import TOTAL_TREE_FORM_FACTOR

SIZES = ((30.0, 20.0), (50.0, 32.0), (80.0, 50.0))


class TestTheCeilingItself:
    def test_it_is_volume_times_density(self):
        ceiling = physical_mass_ceiling_kg(30.0, 20.0, 700.0)
        expected = math.pi / 4 * 0.3**2 * 20.0 * TOTAL_TREE_FORM_FACTOR * 700.0

        assert ceiling == pytest.approx(expected)

    def test_a_degenerate_tree_has_no_ceiling_rather_than_a_negative_one(self):
        assert physical_mass_ceiling_kg(0.0, 20.0, 700.0) == 0.0
        assert physical_mass_ceiling_kg(30.0, -1.0, 700.0) == 0.0

    def test_chave_sits_under_the_allowance(self):
        """The bound has to admit the model actually in use, or it is measuring
        the bound's own slack rather than the equation."""
        for name, species in load_species_db().items():
            for dbh_cm, height_m in SIZES:
                ceiling = physical_mass_ceiling_kg(dbh_cm, height_m, species.wood_density)
                chave = calculate_agb_chave_pantropical(dbh_cm, height_m, species.wood_density)
                assert chave < ceiling * MAX_AGB_OVER_PHYSICAL_CEILING, (
                    f"{name} at DBH {dbh_cm}: Chave itself would be refused"
                )


class TestWhatTheRowsActuallyDo:
    def test_only_teak_predicts_a_possible_mass(self):
        """If this changes, the rows changed — check which way before trusting it.

        Teak also tracks Chave to within 8% across the diameter range, so it is
        not merely under the ceiling, it agrees with the reference model.
        """
        possible = {
            name
            for name, species in load_species_db().items()
            if species_equation_is_physically_possible(species)
        }

        assert possible == {"Tectona grandis"}

    def test_the_four_exceed_the_ceiling_by_more_than_twice(self):
        """Recorded as a number so a later 'it is only a bit high' is checkable."""
        worst = {}
        for name, species in load_species_db().items():
            if name == "Tectona grandis":
                continue
            ratios = [
                calculate_agb_species_specific(dbh, h, species)
                / physical_mass_ceiling_kg(dbh, h, species.wood_density)
                for dbh, h in SIZES
            ]
            worst[name] = min(ratios)

        assert min(worst.values()) > 2.0, worst

    def test_it_is_not_a_unit_error(self):
        """The diagnosis this file replaced. Grams for kilograms is a factor of
        1000; nothing here is within two orders of magnitude of that."""
        for name, species in load_species_db().items():
            if species.agb_a is None:
                continue
            ratio = calculate_agb_species_specific(50.0, 32.0, species) / (
                physical_mass_ceiling_kg(50.0, 32.0, species.wood_density)
            )
            assert ratio < 10.0, f"{name} at {ratio:.1f}x could be a unit error after all"


class TestTheGuardIsLoadBearing:
    @staticmethod
    def _row(a: float, *, verified: bool = True) -> SpeciesParams:
        return SpeciesParams(
            name_sci="Test species",
            name_th="ทดสอบ",
            name_en="Test",
            wood_density=700.0,
            agb_a=a,
            agb_b=2.42,
            agb_c=0.66,
            agb_source="synthetic",
            coefficients_verified=verified,
        )

    def test_a_plausible_equation_passes(self):
        # Scaled to land near Chave rather than above the ceiling.
        assert species_equation_is_physically_possible(self._row(0.020))

    def test_an_impossible_equation_is_refused_even_when_flagged_verified(self):
        """The case species_db is in today, and the one an operator can create
        by editing a CSV inside the image."""
        row = self._row(0.0612)

        assert row.coefficients_verified is True
        assert not species_equation_is_physically_possible(row)

    def test_a_row_missing_coefficients_is_not_treated_as_possible(self):
        row = SpeciesParams(
            name_sci="No equation", name_th="-", name_en="-", wood_density=700.0
        )

        assert not species_equation_is_physically_possible(row)

    def test_a_small_tree_check_alone_would_miss_a_diverging_equation(self):
        """Why three sizes and not one.

        None of the four rows in species_db needs this — each is already over
        the ceiling at DBH 10 cm, so a small-tree check would catch them too.
        The case it protects against is an equation whose exponent is wrong
        rather than its coefficient: harmless on saplings, badly wrong on the
        large trees that hold most of the carbon. That equation is built here
        rather than assumed, because the rows present do not demonstrate it.
        """
        # b = 3.0 against Chave's effective 1.952 in D. Tuned so the ceiling
        # ratios run 0.37 / 0.81 / 1.14 / 1.57 at DBH 10 / 30 / 50 / 80 — under
        # the allowance everywhere except the largest tree.
        diverging = SpeciesParams(
            name_sci="Diverging",
            name_th="-",
            name_en="-",
            wood_density=700.0,
            agb_a=0.0024,
            agb_b=3.0,
            agb_c=0.66,
            agb_source="synthetic",
            coefficients_verified=True,
        )

        for small in ((10.0, 8.0), (30.0, 20.0), (50.0, 32.0)):
            assert species_equation_is_physically_possible(diverging, sizes=(small,)), (
                f"the synthetic equation was meant to look fine at DBH {small[0]}"
            )
        assert not species_equation_is_physically_possible(diverging), (
            "the default sizes must reach far enough out to catch it"
        )


class TestNothingUsesThemToday:
    def test_every_species_is_still_costed_with_chave(self):
        """Both gates are closed, so this is belt and braces — but it is the
        property a caller depends on, so it is asserted directly."""
        for name in load_species_db():
            result = calculate_carbon(dbh_cm=30, height_m=20, species_sci=name)
            assert result.method == "chave_pantropical", name


class TestTheRuntimeGuardIsReachable:
    """The check inside calculate_carbon, exercised rather than assumed.

    Every row has coefficients_verified=no, so `usable_species_equation` is
    already false before the physical check is consulted — deleting that check
    from the decision changed no test result. A guard nothing can reach is not
    a guard, so these force the state it exists for: a row somebody flipped to
    `yes` on an equation that cannot be right.
    """

    @staticmethod
    def _flip_to_verified(monkeypatch, name: str, **overrides: object) -> None:
        from dataclasses import replace

        from pipeline import allometric

        db = dict(load_species_db())
        db[name] = replace(db[name], coefficients_verified=True, **overrides)
        monkeypatch.setattr(allometric, "load_species_db", lambda *a, **k: db)

    def test_a_verified_but_impossible_row_is_still_costed_with_chave(self, monkeypatch):
        self._flip_to_verified(monkeypatch, "Afzelia xylocarpa")

        result = calculate_carbon(dbh_cm=50, height_m=32, species_sci="Afzelia xylocarpa")

        assert result.method == "chave_pantropical", (
            "an equation predicting more mass than the tree can hold was used "
            "because a CSV cell said someone had checked it"
        )

    def test_a_verified_and_possible_row_is_used(self, monkeypatch):
        """The other direction. Without this the guard could be refusing
        everything and the test above would still pass."""
        self._flip_to_verified(monkeypatch, "Tectona grandis")

        result = calculate_carbon(dbh_cm=50, height_m=32, species_sci="Tectona grandis")

        assert result.method == "species_specific"

    def test_the_refusal_survives_an_explicit_request_for_the_equation(self, monkeypatch):
        """prefer_method='species_specific' asks for it by name. Physics still
        wins: the caller can choose between defensible methods, not opt into an
        impossible one."""
        self._flip_to_verified(monkeypatch, "Bambusa spp.")

        result = calculate_carbon(
            dbh_cm=50,
            height_m=32,
            species_sci="Bambusa spp.",
            prefer_method="species_specific",
        )

        assert result.method == "chave_pantropical"
