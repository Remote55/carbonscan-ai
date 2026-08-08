"""Short-lived storage for the segmented point cloud an analysis produced.

The pipeline can write a plot-wide PLY carrying the wood/leaf/ground label of
every point - the same labels the DBH, volume and carbon figures were taken
from. The viewer needs that file to show the separation it computed; without it
the browser keeps displaying the raw cloud it parsed on upload, and pressing
"analyse" appears to do nothing to the picture.

It is handed over as an id plus a fetch, not inline in the response. Two reasons:
the async job record is polled repeatedly and re-sending megabytes of base64 on
every poll would be wasteful, and an id is the shape that survives being moved
to object storage when the API gets a permanent home.

Deliberately in-process and deliberately temporary. Nothing here is durable
state: a restart drops everything, and that is correct, because a cloud whose
analysis result the caller no longer holds is of no use to anyone.
"""

from __future__ import annotations

import os
import re
import secrets
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path

# ids are generated here and only ever compared against this shape, so a
# traversal attempt ("../../etc/passwd") can never reach the filesystem.
_ID_PATTERN = re.compile(r"\A[A-Za-z0-9_-]{16,64}\Z")

DEFAULT_TTL_SECONDS = 30 * 60
DEFAULT_MAX_ENTRIES = 32


@dataclass
class _Entry:
    path: Path
    created_at: float


class SegmentedCloudStore:
    """Keeps recently produced segmented clouds until they expire.

    Thread-safe: FastAPI runs the pipeline in a threadpool, so puts can overlap
    with a browser fetching an earlier one.
    """

    def __init__(
        self,
        *,
        root: Path | None = None,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        clock: object = time.monotonic,
    ) -> None:
        # A stable directory, not mkdtemp. uvicorn runs several workers - the
        # repo's own Dockerfile asks for two - and a random per-process root
        # meant the worker that answered the download was usually not the one
        # that wrote the file. The browser then got a 404 saying "expired",
        # which points at the TTL and not at the real cause.
        self._root = Path(root) if root else Path(tempfile.gettempdir()) / "treeq-segmented"
        self._root.mkdir(parents=True, exist_ok=True)
        self._ttl = float(ttl_seconds)
        self._max_entries = int(max_entries)
        self._clock = clock
        self._entries: dict[str, _Entry] = {}
        self._lock = threading.Lock()

    @property
    def root(self) -> Path:
        return self._root

    def put(self, data: bytes) -> str:
        """Store a PLY and return its id."""
        cloud_id = secrets.token_urlsafe(24)
        path = self._root / f"{cloud_id}.ply"
        path.write_bytes(data)
        with self._lock:
            self._entries[cloud_id] = _Entry(path=path, created_at=self._now())
            self._evict_locked()
        return cloud_id

    def reserve(self) -> tuple[str, Path]:
        """Reserve an id and a scratch path for the pipeline to write to.

        Saves reading a multi-megabyte file into memory only to write it back
        out. The path ends in `.part`: `get` serves only the final name, so a
        download can never catch a file mid-write. The caller must call `commit`.
        """
        cloud_id = secrets.token_urlsafe(24)
        return cloud_id, self._root / f"{cloud_id}.ply.part"

    def commit(self, cloud_id: str, path: Path) -> str | None:
        """Publish a reserved id, or return None if the file was never written.

        The rename is atomic on the same filesystem, so the file appears under
        its final name complete or not at all - which is what lets `get` fall
        back to the filesystem safely from another worker.
        """
        if not path.exists() or path.stat().st_size == 0:
            path.unlink(missing_ok=True)
            return None
        final = self._root / f"{cloud_id}.ply"
        os.replace(path, final)
        with self._lock:
            self._entries[cloud_id] = _Entry(path=final, created_at=self._now())
            self._evict_locked()
        return cloud_id

    def get(self, cloud_id: str) -> bytes | None:
        """Return the stored PLY, or None if unknown, expired or malformed.

        Falls back to the filesystem when this process has no record of the id.
        Another worker in the same deployment may have written it, and the id is
        the filename, so the bytes are findable without shared memory. Expiry
        stays best-effort per process; a file whose owner has not yet evicted it
        is still served, which is the right trade for a caller holding a valid
        id. Sharing a filesystem is the assumption here - across hosts this
        needs object storage, and it will still answer 404 until it gets one.
        """
        if not _ID_PATTERN.match(cloud_id or ""):
            return None
        with self._lock:
            self._evict_locked()
            entry = self._entries.get(cloud_id)
            path = entry.path if entry else self._root / f"{cloud_id}.ply"
        try:
            data = path.read_bytes()
        except OSError:
            with self._lock:
                self._entries.pop(cloud_id, None)
            return None
        # Zero bytes is not a cloud. commit() never publishes an empty file, so
        # this only catches something that went wrong outside the store.
        return data or None

    def _now(self) -> float:
        clock = self._clock
        return float(clock())  # type: ignore[operator]

    def _evict_locked(self) -> None:
        """Drop expired entries, then the oldest ones over the cap."""
        now = self._now()
        for cloud_id, entry in list(self._entries.items()):
            if now - entry.created_at >= self._ttl:
                self._discard_locked(cloud_id, entry)

        overflow = len(self._entries) - self._max_entries
        if overflow > 0:
            oldest = sorted(self._entries.items(), key=lambda kv: kv[1].created_at)
            for cloud_id, entry in oldest[:overflow]:
                self._discard_locked(cloud_id, entry)

    def _discard_locked(self, cloud_id: str, entry: _Entry) -> None:
        self._entries.pop(cloud_id, None)
        entry.path.unlink(missing_ok=True)


# One store per process. The analyse endpoint writes into it and the download
# endpoint reads from it; both live in the same worker.
store = SegmentedCloudStore()
