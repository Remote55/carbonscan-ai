"""Test health endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "CarbonScan AI API"
    assert "version" in data


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


@pytest.mark.asyncio
async def test_v1_health(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_demo_ready_requires_demo_token(client: AsyncClient, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
    monkeypatch.setattr(settings, "TREEQ_DEMO_TOKEN", "d" * 64)
    response = await client.get(
        "/api/v1/health/demo-ready",
        headers={"X-TreeQ-Demo-Challenge": "e" * 64},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}
