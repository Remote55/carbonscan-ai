"""The store hands back exactly what was put in, and forgets on schedule."""

from __future__ import annotations

from pathlib import Path

from app.services.segmented_cloud_store import SegmentedCloudStore


class FakeClock:
    """A clock the test moves by hand, so expiry needs no sleeping."""

    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def _store(tmp_path: Path, **kwargs) -> tuple[SegmentedCloudStore, FakeClock]:
    clock = FakeClock()
    return SegmentedCloudStore(root=tmp_path, clock=clock, **kwargs), clock


def test_round_trips_bytes_unchanged(tmp_path: Path) -> None:
    store, _clock = _store(tmp_path)
    payload = b"ply\nformat binary_little_endian 1.0\n" + bytes(range(256))

    cloud_id = store.put(payload)

    assert store.get(cloud_id) == payload


def test_unknown_id_is_none_rather_than_an_error(tmp_path: Path) -> None:
    store, _clock = _store(tmp_path)

    assert store.get("PGVsqZ3fXn8sQ2mKdT4bWc9y") is None


def test_refuses_ids_that_are_not_ids(tmp_path: Path) -> None:
    """Path traversal cannot reach the filesystem: the shape is checked first."""
    store, _clock = _store(tmp_path)
    store.put(b"real content")

    for hostile in [
        "../../../../etc/passwd",
        "..\\..\\windows\\system32",
        "/absolute/path",
        "has spaces",
        "short",
        "",
        "a" * 200,
    ]:
        assert store.get(hostile) is None


def test_forgets_after_the_ttl_and_deletes_the_file(tmp_path: Path) -> None:
    store, clock = _store(tmp_path, ttl_seconds=600)
    cloud_id = store.put(b"expires")
    on_disk = next(tmp_path.glob("*.ply"))

    clock.advance(599)
    assert store.get(cloud_id) == b"expires"

    clock.advance(2)
    assert store.get(cloud_id) is None
    assert not on_disk.exists(), "an expired cloud must not be left on disk"


def test_keeps_only_the_newest_entries_up_to_the_cap(tmp_path: Path) -> None:
    store, clock = _store(tmp_path, max_entries=3)

    ids = []
    for index in range(5):
        ids.append(store.put(f"cloud {index}".encode()))
        clock.advance(1)

    # The two oldest are gone, the three newest survive.
    assert [store.get(i) for i in ids[:2]] == [None, None]
    assert [store.get(i) for i in ids[2:]] == [b"cloud 2", b"cloud 3", b"cloud 4"]
    assert len(list(tmp_path.glob("*.ply"))) == 3


def test_reserve_then_commit_registers_a_file_the_pipeline_wrote(tmp_path: Path) -> None:
    store, _clock = _store(tmp_path)

    cloud_id, path = store.reserve()
    assert store.get(cloud_id) is None, "nothing is fetchable before it is written"

    path.write_bytes(b"written by the pipeline")
    assert store.commit(cloud_id, path) == cloud_id
    assert store.get(cloud_id) == b"written by the pipeline"


def test_a_second_worker_can_serve_what_the_first_one_wrote(tmp_path: Path) -> None:
    """uvicorn runs several workers; the one that answers the download is
    usually not the one that ran the pipeline. Sharing a root is what makes the
    id resolvable, and the id is the filename, so no shared memory is needed."""
    writer, _ = _store(tmp_path)
    reader, _ = _store(tmp_path)  # a different process, same filesystem

    cloud_id = writer.put(b"written by worker A")

    assert reader.get(cloud_id) == b"written by worker A"


def test_default_root_is_stable_across_instances() -> None:
    """Two stores made with no explicit root must land in the same directory,
    or the multi-worker fix above never applies in production."""
    assert SegmentedCloudStore().root == SegmentedCloudStore().root


def test_commit_declines_a_file_the_pipeline_never_wrote(tmp_path: Path) -> None:
    """A run with no segmented output must not advertise one."""
    store, _clock = _store(tmp_path)

    cloud_id, path = store.reserve()
    assert store.commit(cloud_id, path) is None

    path.write_bytes(b"")
    assert store.commit(cloud_id, path) is None
    assert store.get(cloud_id) is None
