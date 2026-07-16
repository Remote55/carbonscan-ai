"""Unit tests for the shared upload validation helper."""

import pytest
from fastapi import HTTPException

from app.services.upload_validation import ANALYZE_EXTENSIONS, validate_upload


def test_accepts_known_extension_and_returns_ext():
    assert validate_upload("plot.LAS", b"some-bytes") == ".las"


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
