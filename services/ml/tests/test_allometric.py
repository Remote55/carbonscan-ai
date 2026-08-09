"""Tests for allometric carbon calculation.

These tests use known input/output pairs from the literature to verify
correctness of the implementation.
"""

import pytest

from pipeline.allometric import (
    CO2_PER_CARBON,
    DEFAULT_CARBON_FRACTION,
    DEFAULT_ROOT_TO_SHOOT_TROPICAL,
    calculate_agb_chave_pantropical,
    calculate_agb_species_specific,
    calculate_carbon,
    calculate_carbon_from_volume,
    load_species_db,
)


class TestSpeciesDb:
    def test_load_species_db(self):
        db = load_species_db()
        assert len(db) >= 5
        assert "Tectona grandis" in db
        assert "Dipterocarpus alatus" in db
        assert "Bambusa spp." in db
        assert "Hevea brasiliensis" in db
        assert "Afzelia xylocarpa" in db

    def test_teak_properties(self):
        db = load_species_db()
        teak = db["Tectona grandis"]
        assert teak.name_th == "สัก"
        assert 500 <= teak.wood_density <= 800  # sanity bounds
        assert teak.agb_a is not None
        assert teak.carbon_fraction == DEFAULT_CARBON_FRACTION

    def test_makha_dense(self):
        """Mahka should be the densest in our DB."""
        db = load_species_db()
        densities = {name: sp.wood_density for name, sp in db.items()}
        assert densities["Afzelia xylocarpa"] == max(densities.values())


class TestChavePantropical:
    """Chave et al. 2014 model verification."""

    def test_chave_formula_sanity(self):
        """Manual calculation for ρ=0.66, DBH=30, H=18:
        AGB = 0.0673 × (0.66 × 900 × 18)^0.976
            = 0.0673 × (10692)^0.976
            ≈ 0.0673 × 9438.4
            ≈ 635 kg
        """
        agb = calculate_agb_chave_pantropical(dbh_cm=30, height_m=18, wood_density=660)
        assert 500 < agb < 800  # ballpark range

    def test_a_seedling_weighs_almost_nothing(self):
        """`agb >= 0` used to be the assertion here. The formula is a positive
        constant times a positive base raised to a positive power, so it could
        not fail for any input the function accepts — it asserted arithmetic,
        not behaviour. What is worth checking is that the tiny end of the range
        stays tiny rather than collapsing to zero or blowing up."""
        agb = calculate_agb_chave_pantropical(dbh_cm=0.01, height_m=0.01, wood_density=600)
        assert 0 < agb < 0.001

    def test_output_rises_with_every_input(self):
        base = calculate_agb_chave_pantropical(dbh_cm=30, height_m=18, wood_density=600)
        assert calculate_agb_chave_pantropical(31, 18, 600) > base
        assert calculate_agb_chave_pantropical(30, 19, 600) > base
        assert calculate_agb_chave_pantropical(30, 18, 610) > base

    def test_diameter_dominates_height(self):
        """AGB goes as (rho·D²·H)^0.976, so doubling D must outweigh doubling H.
        A transposed exponent would still pass a monotonicity check."""
        wider = calculate_agb_chave_pantropical(dbh_cm=60, height_m=18, wood_density=600)
        taller = calculate_agb_chave_pantropical(dbh_cm=30, height_m=36, wood_density=600)
        assert wider > taller * 1.8


class TestSpeciesSpecific:
    def test_teak_known_dbh_height(self):
        """For a teak DBH=25cm, H=15m, AGB should be in expected range
        based on Tsutsumi 1983 coefficients (a=0.0509, b=2.15, c=0.70).
        """
        db = load_species_db()
        teak = db["Tectona grandis"]
        agb = calculate_agb_species_specific(dbh_cm=25, height_m=15, species=teak)
        # 0.0509 × 25^2.15 × 15^0.70 ≈ 0.0509 × 909 × 6.83 ≈ 316 kg
        assert 200 < agb < 500


