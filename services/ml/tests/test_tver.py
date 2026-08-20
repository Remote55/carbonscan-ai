"""Thailand's official allometric equations, checked against the table itself.

`pipeline/tver.py` transcribes T-VER-S-TOOL-01-01 v2 Appendix 2 Table 2. The
expected values below are transcribed a second time, independently, straight
from the published equations — `0.0509 * (30**2 * 20) ** 0.919` rather than
whatever the module returns. A test that asks the code what the code says would
have passed for `species_db.csv` too, which held a real published coefficient
attached to exponents that were not its own.
"""

from __future__ import annotations

import math

import pytest

from pipeline.tver import (
    FOREST_TYPES,
    OGAWA_RECIPROCAL_LEAF,
    aboveground_biomass,
    implausible_sizes,
    solid_cylinder_mass_kg,
)

#: A mid-sized tree. D²H = 18000.
DBH_CM, HEIGHT_M = 30.0, 20.0
D2H = DBH_CM**2 * HEIGHT_M


class TestTheEquationsAreWhatTheTableSays:
    def test_dry_evergreen_matches_tsutsumi(self):
        """WS = 0.0509 (D²H)^0.919, WB = 0.00893 (D²H)^0.977,
        WL = 0.0140 (D²H)^0.669."""
        result = aboveground_biomass("dry_evergreen", DBH_CM, HEIGHT_M)

        assert result.stem_kg == pytest.approx(0.0509 * D2H**0.919)
        assert result.branch_kg == pytest.approx(0.00893 * D2H**0.977)
        assert result.leaf_kg == pytest.approx(0.0140 * D2H**0.669)

    def test_mixed_deciduous_matches_ogawa(self):
        """WS = 0.0396 (D²H)^0.933, WB = 0.00349 (D²H)^1.030, and the leaf term
        is the reciprocal form rather than a power law."""
        result = aboveground_biomass("mixed_deciduous", DBH_CM, HEIGHT_M)
        stem = 0.0396 * D2H**0.933
        branch = 0.00349 * D2H**1.030

        assert result.stem_kg == pytest.approx(stem)
        assert result.branch_kg == pytest.approx(branch)
        assert result.leaf_kg == pytest.approx(1.0 / (28.0 / (stem + branch) + 0.025))

    def test_the_two_ogawa_rows_are_not_the_same_equation(self):
        """Both carry a stem coefficient of 0.0396 and they are different fits:
        rain forest is exponent 0.9326 with a branch term of 0.006003·^1.027,
        deciduous is 0.933 with 0.00349·^1.030.

        Reading one as the other is exactly how a published coefficient ends up
        in a row it does not belong to.
        """
        rain = aboveground_biomass("tropical_rain", DBH_CM, HEIGHT_M)
        deciduous = aboveground_biomass("mixed_deciduous", DBH_CM, HEIGHT_M)

        assert rain.stem_kg != pytest.approx(deciduous.stem_kg)
        assert rain.branch_kg > deciduous.branch_kg * 1.5

    def test_every_row_carries_its_citation(self):
        for key, forest in FOREST_TYPES.items():
            assert forest.key == key
            assert "T-VER-S-TOOL-01-01 v2" in forest.source, key
            assert forest.name_th and forest.name_en, key

    def test_components_sum_to_the_total(self):
        """WT = WS + WB + WL. The stem alone is not the tree, which is the
        mistake docs/ml/ALLOMETRIC_COEFFICIENTS.md exists for."""
        for key in FOREST_TYPES:
            result = aboveground_biomass(key, DBH_CM, HEIGHT_M)

            assert result.total_kg == pytest.approx(
                result.stem_kg + result.branch_kg + result.leaf_kg
            ), key
            assert result.stem_kg < result.total_kg, key


class TestTheOgawaLeafTermBehavesLikeACrown:
    def test_it_saturates_instead_of_growing_without_bound(self):
        """1/(28/(WS+WB) + 0.025) approaches 40 kg however large the tree gets.
        A power law would not: leaf mass would pass the stem eventually."""
        huge = aboveground_biomass("mixed_deciduous", 200.0, 60.0)

        assert huge.leaf_kg < 40.0
        assert huge.leaf_kg > 35.0

    def test_it_still_rises_with_size(self):
        small = aboveground_biomass("mixed_deciduous", 10.0, 8.0)
        large = aboveground_biomass("mixed_deciduous", 50.0, 28.0)

        assert small.leaf_kg < large.leaf_kg

    def test_both_ogawa_rows_use_it(self):
        for key in ("tropical_rain", "mixed_deciduous"):
            assert FOREST_TYPES[key].leaf == OGAWA_RECIPROCAL_LEAF, key


