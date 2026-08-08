"""Security contract for the ephemeral judge-demo API surface."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.demo_security import (
    DemoGuardMiddleware,
    compute_readiness_hmac,
    token_matches,
)

MINIMAL_ASCII_PLY = b"""ply
format ascii 1.0
element vertex 1
property float x
property float y
property float z
end_header
0 0 0
"""


def test_token_comparison_is_constant_contract():
    assert token_matches("a" * 64, "a" * 64)
    assert not token_matches("a" * 64, "b" * 64)


@pytest.mark.parametrize(
    "invalid_token",
    ["aa" * 31, "g" * 64],
    ids=["under-256-bits", "non-hex"],
)
def test_token_comparison_rejects_weak_or_malformed_config(invalid_token):
    assert not token_matches(invalid_token, invalid_token)


@pytest.mark.parametrize(
    "provided",
    ["\xff" * 64, "ก" * 64, "café" + "a" * 60, ""],
    ids=["high-byte", "thai", "accented", "empty"],
)
def test_a_hostile_token_header_is_refused_rather_than_raising(provided):
    """The header is decoded latin-1, so any byte above 0x7f reaches this as a
    non-ASCII str. compare_digest raises TypeError on those, and the comparison
    used to run before the shape check — so a stranger could turn the pre-auth
    path into an unhandled 500, one traceback per request. Refusing is the only
    acceptable answer; crashing is not a decision."""
    assert token_matches("a" * 64, provided) is False


@pytest.mark.asyncio
async def test_a_hostile_token_header_gets_401_not_500(client, monkeypatch):
    """The same thing through the real middleware, which is where it bit."""
    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
    monkeypatch.setattr(settings, "TREEQ_DEMO_TOKEN", "a" * 64)

    # Raw bytes, because that is what an attacker puts on the wire and what
    # ASGI hands the middleware. httpx refuses to ascii-encode a str header,
    # which is client-side strictness the network does not share.
    response = await client.post(
        "/api/v1/upload/analyze",
        headers={b"x-treeq-demo-token": b"\xff" * 64},
        files={"file": ("plot.ply", b"ply\n", "application/octet-stream")},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_demo_guard_rejects_missing_token(client, monkeypatch):
    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
    monkeypatch.setattr(settings, "TREEQ_DEMO_TOKEN", "a" * 64)
    response = await client.post(
        "/api/v1/upload/analyze",
        files={"file": ("tree.ply", MINIMAL_ASCII_PLY, "application/octet-stream")},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
    assert "a" * 64 not in response.text


@pytest.mark.asyncio
async def test_demo_guard_does_not_protect_liveness(client, monkeypatch):
    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
    monkeypatch.setattr(settings, "TREEQ_DEMO_TOKEN", "a" * 64)
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_demo_ready_returns_hmac_only_after_auth(client, monkeypatch):
    import app.api.v1.health as health_mod

    token = "a" * 64
    nonce = "b" * 64
    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
    monkeypatch.setattr(settings, "TREEQ_DEMO_TOKEN", token)
    monkeypatch.setattr(health_mod, "probe_pipeline_runtime", lambda timeout=30: "0.3.0")
    response = await client.get(
        "/api/v1/health/demo-ready",
        headers={
            "X-TreeQ-Demo-Token": token,
            "X-TreeQ-Demo-Challenge": nonce,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "mode": "demo",
        "pipeline_version": "0.3.0",
        "challenge_hmac": "fa08c4525e4bf45cabec6ee274f10d2cd39036dd2ef57499d8a0c7a53a7be3ce",
    }
    assert response.json()["challenge_hmac"] == compute_readiness_hmac(token, nonce)
    assert token not in response.text


@pytest.mark.asyncio
async def test_demo_guard_rate_limits_authenticated_uploads_per_client(monkeypatch):
    token = "c" * 64
    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
    monkeypatch.setattr(settings, "TREEQ_DEMO_TOKEN", token)
    monkeypatch.setattr(settings, "RATE_LIMIT_UPLOAD", 1)

    isolated_app = FastAPI()
    isolated_app.add_middleware(DemoGuardMiddleware)

    @isolated_app.post("/api/v1/upload/analyze")
    async def accepted_upload():
        return {"accepted": True}

    transport = ASGITransport(app=isolated_app)
    async with AsyncClient(transport=transport, base_url="http://test") as isolated_client:
        headers = {"X-TreeQ-Demo-Token": token}
        first = await isolated_client.post("/api/v1/upload/analyze", headers=headers)
        limited = await isolated_client.post("/api/v1/upload/analyze", headers=headers)

    assert first.status_code == 200
    assert limited.status_code == 429
    assert limited.json() == {"detail": "Too many requests"}
    assert token not in limited.text
