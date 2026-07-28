"""Tests for the synchronous point-cloud analyze endpoint (MVP).

The ML pipeline itself runs out-of-process (subprocess to the ml venv); here we
mock ``run_pipeline`` so the test exercises the HTTP plumbing + validation only,
with no heavy ML deps and no real subprocess.
"""

import logging
import subprocess

import pytest

from app.core.config import settings
from app.schemas.analyze import AnalyzeMetadata, AnalyzeResponse
from app.services.pipeline_runner import PipelineError, probe_pipeline_runtime, run_pipeline

MINIMAL_ASCII_PLY = b"""ply
format ascii 1.0
element vertex 1
property float x
property float y
property float z
end_header
0 0 0
"""

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


@pytest.mark.asyncio
async def test_demo_analyze_rejects_malformed_ply_before_pipeline(client, monkeypatch):
    import app.api.v1.upload as upload_mod

    token = "f" * 64
    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
    monkeypatch.setattr(settings, "TREEQ_DEMO_TOKEN", token)
    monkeypatch.setattr(settings, "RATE_LIMIT_UPLOAD", 100)

    def pipeline_must_not_run(*args, **kwargs):
        raise AssertionError("pipeline must not run for malformed PLY")

    monkeypatch.setattr(upload_mod, "run_pipeline", pipeline_must_not_run)
    response = await client.post(
        "/api/v1/upload/analyze",
        headers={"X-TreeQ-Demo-Token": token},
        files={"file": ("tree.ply", b"not a ply", "application/octet-stream")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_demo_analyze_rejects_oversize_stream_before_pipeline(client, monkeypatch):
    import app.api.v1.upload as upload_mod

    token = "1" * 64
    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
    monkeypatch.setattr(settings, "TREEQ_DEMO_TOKEN", token)
    monkeypatch.setattr(settings, "TREEQ_DEMO_MAX_UPLOAD_SIZE_MB", 0)
    monkeypatch.setattr(settings, "RATE_LIMIT_UPLOAD", 100)

    def pipeline_must_not_run(*args, **kwargs):
        raise AssertionError("pipeline must not run for oversized input")

    monkeypatch.setattr(upload_mod, "run_pipeline", pipeline_must_not_run)
    response = await client.post(
        "/api/v1/upload/analyze",
        headers={"X-TreeQ-Demo-Token": token},
        files={"file": ("tree.ply", MINIMAL_ASCII_PLY, "application/octet-stream")},
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "File too large"}


@pytest.mark.asyncio
async def test_pipeline_failure_response_hides_operator_detail(client, monkeypatch, caplog):
    import app.api.v1.upload as upload_mod

    operator_detail = r"C:\Users\judge\AppData\Local\Temp\tree.ply: raw private stderr"

    def fail_pipeline(*args, **kwargs):
        raise PipelineError(operator_detail=operator_detail)

    monkeypatch.setattr(upload_mod, "run_pipeline", fail_pipeline)
    with caplog.at_level(logging.ERROR, logger=upload_mod.__name__):
        response = await client.post(
            "/api/v1/upload/analyze",
            files={"file": ("tree.ply", MINIMAL_ASCII_PLY, "application/octet-stream")},
        )

    assert response.status_code == 502
    assert response.json() == {"detail": "Pipeline execution failed"}
    assert "raw private stderr" not in response.text
    assert r"C:\Users\judge" not in response.text
    assert r"C:\Users\judge\AppData\Local\Temp" not in caplog.text


def test_run_pipeline_strips_secrets_from_subprocess_env(tmp_path, monkeypatch):
    captured_env: dict[str, str] = {}
    monkeypatch.setenv("TREEQ_DEMO_TOKEN", "demo-secret")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-secret")

    def completed_run(cmd, **kwargs):
        captured_env.update(kwargs["env"])
        output_path = cmd[cmd.index("--output") + 1]
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write("{}")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("app.services.pipeline_runner.subprocess.run", completed_run)
    result = run_pipeline(tmp_path / "tree.ply")

    assert result == {}
    assert "TREEQ_DEMO_TOKEN" not in captured_env
    assert "SUPABASE_SERVICE_KEY" not in captured_env


def test_probe_pipeline_runtime_returns_version_and_strips_secrets(monkeypatch):
    captured_env: dict[str, str] = {}
    monkeypatch.setenv("TREEQ_DEMO_TOKEN", "demo-secret")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-secret")

    def completed_run(cmd, **kwargs):
        captured_env.update(kwargs["env"])
        return subprocess.CompletedProcess(cmd, 0, stdout="0.3.0\n", stderr="")

    monkeypatch.setattr("app.services.pipeline_runner.subprocess.run", completed_run)
    assert probe_pipeline_runtime(timeout=7) == "0.3.0"
    assert "TREEQ_DEMO_TOKEN" not in captured_env
    assert "SUPABASE_SERVICE_KEY" not in captured_env
