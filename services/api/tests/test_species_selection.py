"""Naming the species, which is the largest accuracy gain this API can offer.

Measured on the 65 Demol trees weighed after felling: Chave at the default
600 kg/m3 is 41.0% out with a +40.8% bias; at each tree's own measured density
it is 20.0% out. About half the carbon error is not knowing what the wood is.

process_points has accepted a species since it was written, run_pipeline has
had the argument, and the CLI has had the flag. Nothing ever passed one, because
the HTTP endpoint had no field for it.
"""

from __future__ import annotations

import pytest

import app.api.v1.upload as upload_mod
from app.services import species_catalogue
from tests.test_upload_analyze import FAKE_RESULT


@pytest.fixture(autouse=True)
def clear_catalogue_cache():
    species_catalogue.load_species.cache_clear()
    yield
    species_catalogue.load_species.cache_clear()


class TestCatalogue:
    def test_reads_the_pipelines_own_data_file(self):
        catalogue = species_catalogue.load_species()
        assert "Tectona grandis" in catalogue
        assert catalogue["Tectona grandis"].name_th == "สัก"
        # 525, not the 660 this asserted until 2026-08-14. That was an air-dry
        # density at 12% moisture; Chave takes basic specific gravity, and Reyes
        # et al. 1992 measures Tectona grandis at 0.50 and 0.55 basic. See
        # docs/ml/WOOD_DENSITY_PROVENANCE.md.
        assert catalogue["Tectona grandis"].wood_density == 525

    def test_reports_that_no_equation_has_been_verified(self):
        """Naming a species buys its density, not its equation. If this ever
        flips, the copy telling users so needs revisiting."""
        catalogue = species_catalogue.load_species()
        assert catalogue, "catalogue is empty"
        assert not any(item.coefficients_verified for item in catalogue.values())

    def test_a_missing_file_disables_the_feature_rather_than_breaking_analysis(
        self, monkeypatch, tmp_path
    ):
        from app.core.config import settings

        monkeypatch.setattr(settings, "ML_DIR", str(tmp_path))
        species_catalogue.load_species.cache_clear()
        assert species_catalogue.load_species() == {}
        assert species_catalogue.is_known("Tectona grandis") is False


@pytest.mark.asyncio
class TestListingEndpoint:
    async def test_offers_the_species_a_caller_may_name(self, client):
        response = await client.get("/api/v1/upload/species")

        assert response.status_code == 200
        names = [item["name_sci"] for item in response.json()["species"]]
        assert "Tectona grandis" in names

    async def test_each_entry_carries_what_a_picker_needs(self, client):
        response = await client.get("/api/v1/upload/species")

        first = response.json()["species"][0]
        assert set(first) == {
            "name_sci",
            "name_th",
            "name_en",
            "wood_density_kg_m3",
            # Both flags travel, because both are false and each means something
            # different. density_verified was added after the density was found
            # to have no cited source at all — and, for the one row with any
            # evidence, to look like an air-dry figure where Chave wants a basic
            # one. A picker that showed the density without it would present an
            # unchecked number as the reason to choose a species.
            "coefficients_verified",
            "density_verified",
        }

    async def test_the_picker_distinguishes_checked_densities_from_converted(self, client):
        """This asserted that no row claims a verified density, which was true
        while every value was an unsourced air-dry figure.

        Three now carry a basic density measured in Reyes et al. 1992 and are
        flagged; two were converted from an air-dry figure that itself has no
        source, and are not. The flag has to keep separating those, because it is
        what the picker shows a user deciding whether to trust a number.
        """
        rows = (await client.get("/api/v1/upload/species")).json()["species"]

        assert rows, "no species returned"
        verified = {row["name_sci"] for row in rows if row["density_verified"]}
        unverified = {row["name_sci"] for row in rows if not row["density_verified"]}

        assert verified and unverified, (
            f"every row now reports density_verified={bool(verified)}. If the "
            "last two were sourced, update this test rather than deleting it"
        )
        assert unverified == {"Afzelia xylocarpa", "Bambusa spp."}, (
            f"the unsourced rows are now {sorted(unverified)}; "
            "docs/ml/WOOD_DENSITY_PROVENANCE.md says which two should be"
        )

    async def test_says_what_happens_if_you_do_not_choose(self, client):
        response = await client.get("/api/v1/upload/species")

        assert "ความหนาแน่น" in response.json()["note"]


@pytest.mark.asyncio
class TestAnalyzeAcceptsSpecies:
    async def _post(self, client, **data):
        return await client.post(
            "/api/v1/upload/analyze",
            files={"file": ("plot.las", b"dummy-point-cloud-bytes", "application/octet-stream")},
            data=data,
        )

    async def test_a_named_species_reaches_the_pipeline(self, client, monkeypatch):
        seen: dict[str, object] = {}

        def capture(path, **kwargs):
            seen.update(kwargs)
            return FAKE_RESULT

        monkeypatch.setattr(upload_mod, "run_pipeline", capture)

        response = await self._post(client, species="Tectona grandis")

        assert response.status_code == 200, response.text
        assert seen.get("species") == "Tectona grandis"

    async def test_omitting_it_is_normal_and_passes_nothing(self, client, monkeypatch):
        seen: dict[str, object] = {}

        def capture(path, **kwargs):
            seen.update(kwargs)
            return FAKE_RESULT

        monkeypatch.setattr(upload_mod, "run_pipeline", capture)

        response = await self._post(client)

        assert response.status_code == 200, response.text
        assert seen.get("species") is None

    async def test_blank_is_treated_as_omitted(self, client, monkeypatch):
        seen: dict[str, object] = {}
        monkeypatch.setattr(
            upload_mod, "run_pipeline", lambda path, **kw: (seen.update(kw), FAKE_RESULT)[1]
        )

        response = await self._post(client, species="   ")

        assert response.status_code == 200, response.text
        assert seen.get("species") is None

    async def test_an_unknown_name_is_refused_not_quietly_ignored(self, client, monkeypatch):
        """Falling back to the default density would answer with a number that
        looks like it used the species the caller asked for, and be 40% out
        without saying so."""
        called = False

        def should_not_run(path, **kwargs):
            nonlocal called
            called = True
            return FAKE_RESULT

        monkeypatch.setattr(upload_mod, "run_pipeline", should_not_run)

        response = await self._post(client, species="Tectona grandisss")

        assert response.status_code == 422
        assert "Unknown species" in response.text
        assert called is False, "the pipeline ran with a species it did not have"
