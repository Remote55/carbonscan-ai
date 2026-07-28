import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from pipeline import external_tree_dataset
from pipeline.external_tree_dataset import fetch_external_cohort, load_external_trees
from pipeline.provenance import sha256_file, write_canonical_json

METADATA_URL = "https://zenodo.org/api/records/6831378"


def _protocol():
    return {
        "experiment_id": "pointnet-independent-eval-2026-07-16",
        "external": {
            "provider": "Zenodo",
            "record_id": 6831378,
            "doi": "10.5281/zenodo.6831378",
            "license": "CC-BY-4.0",
            "expected_trees": 10,
            "concatenation_order": ["wood", "leaf"],
        },
    }


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _freeze_payload(checkpoint_sha256: str, protocol_sha256: str, commit: str):
    metrics = {
        "wood_iou": 0.5,
        "leaf_iou": 0.6,
        "mean_iou": 0.55,
        "accuracy": 0.7,
    }
    return {
        "schema_version": "1",
        "experiment_id": "pointnet-independent-eval-2026-07-16",
        "protocol_sha256": protocol_sha256,
        "wan_manifest_sha256": "a" * 64,
        "training_runs_sha256": "b" * 64,
        "training_git_commit": commit,
        "working_tree_clean": True,
        "training_command": ["python", "-m", "scripts.pointnet_evidence", "train"],
        "environment": {"python_version": "test", "device_type": "cpu"},
        "architecture": "PointNet2SegSSG",
        "training_configuration": {"seeds": [20260716, 20260717, 20260718]},
        "wan_evidence": {
            "schema_version": "1",
            "config": {},
            "sources": [],
            "outputs": {"train": {}, "dev": {}},
        },
        "winner": {
            "seed": 20260716,
            "selected_epoch": 12,
            "dev_metrics": metrics,
            "checkpoint_file": "winner.pt",
            "checkpoint_sha256": checkpoint_sha256,
            "state_dict_sha256": "c" * 64,
        },
        "rerun_evidence": {
            "seed": 20260716,
            "best_epoch": 12,
            "best_macro_tile_wood_iou": 0.5,
            "state_dict_sha256": "c" * 64,
            "checkpoint_file": "seed-20260716-rerun.pt",
            "checkpoint_sha256": "d" * 64,
            "reproducible": True,
        },
    }


def _guard_fixture(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "TreeQ Tests")
    (repo / ".gitignore").write_text(
        "/winner.pt\n/raw/\n/manifest.json\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-q", "-m", "fixture")
    checkpoint = repo / "winner.pt"
    checkpoint.write_bytes(b"frozen checkpoint")
    protocol_sha256 = "e" * 64
    freeze = repo / "freeze_manifest.json"
    write_canonical_json(
        freeze,
        _freeze_payload(
            sha256_file(checkpoint),
            protocol_sha256,
            _git(repo, "rev-parse", "HEAD"),
        ),
    )
    _git(repo, "add", "freeze_manifest.json")
    _git(repo, "commit", "-q", "-m", "freeze")
    assert not _git(repo, "status", "--porcelain", "--untracked-files=normal")
    return {
        "repo": repo,
        "freeze": freeze,
        "checkpoint": checkpoint,
        "destination": repo / "raw",
        "manifest_out": repo / "manifest.json",
        "protocol_sha256": protocol_sha256,
    }


def _pcd_files():
    files = []
    bodies = {}
    for tree_number in range(10):
        for part in ("wood", "leaf"):
            filename = f"tree-{tree_number:02d}_{part}.pcd"
            body = f"{filename}\n".encode()
            url = f"https://zenodo.org/api/files/test/{filename}"
            bodies[url] = body
            files.append(
                {
                    "key": filename,
                    "checksum": f"md5:{hashlib.md5(body).hexdigest()}",
                    "size": len(body),
                    "links": {"content": url, "self": url},
                }
            )
    return files, bodies


def _metadata(files):
    return {
        "id": 6831378,
        "doi": "10.5281/zenodo.6831378",
        "metadata": {"license": {"id": "cc-by-4.0"}},
        "files": files,
    }


