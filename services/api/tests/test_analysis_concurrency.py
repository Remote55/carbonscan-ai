"""The two things that stood between a public URL and a dead instance.

Neither existed. `/upload/analyze` is unauthenticated and hands its work to
run_in_threadpool, whose default pool is 40 threads, and nothing capped how
many pipeline subprocesses could be resident at once. The rate limit, which was
the only other guard, keyed on the socket peer — behind any proxy that is one
address for every caller in the world.
"""

from __future__ import annotations

import threading

import pytest
from fastapi.testclient import TestClient

from app.core import demo_security
from app.core.demo_security import DemoGuardMiddleware, client_key
from app.main import app
from app.services.analysis_slots import AnalysisSlots

ANALYZE = "/api/v1/upload/analyze"
PLY = (
    b"ply\nformat ascii 1.0\nelement vertex 1\n"
    b"property float x\nproperty float y\nproperty float z\n"
    b"end_header\n0 0 0\n"
)


def _scope(peer: str = "10.0.0.1", headers: list[tuple[bytes, bytes]] | None = None) -> dict:
    return {"client": (peer, 1234), "headers": headers or []}


class TestTheSlotCap:
    def test_a_free_slot_is_taken_and_given_back(self):
        slots = AnalysisSlots(1)
        assert slots.try_acquire()
        assert slots.in_flight == 1
        slots.release()
        assert slots.in_flight == 0
        assert slots.try_acquire()

    def test_the_cap_is_the_cap(self):
        slots = AnalysisSlots(2)
        assert slots.try_acquire()
        assert slots.try_acquire()
        assert not slots.try_acquire(), "a third analysis started with a cap of two"

    def test_refusal_is_immediate_rather_than_a_wait(self):
        """The property that makes 503 the right answer. If try_acquire blocked,
        a caller would sit behind a multi-minute subprocess learning nothing."""
        slots = AnalysisSlots(1)
        slots.try_acquire()
        done = threading.Event()

        def attempt() -> None:
            slots.try_acquire()
            done.set()

        threading.Thread(target=attempt, daemon=True).start()
        assert done.wait(timeout=2.0), "try_acquire blocked instead of refusing"

    def test_releasing_a_slot_nobody_held_is_an_error(self):
        """Silently absorbing it would raise the cap for the life of the
        process, which is worse than the crash it is hiding."""
        slots = AnalysisSlots(1)
        with pytest.raises(RuntimeError):
            slots.release()

    def test_a_slot_survives_concurrent_pressure(self):
        slots = AnalysisSlots(3)
        taken: list[bool] = []
        lock = threading.Lock()

        def worker() -> None:
            got = slots.try_acquire()
            with lock:
                taken.append(got)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert sum(taken) == 3, f"cap of 3 handed out {sum(taken)} slots"


class TestTheRouteRefusesWhenFull:
    def test_analyze_returns_503_with_retry_after_when_no_slot_is_free(self, monkeypatch):
        from app.services import analysis_slots

        exhausted = AnalysisSlots(1)
        assert exhausted.try_acquire()
        monkeypatch.setattr(analysis_slots, "slots", exhausted)

        with TestClient(app) as client:
            response = client.post(ANALYZE, files={"file": ("plot.ply", PLY, "text/plain")})

        assert response.status_code == 503
        assert response.headers.get("Retry-After") == "30"

    def test_the_slot_is_returned_when_the_pipeline_fails(self, monkeypatch):
        """A leaked slot is permanent: the cap drops by one for the life of the
        process, and enough failures take the route to a standing 503."""
        from app.api.v1 import upload
        from app.services import analysis_slots
        from app.services.pipeline_runner import PipelineError

        fresh = AnalysisSlots(1)
        monkeypatch.setattr(analysis_slots, "slots", fresh)

        def boom(*_args, **_kwargs):
            raise PipelineError(public_message="nope", operator_detail="nope")

        monkeypatch.setattr(upload, "_run_pipeline_on_bytes", boom)

        with TestClient(app) as client:
            first = client.post(ANALYZE, files={"file": ("plot.ply", PLY, "text/plain")})

        assert first.status_code == 502
        assert fresh.in_flight == 0, "the failed run kept its slot"
        assert fresh.try_acquire(), "the route is now permanently one slot poorer"


class TestWhoTheRateLimitCounts:
    def test_without_a_proxy_the_socket_peer_is_the_client(self):
        assert client_key(_scope("203.0.113.9")) == "203.0.113.9"

    def test_a_forged_header_is_ignored_when_no_proxy_is_declared(self, monkeypatch):
        """Honouring it unconditionally would let one caller mint a new identity
        per request and have no limit at all."""
        monkeypatch.setattr(demo_security.settings, "TRUST_PROXY_HEADERS", False)
        scope = _scope("203.0.113.9", [(b"x-forwarded-for", b"1.2.3.4")])
        assert client_key(scope) == "203.0.113.9"

    def test_behind_a_declared_proxy_the_original_client_is_used(self, monkeypatch):
        """Without this every caller shares the proxy's address, so the limit
        applies to the whole world at once instead of to each caller."""
        monkeypatch.setattr(demo_security.settings, "TRUST_PROXY_HEADERS", True)
        scope = _scope("10.0.0.1", [(b"x-forwarded-for", b"198.51.100.7, 10.0.0.1")])
        assert client_key(scope) == "198.51.100.7"

    def test_two_callers_behind_one_proxy_get_separate_budgets(self, monkeypatch):
        monkeypatch.setattr(demo_security.settings, "TRUST_PROXY_HEADERS", True)
        monkeypatch.setattr(demo_security.settings, "RATE_LIMIT_UPLOAD", 1)
        guard = DemoGuardMiddleware(app)

        first = client_key(_scope("10.0.0.1", [(b"x-forwarded-for", b"198.51.100.7")]))
        second = client_key(_scope("10.0.0.1", [(b"x-forwarded-for", b"198.51.100.8")]))

        assert guard._allow_upload(first)
        assert not guard._allow_upload(first), "the same caller was not limited"
        assert guard._allow_upload(second), "a different caller inherited the limit"

    def test_an_empty_forwarded_header_falls_back_to_the_peer(self, monkeypatch):
        monkeypatch.setattr(demo_security.settings, "TRUST_PROXY_HEADERS", True)
        scope = _scope("10.0.0.1", [(b"x-forwarded-for", b"  ")])
        assert client_key(scope) == "10.0.0.1"

    def test_the_client_table_does_not_grow_without_bound(self, monkeypatch):
        """One entry per address seen, never pruned, is a slow leak on a public
        URL — a client's entry was only cleaned up when that client returned."""
        monkeypatch.setattr(demo_security.settings, "RATE_LIMIT_UPLOAD", 5)
        guard = DemoGuardMiddleware(app)
        monkeypatch.setattr(guard, "MAX_TRACKED_CLIENTS", 16)

        for index in range(200):
            guard._allow_upload(f"198.51.100.{index}")

        assert len(guard._upload_attempts) <= 16, (
            f"tracking {len(guard._upload_attempts)} clients with a cap of 16"
        )
