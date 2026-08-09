"""Uploads for async jobs have to leave again.

save_job_input wrote a file per submission and nothing ever removed one, so an
instance accumulated every point cloud ever submitted until the disk filled.
Two exits now: the worker deletes what it finished with, and abandoned uploads
age out.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from app.services import job_input
from app.services.job_input import (
    discard_job_input,
    job_upload_dir,
    save_job_input,
    sweep_orphans,
)


@pytest.fixture
def upload_dir(tmp_path, monkeypatch) -> Path:
    from app.core.config import settings

    monkeypatch.setattr(settings, "JOB_UPLOAD_DIR", str(tmp_path / "jobs"))
    return job_upload_dir()


class TestDiscard:
    def test_removes_the_file(self, upload_dir):
        path = save_job_input(b"cloud", ".ply")
        assert Path(path).exists()
        discard_job_input(path)
        assert not Path(path).exists()

    def test_is_safe_to_call_twice(self, upload_dir):
        path = save_job_input(b"cloud", ".ply")
        discard_job_input(path)
        discard_job_input(path)

    def test_refuses_a_path_outside_the_upload_dir(self, upload_dir, tmp_path):
        """input_url is a database column. A delete driven by stored data must
        not reach arbitrary paths if the row is ever wrong."""
        outsider = tmp_path / "important.txt"
        outsider.write_text("do not delete", encoding="utf-8")
        discard_job_input(outsider)
        assert outsider.exists()

    def test_refuses_a_traversal_out_of_the_upload_dir(self, upload_dir, tmp_path):
        outsider = tmp_path / "escape.txt"
        outsider.write_text("do not delete", encoding="utf-8")
        discard_job_input(upload_dir / ".." / "escape.txt")
        assert outsider.exists()


class TestSweep:
    def test_leaves_recent_uploads_alone(self, upload_dir):
        path = save_job_input(b"cloud", ".ply")
        assert sweep_orphans() == 0
        assert Path(path).exists()

    def test_removes_an_abandoned_upload(self, upload_dir):
        path = Path(save_job_input(b"cloud", ".ply"))
        old = time.time() - (job_input.ORPHAN_TTL_SECONDS + 60)
        os.utime(path, (old, old))
        assert sweep_orphans() == 1
        assert not path.exists()

    def test_saving_sweeps_without_anyone_scheduling_it(self, upload_dir):
        """No cron to deploy and none to forget to start."""
        stale = Path(save_job_input(b"old", ".ply"))
        old = time.time() - (job_input.ORPHAN_TTL_SECONDS + 60)
        os.utime(stale, (old, old))

        fresh = Path(save_job_input(b"new", ".ply"))

        assert not stale.exists()
        assert fresh.exists()

    def test_a_locked_or_vanished_file_does_not_fail_the_upload(self, upload_dir, monkeypatch):
        stale = Path(save_job_input(b"old", ".ply"))
        old = time.time() - (job_input.ORPHAN_TTL_SECONDS + 60)
        os.utime(stale, (old, old))

        def refuse(*_args, **_kwargs):
            raise OSError("in use by another process")

        monkeypatch.setattr(Path, "unlink", refuse)
        assert sweep_orphans() == 0  # swallowed, not raised


@pytest.mark.asyncio
class TestWorkerCleansUp:
    async def _run(self, upload_dir, runner):
        from app.services.job_store import InMemoryJobStore
        from app.worker import process_one

        store = InMemoryJobStore()
        path = save_job_input(b"cloud", ".ply")
        await store.create(
            owner_id=__import__("uuid").uuid4(),
            owner_email="a@example.invalid",
            input_url=path,
        )
        await process_one(store, runner=runner)
        return Path(path)

    async def test_after_a_successful_job(self, upload_dir):
        path = await self._run(
            upload_dir,
            lambda _p: {"summary": {"total_trees": 1, "total_carbon_kg": 1.0}},
        )
        assert not path.exists()

    async def test_after_a_failed_job(self, upload_dir):
        """Nothing retries a failed job, so its upload has no reader either."""

        def explode(_path):
            raise RuntimeError("pipeline died")

        path = await self._run(upload_dir, explode)
        assert not path.exists()

    async def test_a_delete_failure_does_not_mark_a_good_job_failed(
        self, upload_dir, monkeypatch
    ):
        from app.services.job_store import InMemoryJobStore
        from app.worker import process_one

        store = InMemoryJobStore()
        path = save_job_input(b"cloud", ".ply")
        rec = await store.create(
            owner_id=__import__("uuid").uuid4(),
            owner_email="a@example.invalid",
            input_url=path,
        )
        monkeypatch.setattr(
            job_input,
            "discard_job_input",
            lambda _p: (_ for _ in ()).throw(OSError("locked")),
        )
        import app.worker as worker_module

        monkeypatch.setattr(
            worker_module,
            "discard_job_input",
            lambda _p: (_ for _ in ()).throw(OSError("locked")),
        )
        await process_one(
            store, runner=lambda _p: {"summary": {"total_trees": 1, "total_carbon_kg": 1.0}}
        )
        stored = await store.get(rec.id)
        assert stored is not None and stored.status == "completed"