def _rename_tree_pair(files, bodies, old_tree_id, new_tree_id):
    for entry in files:
        filename = entry["key"]
        if not filename.startswith(f"{old_tree_id}_"):
            continue
        part = filename.removeprefix(f"{old_tree_id}_").removesuffix(".pcd")
        renamed = f"{new_tree_id}_{part}.pcd"
        old_url = entry["links"]["content"]
        body = f"{renamed}\n".encode()
        url = f"https://zenodo.org/api/files/test/{renamed}"
        bodies.pop(old_url)
        bodies[url] = body
        entry.update(
            {
                "key": renamed,
                "checksum": f"md5:{hashlib.md5(body).hexdigest()}",
                "size": len(body),
                "links": {"content": url, "self": url},
            }
        )


def _assert_no_fetch_outputs(fixture):
    if fixture["destination"].exists():
        assert list(fixture["destination"].iterdir()) == []
    assert not fixture["manifest_out"].exists()
    assert not fixture["manifest_out"].with_name(f"{fixture['manifest_out'].name}.part").exists()


class _Response:
    def __init__(self, *, payload=None, body=b""):
        self._payload = payload
        self._body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload

    def iter_bytes(self):
        midpoint = max(1, len(self._body) // 2)
        yield self._body[:midpoint]
        yield self._body[midpoint:]


class _Client:
    def __init__(self, metadata, bodies):
        self.metadata = metadata
        self.bodies = bodies
        self.calls = []

    def get(self, url):
        self.calls.append(url)
        if url == METADATA_URL:
            return _Response(payload=self.metadata)
        return _Response(body=self.bodies[url])


def _fetch(fixture, client):
    return fetch_external_cohort(
        protocol=_protocol(),
        freeze_manifest=fixture["freeze"],
        checkpoint=fixture["checkpoint"],
        destination=fixture["destination"],
        manifest_out=fixture["manifest_out"],
        repo_root=fixture["repo"],
        client=client,
        protocol_sha256=fixture["protocol_sha256"],
    )


def test_fetch_refuses_missing_freeze_before_http(tmp_path: Path):
    called = False

    class Client:
        def get(self, url):
            nonlocal called
            called = True
            raise AssertionError("network must not be reached")

    with pytest.raises(ValueError, match="freeze"):
        fetch_external_cohort(
            protocol=_protocol(),
            freeze_manifest=tmp_path / "missing.json",
            checkpoint=tmp_path / "missing.pt",
            destination=tmp_path / "data",
            manifest_out=tmp_path / "manifest.json",
            repo_root=tmp_path,
            client=Client(),
        )
    assert called is False


def test_fetch_refuses_invalid_freeze_before_checkpoint_or_protocol_hash(tmp_path: Path):
    freeze = tmp_path / "freeze.json"
    freeze.write_text("{}", encoding="utf-8")
    client = _Client({}, {})

    with pytest.raises(ValueError, match=r"freeze manifest.*schema"):
        fetch_external_cohort(
            protocol=_protocol(),
            freeze_manifest=freeze,
            checkpoint=tmp_path / "missing.pt",
            destination=tmp_path / "data",
            manifest_out=tmp_path / "manifest.json",
            repo_root=tmp_path,
            client=client,
        )

    assert client.calls == []


def test_fetch_rejects_checkpoint_hash_before_http(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    fixture["checkpoint"].write_bytes(b"tampered")
    client = _Client({}, {})

    with pytest.raises(ValueError, match=r"checkpoint.*sha256"):
        _fetch(fixture, client)

    assert client.calls == []


def test_fetch_requires_actual_protocol_sha256_before_http(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    client = _Client({}, {})
    fixture["protocol_sha256"] = "f" * 64

    with pytest.raises(ValueError, match=r"protocol.*sha256"):
        _fetch(fixture, client)

    assert client.calls == []


def test_fetch_rejects_dirty_repo_before_http(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    (fixture["repo"] / "dirty.txt").write_text("dirty", encoding="utf-8")
    client = _Client({}, {})

    with pytest.raises(ValueError, match="clean"):
        _fetch(fixture, client)

    assert client.calls == []


def test_fetch_rejects_freeze_bytes_that_differ_from_head_before_http(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    _git(fixture["repo"], "update-index", "--assume-unchanged", "freeze_manifest.json")
    fixture["freeze"].write_bytes(fixture["freeze"].read_bytes() + b" ")
    client = _Client({}, {})

    with pytest.raises(ValueError, match="tracked HEAD"):
        _fetch(fixture, client)

    assert client.calls == []


def test_fetch_converts_training_ancestor_git_failure_to_value_error(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    freeze = json.loads(fixture["freeze"].read_text(encoding="utf-8"))
    freeze["training_git_commit"] = "1" * 40
    write_canonical_json(fixture["freeze"], freeze)
    _git(fixture["repo"], "add", "freeze_manifest.json")
    _git(fixture["repo"], "commit", "-q", "-m", "invalid ancestor fixture")
    client = _Client({}, {})

    with pytest.raises(ValueError, match="Git validation failed"):
        _fetch(fixture, client)

    assert client.calls == []


def test_fetch_rejects_manifest_inside_raw_destination_before_http(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    fixture["manifest_out"] = fixture["destination"] / "manifest.json"
    client = _Client({}, {})

    with pytest.raises(ValueError, match="raw destination"):
        _fetch(fixture, client)

    assert client.calls == []


@pytest.mark.parametrize("output_kind", ["final", "part", "manifest"])
def test_fetch_rejects_preexisting_output_before_http_without_deleting_it(
    tmp_path: Path, output_kind: str
):
    fixture = _guard_fixture(tmp_path)
    if output_kind == "manifest":
        output = fixture["manifest_out"]
    else:
        fixture["destination"].mkdir()
        suffix = "" if output_kind == "final" else ".part"
        output = fixture["destination"] / f"tree-00_wood.pcd{suffix}"
    output.write_bytes(b"belongs to user")
    files, bodies = _pcd_files()
    client = _Client(_metadata(files), bodies)

    with pytest.raises(ValueError, match="output already exists"):
        _fetch(fixture, client)

    assert client.calls == []
    assert output.read_bytes() == b"belongs to user"


def test_fetch_rejects_wrong_expected_pair_count_before_download(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    client = _Client(_metadata(files[:-2]), bodies)

    with pytest.raises(ValueError, match="20"):
        _fetch(fixture, client)

    assert client.calls == [METADATA_URL]
    assert not fixture["destination"].exists()


def test_fetch_rejects_duplicate_filename_before_download(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    files[-1] = dict(files[0])
    client = _Client(_metadata(files), bodies)

    with pytest.raises(ValueError, match="duplicate filename"):
        _fetch(fixture, client)

    assert client.calls == [METADATA_URL]


def test_fetch_rejects_publisher_path_traversal_before_download(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    files[0] = {**files[0], "key": "../escape_wood.pcd"}
    client = _Client(_metadata(files), bodies)

    with pytest.raises(ValueError, match="path-safe"):
        _fetch(fixture, client)

    assert client.calls == [METADATA_URL]
    assert not (fixture["repo"] / "escape_wood.pcd").exists()


@pytest.mark.parametrize(
    "tree_id",
    [
        "tree-00:alternate-stream",
        "CON",
        "tree-00 ",
        "tree-00.",
        "tree-\x1f00",
    ],
)
def test_fetch_rejects_nonportable_publisher_filename_before_download(tmp_path: Path, tree_id: str):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    _rename_tree_pair(files, bodies, "tree-00", tree_id)
    client = _Client(_metadata(files), bodies)

    with pytest.raises(ValueError, match="portable logical PCD filename"):
        _fetch(fixture, client)

    assert client.calls == [METADATA_URL]
    assert not fixture["destination"].exists()


def test_fetch_rejects_case_only_publisher_pair_alias_before_download(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    _rename_tree_pair(files, bodies, "tree-01", "TREE-00")
    client = _Client(_metadata(files), bodies)

    with pytest.raises(ValueError, match="case-insensitive"):
        _fetch(fixture, client)

    assert client.calls == [METADATA_URL]
    assert not fixture["destination"].exists()


def test_fetch_rejects_wrong_zenodo_record_before_download(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    metadata = _metadata(files)
    metadata["id"] = 6831379
    client = _Client(metadata, bodies)

    with pytest.raises(ValueError, match="exact record 6831378"):
        _fetch(fixture, client)

    assert client.calls == [METADATA_URL]


def test_fetch_removes_part_and_manifest_on_md5_mismatch(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    files[0] = {**files[0], "checksum": "md5:" + "0" * 32}
    client = _Client(_metadata(files), bodies)

    with pytest.raises(ValueError, match="MD5"):
        _fetch(fixture, client)

    assert not list(fixture["destination"].glob("*.part"))
    assert not fixture["manifest_out"].exists()


def test_fetch_rolls_back_late_md5_failure_and_reruns_same_destination(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    late = next(entry for entry in files if entry["key"] == "tree-09_wood.pcd")
    late["checksum"] = "md5:" + "0" * 32

    with pytest.raises(ValueError, match="MD5"):
        _fetch(fixture, _Client(_metadata(files), bodies))

    _assert_no_fetch_outputs(fixture)
    retry_files, retry_bodies = _pcd_files()
    manifest = _fetch(fixture, _Client(_metadata(retry_files), retry_bodies))
    assert len(manifest["files"]) == 20
    assert fixture["manifest_out"].is_file()


def test_fetch_rolls_back_manifest_write_failure_and_reruns_same_destination(
    tmp_path: Path, monkeypatch
):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    real_write = external_tree_dataset.write_canonical_json

    def injected_write_failure(path, payload):
        real_write(path, payload)
        raise OSError("injected manifest write failure")

    monkeypatch.setattr(
        external_tree_dataset,
        "write_canonical_json",
        injected_write_failure,
    )
    with pytest.raises(OSError, match="injected manifest write failure"):
        _fetch(fixture, _Client(_metadata(files), bodies))

    _assert_no_fetch_outputs(fixture)
    monkeypatch.setattr(external_tree_dataset, "write_canonical_json", real_write)
    retry_files, retry_bodies = _pcd_files()
    manifest = _fetch(fixture, _Client(_metadata(retry_files), retry_bodies))
    assert len(manifest["files"]) == 20
    assert fixture["manifest_out"].is_file()


def test_fetch_writes_canonical_path_private_manifest_with_local_sha256(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    client = _Client(_metadata(files), bodies)

    manifest = _fetch(fixture, client)

    written = json.loads(fixture["manifest_out"].read_text(encoding="utf-8"))
    assert manifest == written
    assert fixture["manifest_out"].read_bytes().endswith(b"\n")
    assert manifest["record"] == {
        "provider": "Zenodo",
        "record_id": 6831378,
        "doi": "10.5281/zenodo.6831378",
        "license": "CC-BY-4.0",
    }
    assert manifest["tree_ids"] == [f"tree-{index:02d}" for index in range(10)]
    for record in manifest["files"]:
        local_path = fixture["destination"] / record["filename"]
        assert record["sha256"] == sha256_file(local_path)
        assert record["size_bytes"] == local_path.stat().st_size
    assert str(tmp_path) not in repr(manifest)
    assert not list(fixture["destination"].glob("*.part"))


def test_fetch_allows_authorized_destination_outside_repo_without_path_leak(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    fixture["destination"] = tmp_path / "authorized-external-raw"
    files, bodies = _pcd_files()

    manifest = _fetch(fixture, _Client(_metadata(files), bodies))

    assert len(list(fixture["destination"].glob("*.pcd"))) == 20
    assert str(fixture["destination"]) not in repr(manifest)
    assert str(fixture["repo"]) not in repr(manifest)


def test_load_external_trees_concatenates_wood_before_leaf(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    manifest = _fetch(fixture, _Client(_metadata(files), bodies))

    def point_loader(path):
        tree_number = int(path.name[5:7])
        if path.name.endswith("_wood.pcd"):
            return np.array([[tree_number, 1.0, 2.0], [tree_number, 3.0, 4.0]])
        return np.array([[tree_number, 5.0, 6.0]])

    trees = load_external_trees(fixture["destination"], manifest, point_loader)

    assert [tree_id for tree_id, _, _ in trees] == manifest["tree_ids"]
    _, points, gt = trees[0]
    np.testing.assert_array_equal(
        points,
        np.array([[0.0, 1.0, 2.0], [0.0, 3.0, 4.0], [0.0, 5.0, 6.0]]),
    )
    np.testing.assert_array_equal(gt, np.array([0, 0, 1], dtype=np.uint8))
    assert points.dtype == np.float64
    assert gt.dtype == np.uint8


def test_load_external_trees_rejects_duplicate_tree_ids(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    manifest = _fetch(fixture, _Client(_metadata(files), bodies))
    manifest["tree_ids"][-1] = manifest["tree_ids"][0]

    with pytest.raises(ValueError, match="duplicate tree"):
        load_external_trees(fixture["destination"], manifest, lambda path: np.ones((1, 3)))


def test_load_external_trees_rejects_casefold_manifest_filename_alias(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    manifest = _fetch(fixture, _Client(_metadata(files), bodies))
    for record in manifest["files"]:
        if record["tree_id"] == "tree-01":
            record["filename"] = record["filename"].replace("tree-01", "TREE-00")
            record["tree_id"] = "TREE-00"
    manifest["tree_ids"] = sorted(
        "TREE-00" if tree_id == "tree-01" else tree_id for tree_id in manifest["tree_ids"]
    )
    manifest["files"].sort(key=lambda record: record["filename"])

    with pytest.raises(ValueError, match="case-insensitive"):
        load_external_trees(fixture["destination"], manifest, lambda path: np.ones((1, 3)))


def test_load_external_trees_rejects_local_sha256_drift(tmp_path: Path):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    manifest = _fetch(fixture, _Client(_metadata(files), bodies))
    drifted = fixture["destination"] / manifest["files"][0]["filename"]
    drifted.write_bytes(b"x" * drifted.stat().st_size)

    with pytest.raises(ValueError, match="sha256"):
        load_external_trees(fixture["destination"], manifest, lambda path: np.ones((1, 3)))


@pytest.mark.parametrize(
    ("bad_points", "message"),
    [
        (np.empty((0, 3)), "nonempty Nx3"),
        (np.array([[np.nan, 0.0, 0.0]]), "non-finite"),
    ],
)
def test_load_external_trees_rejects_invalid_point_coordinates(
    tmp_path: Path, bad_points: np.ndarray, message: str
):
    fixture = _guard_fixture(tmp_path)
    files, bodies = _pcd_files()
    manifest = _fetch(fixture, _Client(_metadata(files), bodies))

    with pytest.raises(ValueError, match=message):
        load_external_trees(fixture["destination"], manifest, lambda path: bad_points)


def test_fetch_external_cli_hashes_actual_protocol_file(tmp_path: Path, monkeypatch, capsys):
    from scripts import pointnet_evidence

    protocol_path = (
        Path(__file__).parents[3] / "docs/evidence/pointnet_independent_eval/protocol.json"
    )
    captured = {}

    def fake_fetch(**kwargs):
        captured.update(kwargs)
        return {
            "record": {"record_id": 6831378},
            "files": [{}] * 20,
            "tree_ids": [str(i) for i in range(10)],
        }

    monkeypatch.setattr(pointnet_evidence, "fetch_external_cohort", fake_fetch)
    exit_code = pointnet_evidence.main(
        [
            "fetch-external",
            "--protocol",
            str(protocol_path),
            "--freeze-manifest",
            str(tmp_path / "freeze.json"),
            "--checkpoint",
            str(tmp_path / "winner.pt"),
            "--destination",
            str(tmp_path / "raw"),
            "--manifest-out",
            str(tmp_path / "manifest.json"),
            "--repo-root",
            str(tmp_path),
        ]
    )

    lines = capsys.readouterr().out.splitlines()
    assert exit_code == 0
    assert len(lines) == 1
    lines[0].encode("ascii")
    assert json.loads(lines[0]) == {
        "command": "fetch-external",
        "files": 20,
        "record_id": 6831378,
        "status": "ok",
        "trees": 10,
    }
    assert captured["protocol_sha256"] == sha256_file(protocol_path)
    assert captured["protocol"]["external"]["record_id"] == 6831378
