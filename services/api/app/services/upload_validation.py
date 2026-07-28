"""Shared validation for point-cloud uploads (used by /upload and /jobs)."""

import os

from fastapi import HTTPException, UploadFile

from app.core.config import settings

# Formats the ML pipeline can load (pipeline.field_eval.load_point_cloud)
ANALYZE_EXTENSIONS = {".las", ".laz", ".ply", ".txt", ".xyz", ".csv"}


async def read_upload_limited(file: UploadFile, max_bytes: int) -> bytes:
    """Read an upload in bounded chunks and stop as soon as it exceeds the limit."""
    chunks: list[bytes] = []
    size = 0
    while chunk := await file.read(1024 * 1024):
        size += len(chunk)
        if size > max_bytes:
            raise HTTPException(status_code=413, detail="File too large")
        chunks.append(chunk)
    return b"".join(chunks)


def validate_demo_ply(data: bytes, max_points: int) -> int:
    """Validate a PLY header without decoding a possible binary body."""
    header_lines: list[str] = []
    offset = 0
    found_end = False
    while offset < len(data):
        newline = data.find(b"\n", offset)
        line_end = len(data) if newline == -1 else newline
        raw_line = data[offset:line_end].removesuffix(b"\r")
        try:
            line = raw_line.decode("ascii")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid PLY header") from exc
        header_lines.append(line)
        if line == "end_header":
            found_end = True
            break
        if newline == -1:
            break
        offset = newline + 1

    if not found_end or not header_lines or header_lines[0] != "ply":
        raise HTTPException(status_code=400, detail="Invalid PLY header")

    formats = [line for line in header_lines if line.startswith("format ")]
    if len(formats) != 1 or formats[0] not in {
        "format ascii 1.0",
        "format binary_little_endian 1.0",
    }:
        raise HTTPException(status_code=400, detail="Unsupported PLY format")

    vertex_counts: list[int] = []
    for line in header_lines:
        parts = line.split()
        if len(parts) == 3 and parts[:2] == ["element", "vertex"]:
            if not parts[2].isdigit():
                raise HTTPException(status_code=400, detail="Invalid PLY vertex count")
            vertex_counts.append(int(parts[2]))
    if len(vertex_counts) != 1:
        raise HTTPException(status_code=400, detail="Invalid PLY vertex count")

    vertex_count = vertex_counts[0]
    if vertex_count > max_points:
        raise HTTPException(status_code=413, detail="Too many points")
    return vertex_count


def validate_upload(filename: str | None, data: bytes) -> str:
    """Validate a point-cloud upload; return its lowercased extension.

    Raises HTTPException (400/413) on bad extension, empty, or oversize input.
    """
    ext = os.path.splitext((filename or "").lower())[1]
    if ext not in ANALYZE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ANALYZE_EXTENSIONS)}",
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    max_size_bytes = (
        settings.TREEQ_DEMO_MAX_UPLOAD_SIZE_BYTES
        if settings.TREEQ_DEMO_MODE
        else settings.MAX_UPLOAD_SIZE_BYTES
    )
    max_size_mb = (
        settings.TREEQ_DEMO_MAX_UPLOAD_SIZE_MB
        if settings.TREEQ_DEMO_MODE
        else settings.MAX_UPLOAD_SIZE_MB
    )
    if len(data) > max_size_bytes:
        raise HTTPException(
            status_code=413, detail=f"File too large (> {max_size_mb} MB)"
        )
    if settings.TREEQ_DEMO_MODE and ext == ".ply":
        validate_demo_ply(data, settings.TREEQ_DEMO_MAX_POINTS)
    return ext
