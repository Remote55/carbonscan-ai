"""Unit tests for the shared upload validation helper."""

from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from app.services.upload_validation import (
    ANALYZE_EXTENSIONS,
    read_upload_limited,
    validate_ply_vertex_count,
    validate_upload,
)


def test_accepts_known_extension_and_returns_ext():
    assert validate_upload("plot.LAS", b"some-bytes") == ".las"


def test_demo_mode_rejects_non_ply_upload(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "TREEQ_DEMO_MODE", True)
    with pytest.raises(HTTPException) as exc:
        validate_upload("plot.las", b"some-bytes")
    assert exc.value.status_code == 400
    assert exc.value.detail == "Demo uploads must be PLY"


def test_rejects_unknown_extension():
    with pytest.raises(HTTPException) as exc:
        validate_upload("photo.jpg", b"x")
    assert exc.value.status_code == 400


def test_rejects_empty_file():
    with pytest.raises(HTTPException) as exc:
        validate_upload("plot.las", b"")
    assert exc.value.status_code == 400


def test_rejects_oversize_file(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)
    with pytest.raises(HTTPException) as exc:
        validate_upload("plot.las", b"too-big")
    assert exc.value.status_code == 413


def test_all_known_extensions_present():
    assert ANALYZE_EXTENSIONS == {".las", ".laz", ".ply", ".txt", ".xyz", ".csv"}


def test_demo_ply_rejects_bad_signature():
    with pytest.raises(HTTPException) as exc:
        validate_ply_vertex_count(b"not-ply\nformat ascii 1.0\nend_header\n", max_points=2_000_000)
    assert exc.value.status_code == 400


def test_demo_ply_rejects_missing_end_header():
    data = b"ply\nformat ascii 1.0\nelement vertex 1\n"
    with pytest.raises(HTTPException) as exc:
        validate_ply_vertex_count(data, max_points=2_000_000)
    assert exc.value.status_code == 400


def test_demo_ply_rejects_vertex_count_above_limit():
    data = b"ply\nformat ascii 1.0\nelement vertex 2000001\nend_header\n"
    with pytest.raises(HTTPException) as exc:
        validate_ply_vertex_count(data, max_points=2_000_000)
    assert exc.value.status_code == 413


def test_demo_ply_reads_only_ascii_header_for_binary_body():
    data = (
        b"ply\nformat binary_little_endian 1.0\nelement vertex 1\nend_header\n"
        b"\xff\x00\x80"
    )
    assert validate_ply_vertex_count(data, max_points=2_000_000) == 1


@pytest.mark.asyncio
async def test_bounded_reader_rejects_stream_above_limit():
    upload = UploadFile(filename="tree.ply", file=BytesIO(b"12345"))
    with pytest.raises(HTTPException) as exc:
        await read_upload_limited(upload, max_bytes=4)
    assert exc.value.status_code == 413
    assert exc.value.detail == "File too large"
