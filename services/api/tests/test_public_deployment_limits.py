"""The limits that apply when demo mode is off.

Every test in test_demo_security.py sets TREEQ_DEMO_MODE True. That is the
ephemeral tunnel handed to a known audience. The configuration a public
deployment actually runs is demo mode OFF, and it was the one with no rate
limit, no vertex cap, and a 500 MB file ceiling on an unauthenticated route
that runs a multi-minute subprocess.

Nothing failed when those three were made unconditional, because nothing tested
this configuration. So these tests exist to fail if the caps are ever put back
behind a mode flag.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.demo_security import DemoGuardMiddleware
from app.services.upload_validation import validate_upload


def _ply(vertex_count: int) -> bytes:
    header = (
        "ply\n"
        "format ascii 1.0\n"
        f"element vertex {vertex_count}\n"
        "property float x\n"
        "property float y\n"
        "property float z\n"
        "end_header\n"
    ).encode("ascii")
    return header + b"0 0 0\n"


@pytest.mark.asyncio
async def test_upload_is_rate_limited_with_demo_mode_off(monkeypatch):
    """The limit protects the instance, not the token. Turning off the token
    check used to turn off the limit with it."""
    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", False)
    monkeypatch.setattr(settings, "RATE_LIMIT_UPLOAD", 1)

    app = FastAPI()
    app.add_middleware(DemoGuardMiddleware)

    @app.post("/api/v1/upload/analyze")
    async def accepted_upload():
        return {"accepted": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/api/v1/upload/analyze")
        second = await client.post("/api/v1/upload/analyze")

    assert first.status_code == 200
    assert second.status_code == 429, "an anonymous caller can queue work without limit"


@pytest.mark.asyncio
async def test_no_token_is_required_with_demo_mode_off(monkeypatch):
    """The counterpart. Demo mode off means open, deliberately — the fix above
    must not have quietly turned the token into a permanent requirement."""
    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", False)
    monkeypatch.setattr(settings, "RATE_LIMIT_UPLOAD", 10)

    app = FastAPI()
    app.add_middleware(DemoGuardMiddleware)

    @app.post("/api/v1/upload/analyze")
    async def accepted_upload():
        return {"accepted": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/upload/analyze")

    assert response.status_code == 200


class TestVertexCap:
    def test_applies_with_demo_mode_off(self, monkeypatch):
        monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", False)
        monkeypatch.setattr(settings, "TREEQ_DEMO_MAX_POINTS", 10)
        with pytest.raises(Exception) as exc:
            validate_upload("cloud.ply", _ply(5_000_000))
        assert getattr(exc.value, "status_code", None) == 413

    def test_still_accepts_a_cloud_under_the_cap(self, monkeypatch):
        monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", False)
        monkeypatch.setattr(settings, "TREEQ_DEMO_MAX_POINTS", 10)
        assert validate_upload("cloud.ply", _ply(1)) == ".ply"


class TestSizeCap:
    def test_demo_mode_off_does_not_raise_the_ceiling(self, monkeypatch):
        """500 MB was the general limit and 100 MB the demo one, so turning demo
        mode off multiplied the accepted payload by five on the route least able
        to survive it. The smaller of the two now wins in both modes."""
        monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", False)
        monkeypatch.setattr(settings, "TREEQ_DEMO_MAX_UPLOAD_SIZE_MB", 1)
        monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 500)

        oversized = b"x" * (2 * 1024 * 1024)
        with pytest.raises(Exception) as exc:
            validate_upload("cloud.ply", oversized)
        assert getattr(exc.value, "status_code", None) == 413

    def test_a_lower_general_limit_is_respected_too(self, monkeypatch):
        """min() in both directions — neither setting may override the other."""
        monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
        monkeypatch.setattr(settings, "TREEQ_DEMO_MAX_UPLOAD_SIZE_MB", 500)
        monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)

        oversized = b"x" * (2 * 1024 * 1024)
        with pytest.raises(Exception) as exc:
            validate_upload("cloud.ply", oversized)
        assert getattr(exc.value, "status_code", None) == 413
