"""Serving the segmented cloud, and keeping it behind the same door as the data.

The id in an analysis response is a handle to the classified point cloud those
numbers were measured from. Anyone holding it can download the shape of a
surveyed plot, so it must not be reachable with less proof than the analysis
itself required.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core import demo_security
from app.services import segmented_cloud_store

PLY = b"ply\nformat binary_little_endian 1.0\nelement vertex 0\nend_header\n"


@pytest.fixture
def stored_cloud() -> str:
    return segmented_cloud_store.store.put(PLY)


async def test_returns_the_stored_bytes(client: AsyncClient, stored_cloud: str) -> None:
    response = await client.get(f"/api/v1/upload/segmented/{stored_cloud}")

    assert response.status_code == 200
    assert response.content == PLY
    assert response.headers["content-type"] == "application/octet-stream"


async def test_unknown_and_malformed_ids_both_read_as_404(client: AsyncClient) -> None:
    """One answer for both: the caller learns nothing about the store."""
    for candidate in [
        "PGVsqZ3fXn8sQ2mKdT4bWc9y",  # id-shaped but never stored
        "short",
    ]:
        response = await client.get(f"/api/v1/upload/segmented/{candidate}")
        assert response.status_code == 404, candidate


def test_sits_behind_the_demo_token() -> None:
    """The download needs the demo token, exactly as /analyze does."""
    assert demo_security.is_protected_path("/api/v1/upload/segmented/anything")
    assert demo_security.is_protected_path("/api/v1/upload/analyze")
    # Unrelated paths stay open, or the guard would lock the whole API.
    assert not demo_security.is_protected_path("/api/v1/health/live")
    assert not demo_security.is_protected_path("/api/v1/upload/segmented")


def test_protection_is_not_a_prefix_accident() -> None:
    """`/upload/segmentedX/id` must not inherit protection from a loose prefix."""
    assert not demo_security.is_protected_path("/api/v1/upload/segmentedX/id")
