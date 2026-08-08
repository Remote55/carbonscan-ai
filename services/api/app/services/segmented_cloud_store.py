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
        self._root = Path(root) if root else Path(tempfile.mkdtemp(prefix="treeq_segmented_"))
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
        """Reserve an id and path for the pipeline to write to directly.

        Saves reading a multi-megabyte file into memory only to write it back
        out. The caller must call `commit` once the file exists.
        """
        cloud_id = secrets.token_urlsafe(24)
        return cloud_id, self._root / f"{cloud_id}.ply"

    def commit(self, cloud_id: str, path: Path) -> str | None:
        """Register a reserved id, or return None if the file was never written."""
        if not path.exists() or path.stat().st_size == 0:
            return None
        with self._lock:
            self._entries[cloud_id] = _Entry(path=path, created_at=self._now())
            self._evict_locked()
        return cloud_id

    def get(self, cloud_id: str) -> bytes | None:
        """Return the stored PLY, or None if unknown, expired or malformed."""
        if not _ID_PATTERN.match(cloud_id or ""):
            return None
        with self._lock:
            self._evict_locked()
            entry = self._entries.get(cloud_id)
            if entry is None:
                return None
            path = entry.path
        try:
            return path.read_bytes()
        except OSError:
            with self._lock:
                self._entries.pop(cloud_id, None)
            return None

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