class TestItRefusesWhatItCannotAnswer:
    def test_an_unknown_forest_type_raises(self):
        with pytest.raises(KeyError, match="unknown forest type"):
            aboveground_biomass("rainforest", DBH_CM, HEIGHT_M)

    @pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf")])
    def test_a_dimension_that_is_not_a_measurement_raises(self, bad):
        with pytest.raises(ValueError):
            aboveground_biomass("dry_evergreen", bad, HEIGHT_M)
        with pytest.raises(ValueError):
            aboveground_biomass("dry_evergreen", DBH_CM, bad)

    def test_biomass_rises_with_both_dimensions(self):
        base = aboveground_biomass("dry_evergreen", DBH_CM, HEIGHT_M).total_kg

        assert aboveground_biomass("dry_evergreen", DBH_CM + 10, HEIGHT_M).total_kg > base
        assert aboveground_biomass("dry_evergreen", DBH_CM, HEIGHT_M + 5).total_kg > base


class TestOneRowOfTheNationalMethodologyIsImpossible:
    """A finding about the source document, not about this code.

    `ป่าสนเขา (สนสองใบ)` carries WS = 0.2141 (D²H)^0.9814, where the
    three-needle row beside it carries 0.02698 — an order of magnitude apart. On
    a 30 cm, 20 m tree it predicts 3258 kg of above-ground biomass.

    A solid cylinder of that size machined from wood denser than lignum vitae
    weighs 1414 kg. The equation is not off by a form factor or a density
    assumption; it exceeds the mass of solid wood by more than double, at every
    size tested.

    tver.py reports it as published anyway, because a national methodology is
    not this repository's to silently correct. This test records that it is
    known, so that using it is a decision.
    """

    SIZES = ((10.0, 8.0), (30.0, 20.0), (50.0, 28.0), (80.0, 35.0))

    def test_only_the_two_needle_pine_row_exceeds_solid_wood(self):
        failing = {
            key for key in FOREST_TYPES if implausible_sizes(key, self.SIZES)
        }

        assert failing == {"pine_two_needle"}, (
            f"the physically impossible rows are now {sorted(failing)}. If one "
            "was corrected upstream, or another has gone wrong, "
            "docs/ml/ALLOMETRIC_COEFFICIENTS.md needs updating with it"
        )

    def test_it_fails_at_every_size_not_just_large_trees(self):
        """A wrong exponent bites only on big trees; a wrong coefficient bites
        everywhere. This one bites everywhere, which says coefficient."""
        assert implausible_sizes("pine_two_needle", self.SIZES) == self.SIZES

    def test_how_far_over_it_is(self):
        result = aboveground_biomass("pine_two_needle", DBH_CM, HEIGHT_M)
        ratio = result.total_kg / solid_cylinder_mass_kg(DBH_CM, HEIGHT_M)

        assert ratio > 2.0, f"now only {ratio:.2f}x solid wood"

    def test_the_sibling_row_is_fine(self):
        """Same forest, same author generation, one order of magnitude apart in
        the stem coefficient. The three-needle row lands where a tree lands."""
        assert not implausible_sizes("pine_three_needle", self.SIZES)


class TestTheBoundIsPhysicsNotAFit:
    def test_a_solid_cylinder_is_computed_from_dimensions_alone(self):
        expected = math.pi * (DBH_CM / 200.0) ** 2 * HEIGHT_M * 1000.0

        assert solid_cylinder_mass_kg(DBH_CM, HEIGHT_M) == pytest.approx(expected)

    def test_it_is_far_above_any_real_tree(self):
        """Every forest type except the known-bad row should sit well under it —
        a real stem tapers and a real crown is mostly air."""
        for key in FOREST_TYPES:
            if key == "pine_two_needle":
                continue
            ratio = (
                aboveground_biomass(key, DBH_CM, HEIGHT_M).total_kg
                / solid_cylinder_mass_kg(DBH_CM, HEIGHT_M)
            )
            assert 0.1 < ratio < 0.9, f"{key} sits at {ratio:.2f}x solid wood"

    def test_it_refuses_a_dimension_that_is_not_a_measurement(self):
        with pytest.raises(ValueError):
            solid_cylinder_mass_kg(0.0, HEIGHT_M)


