"""How many analyses this process will run at once.

`/upload/analyze` is unauthenticated and hands its work to
`run_in_threadpool`, whose default pool is 40 threads. Each of those runs a
subprocess that loads numpy, open3d and a point cloud, so forty concurrent
requests are forty interpreters competing for the box's memory. Nothing capped
that: the rate limit answers "how often may one caller ask", which is a
different question from "how much work may be in flight at once", and it is
keyed per client, so it never bounded the total either.

The cap is a semaphore rather than a queue. A caller that cannot be served now
is told so immediately with 503 and a Retry-After, because the alternative is
holding a request open behind a multi-minute subprocess until something in the
chain times out and the caller learns nothing.

Sized for the smallest host this is meant to run on. One analysis peaks at
roughly the upload size in RAM plus the subprocess's own working set, and the
free tiers named in docs/DEPLOY_PUBLIC.md start around 512 MB.
"""

from __future__ import annotations

import threading

from app.core.config import settings


class AnalysisSlots:
    """Non-blocking permits for concurrent pipeline runs."""

    def __init__(self, limit: int) -> None:
        self._limit = max(1, int(limit))
        self._semaphore = threading.BoundedSemaphore(self._limit)
        self._lock = threading.Lock()
        self._in_flight = 0

    @property
    def limit(self) -> int:
        return self._limit

    @property
    def in_flight(self) -> int:
        with self._lock:
            return self._in_flight

    def try_acquire(self) -> bool:
        """Take a slot if one is free. Never waits."""
        if not self._semaphore.acquire(blocking=False):
            return False
        with self._lock:
            self._in_flight += 1
        return True

    def release(self) -> None:
        with self._lock:
            # Guard against a double release turning into extra capacity:
            # BoundedSemaphore raises on over-release, and losing the count here
            # would silently raise the cap for the life of the process.
            if self._in_flight == 0:
                raise RuntimeError("released an analysis slot that was not held")
            self._in_flight -= 1
        self._semaphore.release()


slots = AnalysisSlots(settings.MAX_CONCURRENT_ANALYSES)
