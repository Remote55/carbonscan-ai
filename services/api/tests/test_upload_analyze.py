"""Tests for the synchronous point-cloud analyze endpoint (MVP).

The ML pipeline itself runs out-of-process (subprocess to the ml venv); here we
mock ``run_pipeline`` so the test exercises the HTTP plumbing + validation only,
with no heavy ML deps and no real subprocess.
"""

import pytest

from app.schemas.analyze import AnalyzeMetadata, AnalyzeResponse

FAKE_RESULT = {
    "metadata": {
        "pipeline_version": "0.3.0",
        "git_commit": "0036996",
        "git_dirty": False,
        "wood_leaf_backend": "tlsep",
        "input_sha256": "a" * 64,
        "checkpoint_sha256": None,
        "algorithms": {
            "ground_segmentation": "percentile_grid",
            "height_normalization": "knn_idw",
            "chm": "max_z_morphology",
            "tree_segmentation": "watershed",
            "wood_leaf": "tlsep",
            "qsm": "ransac_dbh_maxz_height_taper_volume",
            "species": "stub",
            "allometric": "species_db_or_chave_fallback",
        },
        "evidence_status": "baseline",
        "candidate_status": "candidate_not_evaluated",
        "n_input_points": 1000,
        "status": "ok",
    },
    "summary": {"total_trees": 2, "total_carbon_kg": 123.45, "total_co2eq_kg": 452.6},
    "trees": [
        {
            "tree_id": 1, "species_sci": None, "dbh_cm": 20.1, "height_m": 12.3,
            "volume_m3": 0.2, "biomass_kg": 100.0, "carbon_kg": 47.0, "co2eq_kg": 172.0,
            "location": {"x": 1.0, "y": 2.0}, "point_count": 500,
        },
        {
            "tree_id": 2, "species_sci": None, "dbh_cm": 18.0, "height_m": 11.0,
            "volume_m3": 0.15, "biomass_kg": 80.0, "carbon_kg": 37.0, "co2eq_kg": 135.6,
            "location": {"x": 3.0, "y": 4.0}, "point_count": 400,
        },
    ],
}


def test_analyze_response_uses_typed_metadata_schema():
    assert AnalyzeResponse.model_fields["metadata"].annotation is AnalyzeMetadata


@pytest.mark.asyncio
async def test_analyze_returns_carbon_summary(client, monkeypatch):
    import app.api.v1.upload as upload_mod

    monkeypatch.setattr(upload_mod, "run_pipeline", lambda path, **kw: FAKE_RESULT)

    resp = await client.post(
        "/api/v1/upload/analyze",
        files={"file": ("plot.las", b"dummy-point-cloud-bytes", "application/octet-stream")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["summary"]["total_trees"] == 2
    assert data["summary"]["total_carbon_kg"] == 123.45
    assert len(data["trees"]) == 2
    assert data["trees"][0]["dbh_cm"] == 20.1
    assert data["metadata"]["wood_leaf_backend"] == "tlsep"
    assert data["metadata"]["evidence_status"] == "baseline"
    assert data["metadata"]["algorithms"]["species"] == "stub"
    assert data["metadata"]["checkpoint_sha256"] is None
    assert data["metadata"]["git_dirty"] is False


@pytest.mark.asyncio
async def test_analyze_rejects_bad_extension(client):
    resp = await client.post(
        "/api/v1/upload/analyze",
        files={"file": ("photo.jpg", b"x", "image/jpeg")},
    )
    assert resp.status_code == 400