class TestTheProductCanCostATreeThailandsWay:
    """`calculate_carbon(..., forest_type=...)` — opt-in, never the default.

    Chave stays the production model. What this adds is the ability to report
    the number a Thai carbon project is actually accounted by, from the same
    measurements, without changing what any existing caller gets.
    """

    def test_it_changes_nothing_unless_asked(self):
        from pipeline.allometric import calculate_carbon

        default = calculate_carbon(dbh_cm=30, height_m=20, species_sci="Tectona grandis")

        assert default.method == "chave_pantropical"

    def test_a_forest_type_switches_the_model(self):
        from pipeline.allometric import calculate_carbon

        result = calculate_carbon(dbh_cm=30, height_m=20, forest_type="mixed_deciduous")
        expected = aboveground_biomass("mixed_deciduous", 30.0, 20.0)

        assert result.method == "tver_forest_type"
        assert result.agb_kg == pytest.approx(expected.total_kg)
        assert "อบก" in result.uncertainty_basis or "T-VER" in result.source

    def test_the_species_density_does_not_enter_the_biomass(self):
        """T-VER is fitted on D and H alone. Two species with very different
        densities must give the same AGB for the same forest type — if they do
        not, density has leaked into an equation that never took one."""
        from pipeline.allometric import calculate_carbon

        light = calculate_carbon(
            dbh_cm=30, height_m=20, species_sci="Tectona grandis", forest_type="dry_evergreen"
        )
        heavy = calculate_carbon(
            dbh_cm=30, height_m=20, species_sci="Afzelia xylocarpa", forest_type="dry_evergreen"
        )

        assert light.agb_kg == pytest.approx(heavy.agb_kg)

    def test_it_does_not_report_a_density_band_around_a_densityless_model(self):
        """The Chave path propagates ±10% on wood density. Doing that here would
        put an interval on a number density never touched."""
        from pipeline.allometric import calculate_carbon

        result = calculate_carbon(dbh_cm=30, height_m=20, forest_type="mixed_deciduous")

        assert result.co2eq_low_kg == result.co2eq_kg == result.co2eq_high_kg
        assert "ไม่มีช่วงความไม่แน่นอน" in result.uncertainty_basis

    def test_the_impossible_row_is_refused_rather_than_costed(self):
        """Reporting it as published in tver.py is right. Handing a customer a
        3.2-tonne tree is not."""
        from pipeline.allometric import calculate_carbon

        with pytest.raises(ValueError, match="more mass than solid wood"):
            calculate_carbon(dbh_cm=30, height_m=20, forest_type="pine_two_needle")

    def test_an_unknown_forest_type_is_refused(self):
        from pipeline.allometric import calculate_carbon

        with pytest.raises(KeyError, match="unknown forest type"):
            calculate_carbon(dbh_cm=30, height_m=20, forest_type="rainforest")

    def test_the_carbon_chain_still_applies(self):
        """T-VER supplies AGB. Root:shoot, carbon fraction and 44/12 are the
        same chain as every other route through this function."""
        from pipeline.allometric import (
            CO2_PER_CARBON,
            DEFAULT_CARBON_FRACTION,
            DEFAULT_ROOT_TO_SHOOT_TROPICAL,
            calculate_carbon,
        )

        result = calculate_carbon(dbh_cm=30, height_m=20, forest_type="mixed_deciduous")

        assert result.bgb_kg == pytest.approx(result.agb_kg * DEFAULT_ROOT_TO_SHOOT_TROPICAL)
        assert result.carbon_kg == pytest.approx(result.biomass_kg * DEFAULT_CARBON_FRACTION)
        assert result.co2eq_kg == pytest.approx(result.carbon_kg * CO2_PER_CARBON)

    def test_thailands_answer_and_chaves_are_in_the_same_country(self):
        """Not a validation — neither has been checked against a Thai tree. But
        a factor-of-two gap would mean one of them is being used wrong."""
        from pipeline.allometric import calculate_carbon

        chave = calculate_carbon(dbh_cm=30, height_m=20).agb_kg
        for key in ("dry_evergreen", "tropical_rain", "mixed_deciduous"):
            tver_agb = calculate_carbon(dbh_cm=30, height_m=20, forest_type=key).agb_kg
            assert 0.6 < tver_agb / chave < 1.6, f"{key} sits at {tver_agb / chave:.2f}x Chave"
