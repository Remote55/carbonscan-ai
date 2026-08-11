"""Where the wood density came from, and what happens while nobody knows.

Density is the largest lever this pipeline actually pulls on the carbon figure.
Chave is close to linear in it (exponent 0.976), so on the same tree — DBH 30 cm,
H 20 m — naming a species moves CO2e from 1202 kg to 1746 kg across the five
rows in species_db, a 45% spread, entirely on the strength of one number per row.

That number had no source column and no verified flag, while the allometric
coefficients sitting beside it had both and were gated on them. The product was
refusing the cited quantity and trusting the uncited one.

Worse than uncited: probably the wrong quantity. Chave takes ρ as BASIC specific
gravity, oven-dry mass over green volume. Timber tables publish air-dry density
at 12% moisture, which is larger. World Agroforestry's Tectona grandis profile
gives "610-750 kg/m³ at 12% mc" and species_db carries 660 — the middle of the
air-dry range — where the Global Wood Density Database gives 0.60 g/cm³ basic.

Nothing here asserts a corrected value, because none has been sourced. These
assert that the gap is declared rather than hidden.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from pipeline.allometric import calculate_carbon, load_species_db

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "species_db.csv"


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

    def test_nothing_claims_a_verified_density_yet(self):
        """The flag is only allowed to be true once a basic density is cited.

        If this test fails, someone has flipped a row — check that
        density_source names a database and density_basis says `basic`, then
        delete the row from this assertion rather than the assertion.
        """
        unverified = {
            name for name, s in load_species_db().items() if not s.density_verified
        }
        assert unverified == set(load_species_db()), (
            "a row claims a verified density; confirm its source is a basic "
            "density before trusting the carbon figure it produces"
        )

    def test_the_teak_row_records_the_evidence_that_it_is_air_dry(self):
        """The one row anything is known about, and it points the wrong way."""
        teak = load_species_db()["Tectona grandis"]

        assert teak.wood_density == 660
        assert "air_dry" in teak.density_basis
        assert "0.60" in teak.density_source or "basic" in teak.density_source


class TestTheFigureCarriesTheCaveat:
    def test_an_unverified_density_says_so_in_the_result(self):
        """A caller reading uncertainty_basis must learn this, not have to read
        the CSV to find out."""
        result = calculate_carbon(dbh_cm=30, height_m=20, species_sci="Tectona grandis")

        assert "air-dry" in result.uncertainty_basis
        assert "ยังไม่มีแหล่งอ้างอิง" in result.uncertainty_basis

    def test_an_unknown_species_is_unaffected(self):
        """That path has its own caveat and should not gain a second one about a
        species-specific density it never used."""
        result = calculate_carbon(dbh_cm=30, height_m=20, species_sci=None)

        assert "air-dry" not in result.uncertainty_basis
        assert "ไม่ทราบชนิดไม้" in result.uncertainty_basis

    def test_the_numbers_did_not_move(self):
        """This change declares a problem; it does not pretend to fix one.

        Replacing five densities on the strength of evidence for one species
        would be a different guess, not a correction. These are the values the
        pipeline produced before the provenance columns existed.
        """
        expected = {
            "Tectona grandis": 1364.0,
            "Dipterocarpus alatus": 1484.9,
            "Bambusa spp.": 1300.5,
            "Hevea brasiliensis": 1202.4,
            "Afzelia xylocarpa": 1746.1,
        }
        for name, co2eq in expected.items():
            result = calculate_carbon(dbh_cm=30, height_m=20, species_sci=name)
            assert result.co2eq_kg == pytest.approx(co2eq, abs=0.1), name

    def test_density_is_the_dominant_lever_it_is_claimed_to_be(self):
        """The premise of all of the above. If naming a species stopped moving
        the number, the provenance of that number would matter much less."""
        results = {
            name: calculate_carbon(dbh_cm=30, height_m=20, species_sci=name).co2eq_kg
            for name in load_species_db()
        }
        spread = max(results.values()) / min(results.values()) - 1.0

        assert spread > 0.40, f"species choice moves CO2e by only {spread:.0%}"
