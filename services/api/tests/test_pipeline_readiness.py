"""/health/pipeline — the probe that answers the question /health cannot.

The API image shipped for months without the ML pipeline in it. It started,
answered /health with {"status": "ok"}, and failed every analysis. The only
endpoint that checked otherwise was /health/demo-ready, which is gated behind
demo mode — off in any public deployment. So the one question worth asking about
a fresh deployment had no way to be asked.
"""

from __future__ import annotations

import pytest

from app.api.v1 import health as health_module
from app.services.pipeline_runner import PipelineError


@pytest.fixture(autouse=True)
def clear_probe_cache():
    health_module._pipeline_probe = None
    yield
    health_module._pipeline_probe = None


@pytest.mark.asyncio
async def test_reports_the_pipeline_version_when_the_runtime_is_reachable(client, monkeypatch):
    monkeypatch.setattr(health_module, "probe_pipeline_runtime", lambda: "0.4.0")

    response = await client.get("/api/v1/health/pipeline")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "pipeline_version": "0.4.0",
        "cached": "false",
    }


@pytest.mark.asyncio
async def test_503s_when_the_pipeline_is_missing_from_the_image(client, monkeypatch):
    def missing():
        raise PipelineError(operator_detail="No module named 'pipeline' at /app/services/ml")

    monkeypatch.setattr(health_module, "probe_pipeline_runtime", missing)

    response = await client.get("/api/v1/health/pipeline")

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_the_failure_does_not_leak_operator_detail(client, monkeypatch):
    def missing():
        raise PipelineError(
            operator_detail="Traceback: /home/someone/secret/path/pipeline/main.py"
        )

    monkeypatch.setattr(health_module, "probe_pipeline_runtime", missing)

    response = await client.get("/api/v1/health/pipeline")

    assert "secret" not in response.text
    assert "Traceback" not in response.text


@pytest.mark.asyncio
async def test_needs_no_token_and_works_with_demo_mode_off(client, monkeypatch):
    """A readiness probe nobody can reach is not a readiness probe."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", False)
    monkeypatch.setattr(health_module, "probe_pipeline_runtime", lambda: "0.4.0")

    response = await client.get("/api/v1/health/pipeline")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_a_success_is_cached_so_the_endpoint_is_not_a_subprocess_gun(
    client, monkeypatch
):
    calls: list[int] = []

    def probe():
        calls.append(1)
        return "0.4.0"

    monkeypatch.setattr(health_module, "probe_pipeline_runtime", probe)

    first = await client.get("/api/v1/health/pipeline")
    second = await client.get("/api/v1/health/pipeline")

    assert len(calls) == 1, "each call started a Python subprocess"
    assert first.json()["cached"] == "false"
    assert second.json()["cached"] == "true"


@pytest.mark.asyncio
async def test_a_failure_is_not_cached(client, monkeypatch):
    """A container recovering from a bad mount should say so on the next call,
    not in ten minutes."""
    calls: list[int] = []
    outcomes = iter([PipelineError(operator_detail="boom"), None])

    def probe():
        calls.append(1)
        outcome = next(outcomes)
        if outcome is not None:
            raise outcome
        return "0.4.0"

    monkeypatch.setattr(health_module, "probe_pipeline_runtime", probe)

    assert (await client.get("/api/v1/health/pipeline")).status_code == 503

    recovered = await client.get("/api/v1/health/pipeline")
    assert recovered.status_code == 200
    # Status alone is not enough: a cached failure would answer 200 from the
    # cache too, with whatever placeholder it stored. The probe has to run.
    assert len(calls) == 2, "the second call was served from a cached failure"
    assert recovered.json() == {
        "status": "ok",
        "pipeline_version": "0.4.0",
        "cached": "false",
    }