class TestFullCarbonCalc:
    def test_teak_full_calculation(self):
        """End-to-end test with teak.

        Teak is costed with Chave now, not its own equation: no row in
        species_db has had its coefficients checked against the cited paper, and
        four of the five disagree with Chave by 1.4x-3.5x with a diameter-
        dependent ratio. See test_allometric_coefficient_gate.py for the gate
        itself; this test only asserts the chain of arithmetic that follows,
        whichever model produced the AGB.
        """
        result = calculate_carbon(dbh_cm=30, height_m=18, species_sci="Tectona grandis")

        assert result.species_sci == "Tectona grandis"
        assert result.method == "chave_pantropical"
        assert result.wood_density == 660, "teak's own density must still be used"
        assert result.agb_kg > 0
        assert result.bgb_kg == pytest.approx(
            result.agb_kg * DEFAULT_ROOT_TO_SHOOT_TROPICAL,
            rel=1e-6,
        )
        assert result.biomass_kg == pytest.approx(result.agb_kg + result.bgb_kg, rel=1e-6)
        assert result.carbon_kg == pytest.approx(
            result.biomass_kg * DEFAULT_CARBON_FRACTION,
            rel=1e-6,
        )
        assert result.co2eq_kg == pytest.approx(result.carbon_kg * CO2_PER_CARBON, rel=1e-6)

    def test_unknown_species_falls_back_to_chave(self):
        """Unknown species → pantropical model."""
        result = calculate_carbon(dbh_cm=30, height_m=18, species_sci="Unknown sp.")
        assert result.method == "chave_pantropical"

    def test_none_species_uses_chave(self):
        result = calculate_carbon(dbh_cm=30, height_m=18, species_sci=None)
        assert result.method == "chave_pantropical"
        assert result.wood_density == 600.0  # default tropical

    def test_negative_dbh_raises(self):
        with pytest.raises(ValueError, match="DBH must be positive"):
            calculate_carbon(dbh_cm=-5, height_m=18, species_sci="Tectona grandis")

    def test_zero_height_raises(self):
        with pytest.raises(ValueError, match="Height must be positive"):
            calculate_carbon(dbh_cm=30, height_m=0, species_sci="Tectona grandis")


class TestVolumeMethod:
    def test_volume_density_method(self):
        """Volume × density should give reasonable carbon."""
        # 0.5 m³ × 660 kg/m³ = 330 kg AGB
        result = calculate_carbon_from_volume(volume_m3=0.5, wood_density=660)
        assert result.method == "volume_density"
        assert result.agb_kg == pytest.approx(330, rel=1e-3)

    def test_cross_validation_methods_in_ballpark(self):
        """Allometric vs Volume methods should be in the same order of magnitude.

        The cone volume approximation V = (1/3)πr²H is intentionally very crude
        — a real tree isn't a cone (more like a tapered cylinder), so we only
        check that both methods give answers within a 3× ratio. The real cross-
        validation between species-specific allometric and QSM-derived volume
        in production will use proper QSM volume from PointNet++/cylinder
        fitting, which is much more accurate than this synthetic test.
        """
        teak_density = 660  # kg/m³

        allometric = calculate_carbon(dbh_cm=30, height_m=18, species_sci="Tectona grandis")
        # Crude cone approximation: V ≈ (1/3) × π × r² × h
        # r = DBH/2/100 = 0.15m, h = 18m → V ≈ 0.42 m³
        volume_estimate = (1 / 3) * 3.14159 * (0.15**2) * 18
        from_volume = calculate_carbon_from_volume(volume_estimate, teak_density)

        ratio = allometric.biomass_kg / from_volume.biomass_kg
        # Cone underestimates real tree volume → allometric may be 2-3× higher
        assert 0.33 < ratio < 3.0, f"Methods disagree too much: {ratio:.2f}"


class TestConstants:
    def test_co2_per_carbon_ratio(self):
        """44 g/mol CO2 / 12 g/mol C ≈ 3.667"""
        assert CO2_PER_CARBON == pytest.approx(3.667, abs=0.01)

    def test_carbon_fraction_default(self):
        """IPCC 2006 default."""
        assert DEFAULT_CARBON_FRACTION == 0.47

    def test_root_to_shoot_default(self):
        """IPCC 2006 tropical default."""
        assert DEFAULT_ROOT_TO_SHOOT_TROPICAL == 0.24
