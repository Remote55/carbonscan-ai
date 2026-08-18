"""Where the wood density came from, and what it took to find out.

Density is the largest lever this pipeline pulls on the carbon figure. Chave is
close to linear in it (exponent 0.976), so on the same tree — DBH 30 cm, H 20 m
— naming a species moves CO2e across the five rows in species_db on the strength
of one number per row.

Those numbers had no source column and no verified flag, while the allometric
coefficients beside them had both and were gated on them: the product was
refusing the cited quantity and trusting the uncited one. Worse than uncited,
they looked like the wrong quantity. Chave takes ρ as BASIC specific gravity,
oven-dry mass over green volume; timber tables publish air-dry density at 12%
moisture, which is larger.

That was written down as a suspicion in 2026-08-13 and this file asserted only
that the gap was declared. It is now settled. Reyes, Brown, Chapman and Lugo
1992, "Wood densities of tropical tree species", USDA Forest Service GTR SO-88
— public domain, a copy is in `data/reference/` — reports basic density for
tropical Asian species and gives a published air-dry-to-basic regression from
Chudnoff 1984 (379 trees, r² = 0.988).

Both routes agree wherever both exist:

    Tectona grandis        shipped 660  →  541 converted   measured 0.50, 0.55
    Dipterocarpus alatus   shipped 720  →  589 converted   genus 0.52-0.62
    Hevea brasiliensis     shipped 580  →  477 converted   measured 0.53

So the values moved. Three rows now carry a measured basic density and are
flagged verified; two carry a converted one and are not, because the air-dry
figure they were converted from still has no source.

These tests pin that state, and each is written to fail if a row is flipped to
verified without a citation behind it.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from pipeline.allometric import basic_density_from_air_dry, calculate_carbon, load_species_db

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "species_db.csv"

#: What each row shipped before 2026-08-14, when every density was an air-dry
#: figure of unknown provenance. Kept so the conversion can be checked against
#: the independent measurements rather than asserted.
SHIPPED_AIR_DRY = {
    "Tectona grandis": 660.0,
    "Dipterocarpus alatus": 720.0,
    "Bambusa spp.": 650.0,
    "Hevea brasiliensis": 580.0,
    "Afzelia xylocarpa": 850.0,
}


class TestTheDatabaseDeclaresItsProvenance:
    def test_every_row_states_a_basis_and_a_source(self):
        with CSV_PATH.open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        assert rows, "species_db.csv is empty"
        for row in rows:
            for column in ("density_basis", "density_source", "density_verified"):
                assert column in row, f"{column} is missing from species_db.csv"
                assert (row[column] or "").strip(), (
                    f"{row['name_sci']} leaves {column} blank; "
                    "an unfilled cell reads as 'fine' and is not"
                )

    def test_a_verified_row_cites_a_measured_basic_density(self):
        """The flag means one thing: somebody read a basic density out of a
        named source. It is not 'looks about right'."""
        for name, species in load_species_db().items():
            if not species.density_verified:
                continue
            assert species.density_basis.startswith("basic_measured"), (
                f"{name} is flagged verified with basis {species.density_basis!r}; "
                "verified means a measured basic density, not a converted one"
            )
            assert "Reyes" in species.density_source, (
                f"{name} is flagged verified but its source does not name a "
                f"reference: {species.density_source!r}"
            )

    def test_an_unverified_row_says_what_is_still_missing(self):
        """Two rows are converted rather than measured. The conversion fixes the
        basis; it does not supply a source for the number that went into it."""
        unverified = {n: s for n, s in load_species_db().items() if not s.density_verified}

        assert unverified, (
            "every row is now verified — if Afzelia and Bambusa were sourced, "
            "update this file rather than deleting the test"
        )
        for name, species in unverified.items():
            assert species.density_basis == "basic_converted_unsourced", name
            assert "no source" in species.density_source or "not yet cited" in species.density_source, (
                f"{name} is unverified but its source does not say what is missing"
            )

    def test_the_teak_row_carries_the_measurement_that_settled_it(self):
        """The row the whole question was opened on."""
        teak = load_species_db()["Tectona grandis"]

        assert teak.wood_density == 525
        assert teak.density_basis == "basic_measured"
        assert "0.50" in teak.density_source and "0.55" in teak.density_source
        assert "660" in teak.density_source, (
            "the row should record what it replaced; a value that changed "
            "silently is the thing this column exists to prevent"
        )


class TestTheConversionAgreesWithTheMeasurements:
    """The load-bearing evidence. If these two routes disagreed, the air-dry
    diagnosis would be a story rather than a finding."""

    def test_teak_converts_into_its_measured_range(self):
        converted = basic_density_from_air_dry(SHIPPED_AIR_DRY["Tectona grandis"])

        assert 500 <= converted <= 550, (
            f"660 air-dry converts to {converted:.0f}, outside the 500-550 that "
            "Reyes et al. measured directly for Tectona grandis"
        )

    def test_dipterocarpus_converts_into_its_genus_range(self):
        converted = basic_density_from_air_dry(SHIPPED_AIR_DRY["Dipterocarpus alatus"])

        assert 520 <= converted <= 620, (
            f"720 air-dry converts to {converted:.0f}, outside the 0.52-0.62 "
            "the genus spans in Reyes et al."
        )

    def test_the_conversion_always_lowers_a_density(self):
        """Basic density is oven-dry mass over GREEN volume — the larger volume
        — so it is below the air-dry figure for any real wood. A conversion that
        raised a value would be the wrong way round."""
        for name, air_dry in SHIPPED_AIR_DRY.items():
            assert basic_density_from_air_dry(air_dry) < air_dry, name

    def test_it_refuses_a_density_that_is_not_one(self):
        for bad in (0.0, -1.0, float("nan"), float("inf")):
            with pytest.raises(ValueError):
                basic_density_from_air_dry(bad)


class TestTheFigureCarriesTheCaveat:
    def test_an_unverified_density_says_so_in_the_result(self):
        """A caller reading uncertainty_basis must learn this, not have to read
        the CSV to find out."""
        result = calculate_carbon(dbh_cm=30, height_m=20, species_sci="Afzelia xylocarpa")

        assert "ยังไม่มีแหล่งอ้างอิง" in result.uncertainty_basis

    def test_a_verified_density_does_not_carry_the_caveat(self):
        """Otherwise the warning means nothing — it would be on every tree."""
        result = calculate_carbon(dbh_cm=30, height_m=20, species_sci="Tectona grandis")

        assert "ยังไม่มีแหล่งอ้างอิง" not in result.uncertainty_basis

    def test_bamboo_says_the_model_does_not_cover_it(self):
        """Chave 2014 is a pantropical model for trees. A bamboo culm is a
        grass, and the figure is reported with that said out loud."""
        result = calculate_carbon(dbh_cm=30, height_m=20, species_sci="Bambusa spp.")

        assert "หญ้า" in result.uncertainty_basis
        assert "Chave" in result.uncertainty_basis

    def test_an_unknown_species_is_unaffected(self):
        """That path has its own caveat and should not gain a second one about a
        species-specific density it never used."""
        result = calculate_carbon(dbh_cm=30, height_m=20, species_sci=None)

        assert "ไม่ทราบชนิดไม้" in result.uncertainty_basis
        assert "หญ้า" not in result.uncertainty_basis


class TestWhatTheChangeCost:
    def test_the_new_figures_are_pinned(self):
        """The values the pipeline produces now. Every one is lower, because
        every density was an air-dry figure and basic density is smaller."""
        expected = {
            "Tectona grandis": 1091.0,
            "Dipterocarpus alatus": 1263.1,
            "Bambusa spp.": 1071.5,
            "Hevea brasiliensis": 1101.1,
            "Afzelia xylocarpa": 1430.6,
        }
        for name, co2eq in expected.items():
            result = calculate_carbon(dbh_cm=30, height_m=20, species_sci=name)
            assert result.co2eq_kg == pytest.approx(co2eq, abs=0.1), name

    def test_every_species_now_reports_less_carbon_than_before(self):
        """The direction is the whole point: the pipeline was overstating
        biomass, on every named species, by feeding a model that wants basic
        density a number that was air-dry."""
        was = {
            "Tectona grandis": 1364.0,
            "Dipterocarpus alatus": 1484.9,
            "Bambusa spp.": 1300.5,
            "Hevea brasiliensis": 1202.4,
            "Afzelia xylocarpa": 1746.1,
        }
        for name, before in was.items():
            now = calculate_carbon(dbh_cm=30, height_m=20, species_sci=name).co2eq_kg
            assert now < before, f"{name} did not fall: {before} -> {now}"

    def test_density_is_the_dominant_lever_it_is_claimed_to_be(self):
        """The premise of all of the above. If naming a species stopped moving
        the number, the provenance of that number would matter much less.

        The spread narrowed from 45% to 34% when the values were corrected,
        which is what should happen: the air-dry figures were scattered by their
        sources' conventions as well as by the wood.
        """
        results = {
            name: calculate_carbon(dbh_cm=30, height_m=20, species_sci=name).co2eq_kg
            for name in load_species_db()
        }
        spread = max(results.values()) / min(results.values()) - 1.0

        assert spread > 0.25, f"species choice moves CO2e by only {spread:.0%}"
