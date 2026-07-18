"""Guarded download and deterministic loading for the blind external cohort."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import numpy as np

from pipeline.provenance import sha256_file, write_canonical_json

_METADATA_URL = "https://zenodo.org/api/records/6831378"
_LOWER_HEX = frozenset("0123456789abcdef")
_EXPECTED_EXTERNAL = {
    "provider": "Zenodo",
    "record_id": 6831378,
    "doi": "10.5281/zenodo.6831378",
    "license": "CC-BY-4.0",
    "expected_trees": 10,
    "concatenation_order": ["wood", "leaf"],
}
_FREEZE_KEYS = {
    "schema_version",
    "experiment_id",
    "protocol_sha256",
    "wan_manifest_sha256",
    "training_runs_sha256",
    "training_git_commit",
    "working_tree_clean",
    "training_command",
    "environment",
    "architecture",
    "training_configuration",
    "wan_evidence",
    "winner",
    "rerun_evidence",
}
_WINNER_KEYS = {
    "seed",
    "selected_epoch",
    "dev_metrics",
    "checkpoint_file",
    "checkpoint_sha256",
    "state_dict_sha256",
}
_RERUN_KEYS = {
    "seed",
    "best_epoch",
    "best_macro_tile_wood_iou",
    "state_dict_sha256",
    "checkpoint_file",
    "checkpoint_sha256",
    "reproducible",
}
_MANIFEST_KEYS = {
    "schema_version",
    "experiment_id",
    "protocol_sha256",
    "freeze_manifest_sha256",
    "checkpoint_sha256",
    "record",
    "tree_ids",
    "files",
}
_FILE_KEYS = {
    "filename",
    "tree_id",
    "part",
    "publisher_md5",
    "publisher_size_bytes",
    "sha256",
    "size_bytes",
}


def _is_lower_hex(value: Any, length: int) -> bool:
    return (
        type(value) is str
        and len(value) == length
        and all(character in _LOWER_HEX for character in value)
    )


def _require_exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != expected:
        raise ValueError(f"{label} schema is not exact")
    return value


def _validate_metrics(value: Any, label: str) -> None:
    metrics = _require_exact_keys(
        value,
        {"wood_iou", "leaf_iou", "mean_iou", "accuracy"},
        label,
    )
    for name, metric in metrics.items():
        if type(metric) is not float or not math.isfinite(metric) or not 0.0 <= metric <= 1.0:
            raise ValueError(f"{label}.{name} must be a finite float in [0, 1]")


def _load_freeze(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("freeze manifest is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("freeze manifest cannot be parsed") from exc
    freeze = _require_exact_keys(payload, _FREEZE_KEYS, "freeze manifest")
    if freeze["schema_version"] != "1":
        raise ValueError("freeze manifest schema_version must equal '1'")
    if type(freeze["experiment_id"]) is not str or not freeze["experiment_id"]:
        raise ValueError("freeze manifest experiment_id must be a non-empty string")
    for name in ("protocol_sha256", "wan_manifest_sha256", "training_runs_sha256"):
        if not _is_lower_hex(freeze[name], 64):
            raise ValueError(f"freeze manifest {name} must be lowercase SHA-256")
    if not _is_lower_hex(freeze["training_git_commit"], 40):
        raise ValueError("freeze manifest training_git_commit must be 40 lowercase hex")
    if freeze["working_tree_clean"] is not True:
        raise ValueError("freeze manifest working_tree_clean must be true")
    command = freeze["training_command"]
    if (
        type(command) is not list
        or not command
        or any(type(item) is not str or not item for item in command)
    ):
        raise ValueError("freeze manifest training_command must be non-empty strings")
    if type(freeze["environment"]) is not dict:
        raise ValueError("freeze manifest environment must be an object")
    if freeze["architecture"] != "PointNet2SegSSG":
        raise ValueError("freeze manifest architecture must equal PointNet2SegSSG")
    if type(freeze["training_configuration"]) is not dict:
        raise ValueError("freeze manifest training_configuration must be an object")
    wan = _require_exact_keys(
        freeze["wan_evidence"],
        {"schema_version", "config", "sources", "outputs"},
        "freeze manifest wan_evidence",
    )
    if (
        wan["schema_version"] != "1"
        or type(wan["config"]) is not dict
        or type(wan["sources"]) is not list
        or type(wan["outputs"]) is not dict
        or set(wan["outputs"]) != {"train", "dev"}
    ):
        raise ValueError("freeze manifest wan_evidence schema is invalid")
    winner = _require_exact_keys(freeze["winner"], _WINNER_KEYS, "freeze manifest winner")
    if type(winner["seed"]) is not int or type(winner["selected_epoch"]) is not int:
        raise ValueError("freeze manifest winner seed/epoch must be integers")
    _validate_metrics(winner["dev_metrics"], "freeze manifest winner.dev_metrics")
    if winner["checkpoint_file"] != "winner.pt":
        raise ValueError("freeze manifest winner checkpoint_file must equal winner.pt")
    for name in ("checkpoint_sha256", "state_dict_sha256"):
        if not _is_lower_hex(winner[name], 64):
            raise ValueError(f"freeze manifest winner {name} must be lowercase SHA-256")
    rerun = _require_exact_keys(
        freeze["rerun_evidence"],
        _RERUN_KEYS,
        "freeze manifest rerun_evidence",
    )
    if (
        type(rerun["seed"]) is not int
        or type(rerun["best_epoch"]) is not int
        or type(rerun["best_macro_tile_wood_iou"]) is not float
        or not math.isfinite(rerun["best_macro_tile_wood_iou"])
        or rerun["reproducible"] is not True
    ):
        raise ValueError("freeze manifest rerun_evidence values are invalid")
    if type(rerun["checkpoint_file"]) is not str or not rerun["checkpoint_file"]:
        raise ValueError("freeze manifest rerun checkpoint_file is invalid")
    for name in ("checkpoint_sha256", "state_dict_sha256"):
        if not _is_lower_hex(rerun[name], 64):
            raise ValueError(f"freeze manifest rerun {name} must be lowercase SHA-256")
    return freeze


def _run_git(repo_root: Path, *arguments: str, text: bool = False) -> str | bytes:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=text,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"Git validation failed: {' '.join(arguments)}") from exc
    return completed.stdout


def _validate_git_guards(repo_root: Path, freeze_path: Path, freeze: dict[str, Any]) -> None:
    status = _run_git(
        repo_root,
        "status",
        "--porcelain",
        "--untracked-files=normal",
        text=True,
    )
    if str(status).strip():
        raise ValueError("Git working tree must be clean before external fetch")
    try:
        logical_path = freeze_path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("freeze manifest must be inside repo_root") from exc
    _run_git(repo_root, "ls-files", "--error-unmatch", "--", logical_path)
    head_bytes = _run_git(repo_root, "show", f"HEAD:{logical_path}")
    if head_bytes != freeze_path.read_bytes():
        raise ValueError("freeze manifest bytes do not match tracked HEAD")
    _run_git(
        repo_root,
        "merge-base",
        "--is-ancestor",
        freeze["training_git_commit"],
        "HEAD",
    )


def _validate_protocol(
    protocol: dict[str, Any], freeze: dict[str, Any], protocol_sha256: str | None
) -> dict[str, Any]:
    if not _is_lower_hex(protocol_sha256, 64):
        raise ValueError("protocol_sha256 must be a 64-character lowercase SHA-256")
    if protocol_sha256 != freeze["protocol_sha256"]:
        raise ValueError("protocol_sha256 does not match freeze manifest")
    if type(protocol) is not dict or protocol.get("experiment_id") != freeze["experiment_id"]:
        raise ValueError("protocol experiment_id does not match freeze manifest")
    external = protocol.get("external")
    if type(external) is not dict or external != _EXPECTED_EXTERNAL:
        raise ValueError("protocol external cohort contract is not exact")
    training = protocol.get("training")
    if training is not None and training != freeze["training_configuration"]:
        raise ValueError("protocol training configuration does not match freeze manifest")
    return external


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_output_paths(
    destination: Path,
    manifest_out: Path,
    freeze_path: Path,
    checkpoint_path: Path,
    repo_root: Path,
) -> None:
    destination = destination.resolve()
    manifest_out = manifest_out.resolve()
    freeze_path = freeze_path.resolve()
    checkpoint_path = checkpoint_path.resolve()
    repo_root = repo_root.resolve()
    if destination.exists() and not destination.is_dir():
        raise ValueError("destination must be a directory")
    if manifest_out.exists() or manifest_out.with_name(f"{manifest_out.name}.part").exists():
        raise ValueError("manifest output already exists")
    if manifest_out in {freeze_path, checkpoint_path}:
        raise ValueError("manifest output cannot alias frozen inputs")
    if destination == repo_root or _is_within(repo_root, destination):
        raise ValueError("destination cannot be repo_root or its ancestor")
    if any(_is_within(path, destination) for path in (manifest_out, freeze_path, checkpoint_path)):
        raise ValueError("manifest output and frozen inputs cannot alias raw destination")


def _simple_filename(value: Any) -> str:
    if type(value) is not str or not value:
        raise ValueError("publisher filename must be a non-empty string")
    if (
        PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
        or Path(value).name != value
        or "/" in value
        or "\\" in value
        or value in {".", ".."}
    ):
        raise ValueError(f"publisher filename is not path-safe: {value!r}")
    return value


def _pair_identity(filename: str) -> tuple[str, str]:
    for suffix, part in (("_wood.pcd", "wood"), ("_leaf.pcd", "leaf")):
        if filename.endswith(suffix):
            tree_id = filename[: -len(suffix)]
            if not tree_id:
                raise ValueError("tree ID must not be empty")
            return tree_id, part
    raise ValueError(f"filename is not a case-sensitive wood/leaf PCD: {filename!r}")


def _publisher_files(metadata: Any) -> tuple[list[dict[str, Any]], list[str]]:
    if type(metadata) is not dict or metadata.get("id") != 6831378:
        raise ValueError("Zenodo metadata must identify exact record 6831378")
    if metadata.get("doi") != _EXPECTED_EXTERNAL["doi"]:
        raise ValueError("Zenodo metadata DOI does not match record 6831378")
    license_payload = metadata.get("metadata")
    if (
        type(license_payload) is not dict
        or type(license_payload.get("license")) is not dict
        or license_payload["license"].get("id") != "cc-by-4.0"
    ):
        raise ValueError("Zenodo metadata license must equal CC-BY-4.0")
    entries = metadata.get("files")
    if type(entries) is not list:
        raise ValueError("Zenodo metadata files must be a list")
    selected = []
    seen_filenames: set[str] = set()
    pairs: dict[str, dict[str, str]] = {}
    for index, entry in enumerate(entries):
        if type(entry) is not dict:
            raise ValueError(f"Zenodo file {index} must be an object")
        key = entry.get("key")
        if type(key) is not str or not key.endswith(("_wood.pcd", "_leaf.pcd")):
            continue
        filename = _simple_filename(key)
        if filename in seen_filenames:
            raise ValueError(f"duplicate filename in Zenodo metadata: {filename}")
        seen_filenames.add(filename)
        tree_id, part = _pair_identity(filename)
        tree_parts = pairs.setdefault(tree_id, {})
        if part in tree_parts:
            raise ValueError(f"duplicate tree ID/part in Zenodo metadata: {tree_id}/{part}")
        tree_parts[part] = filename
        checksum = entry.get("checksum")
        if type(checksum) is not str or not checksum.startswith("md5:"):
            raise ValueError(f"publisher MD5 is missing for {filename}")
        publisher_md5 = checksum[4:]
        if not _is_lower_hex(publisher_md5, 32):
            raise ValueError(f"publisher MD5 is invalid for {filename}")
        size = entry.get("size")
        if type(size) is not int or size < 0:
            raise ValueError(f"publisher size is invalid for {filename}")
        links = entry.get("links")
        if type(links) is not dict:
            raise ValueError(f"publisher links are invalid for {filename}")
        url = links.get("content") or links.get("self")
        if type(url) is not str or not url.startswith("https://"):
            raise ValueError(f"publisher download URL is invalid for {filename}")
        selected.append(
            {
                "filename": filename,
                "tree_id": tree_id,
                "part": part,
                "publisher_md5": publisher_md5,
                "publisher_size_bytes": size,
                "url": url,
            }
        )
    if len(selected) != 20:
        raise ValueError(
            f"Zenodo record must contain exactly 20 labelled PCD files, got {len(selected)}"
        )
    if len(pairs) != 10:
        raise ValueError(f"Zenodo record must contain exactly 10 unique tree IDs, got {len(pairs)}")
    for tree_id, parts in pairs.items():
        if set(parts) != {"wood", "leaf"}:
            raise ValueError(f"tree {tree_id!r} does not have exactly one wood/leaf pair")
    tree_ids = sorted(pairs)
    return sorted(selected, key=lambda item: item["filename"]), tree_ids


def _response(client: Any, url: str) -> Any:
    response = client.get(url)
    response.raise_for_status()
    return response


def _metadata_request(client: Any | None) -> dict[str, Any]:
    if client is not None:
        payload = _response(client, _METADATA_URL).json()
    else:
        import httpx

        response = httpx.get(_METADATA_URL, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
    if type(payload) is not dict:
        raise ValueError("Zenodo metadata response must be an object")
    return payload


@contextmanager
def _download_chunks(client: Any | None, url: str) -> Iterator[Iterator[bytes]]:
    if client is not None:
        response = _response(client, url)
        try:
            yield response.iter_bytes()
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()
        return
    import httpx

    with httpx.stream("GET", url, follow_redirects=True, timeout=60.0) as response:
        response.raise_for_status()
        yield response.iter_bytes()


def _download_one(client: Any | None, destination: Path, record: dict[str, Any]) -> dict[str, Any]:
    final_path = destination / record["filename"]
    part_path = destination / f"{record['filename']}.part"
    md5_digest = hashlib.md5()
    sha256_digest = hashlib.sha256()
    size = 0
    try:
        with _download_chunks(client, record["url"]) as chunks, part_path.open("xb") as stream:
            for chunk in chunks:
                if not isinstance(chunk, bytes):
                    raise ValueError(f"download chunk for {record['filename']} is not bytes")
                if not chunk:
                    continue
                stream.write(chunk)
                md5_digest.update(chunk)
                sha256_digest.update(chunk)
                size += len(chunk)
        if md5_digest.hexdigest() != record["publisher_md5"]:
            raise ValueError(f"publisher MD5 mismatch for {record['filename']}")
        if size != record["publisher_size_bytes"]:
            raise ValueError(f"publisher size mismatch for {record['filename']}")
        part_path.replace(final_path)
    except Exception:
        part_path.unlink(missing_ok=True)
        raise
    return {
        "filename": record["filename"],
        "tree_id": record["tree_id"],
        "part": record["part"],
        "publisher_md5": record["publisher_md5"],
        "publisher_size_bytes": record["publisher_size_bytes"],
        "sha256": sha256_digest.hexdigest(),
        "size_bytes": size,
    }


def fetch_external_cohort(
    protocol: dict[str, Any],
    freeze_manifest: str | Path,
    checkpoint: str | Path,
    destination: str | Path,
    manifest_out: str | Path,
    repo_root: str | Path,
    client: Any | None = None,
    *,
    protocol_sha256: str | None = None,
) -> dict[str, Any]:
    """Fetch the external cohort only after every frozen-evidence guard passes."""

    freeze_path = Path(freeze_manifest).resolve()
    freeze = _load_freeze(freeze_path)

    checkpoint_path = Path(checkpoint).resolve()
    if not checkpoint_path.is_file():
        raise ValueError("checkpoint is missing")
    checkpoint_sha256 = sha256_file(checkpoint_path)
    if checkpoint_sha256 != freeze["winner"]["checkpoint_sha256"]:
        raise ValueError("checkpoint sha256 does not match freeze manifest")

    external = _validate_protocol(protocol, freeze, protocol_sha256)
    repo_path = Path(repo_root).resolve()
    _validate_git_guards(repo_path, freeze_path, freeze)

    destination_path = Path(destination).resolve()
    manifest_path = Path(manifest_out).resolve()
    _validate_output_paths(
        destination_path,
        manifest_path,
        freeze_path,
        checkpoint_path,
        repo_path,
    )

    publisher_files, tree_ids = _publisher_files(_metadata_request(client))
    for record in publisher_files:
        final_path = destination_path / record["filename"]
        part_path = destination_path / f"{record['filename']}.part"
        if final_path.exists() or part_path.exists():
            raise ValueError(f"raw output already exists for {record['filename']}")

    destination_path.mkdir(parents=True, exist_ok=True)
    files = [_download_one(client, destination_path, record) for record in publisher_files]
    manifest = {
        "schema_version": "1",
        "experiment_id": freeze["experiment_id"],
        "protocol_sha256": protocol_sha256,
        "freeze_manifest_sha256": sha256_file(freeze_path),
        "checkpoint_sha256": checkpoint_sha256,
        "record": {
            "provider": external["provider"],
            "record_id": external["record_id"],
            "doi": external["doi"],
            "license": external["license"],
        },
        "tree_ids": tree_ids,
        "files": files,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_part = manifest_path.with_name(f"{manifest_path.name}.part")
    try:
        write_canonical_json(manifest_part, manifest)
        manifest_part.replace(manifest_path)
    except Exception:
        manifest_part.unlink(missing_ok=True)
        raise
    return manifest


def _validate_manifest(manifest: Any) -> tuple[list[dict[str, Any]], list[str]]:
    payload = _require_exact_keys(manifest, _MANIFEST_KEYS, "external dataset manifest")
    if payload["schema_version"] != "1":
        raise ValueError("external dataset manifest schema_version must equal '1'")
    if type(payload["experiment_id"]) is not str or not payload["experiment_id"]:
        raise ValueError("external dataset manifest experiment_id is invalid")
    for name in ("protocol_sha256", "freeze_manifest_sha256", "checkpoint_sha256"):
        if not _is_lower_hex(payload[name], 64):
            raise ValueError(f"external dataset manifest {name} must be lowercase SHA-256")
    if payload["record"] != {
        "provider": "Zenodo",
        "record_id": 6831378,
        "doi": "10.5281/zenodo.6831378",
        "license": "CC-BY-4.0",
    }:
        raise ValueError("external dataset manifest record identity is invalid")
    tree_ids = payload["tree_ids"]
    if (
        type(tree_ids) is not list
        or len(tree_ids) != 10
        or any(type(tree_id) is not str or not tree_id for tree_id in tree_ids)
        or len(set(tree_ids)) != 10
    ):
        raise ValueError("external dataset manifest has duplicate tree IDs or wrong count")
    if tree_ids != sorted(tree_ids):
        raise ValueError("external dataset manifest tree IDs are not deterministic")
    entries = payload["files"]
    if type(entries) is not list or len(entries) != 20:
        raise ValueError("external dataset manifest must contain exactly 20 files")
    pairs: dict[str, set[str]] = {}
    filenames: set[str] = set()
    validated = []
    for index, entry in enumerate(entries):
        record = _require_exact_keys(entry, _FILE_KEYS, f"external file {index}")
        filename = _simple_filename(record["filename"])
        if filename in filenames:
            raise ValueError(f"external dataset manifest duplicate filename: {filename}")
        filenames.add(filename)
        tree_id, part = _pair_identity(filename)
        if record["tree_id"] != tree_id or record["part"] != part:
            raise ValueError(f"external file identity mismatch for {filename}")
        parts = pairs.setdefault(tree_id, set())
        if part in parts:
            raise ValueError(f"external dataset manifest duplicate tree part: {tree_id}/{part}")
        parts.add(part)
        for name, length in (("publisher_md5", 32), ("sha256", 64)):
            if not _is_lower_hex(record[name], length):
                raise ValueError(f"external file {filename} {name} is invalid")
        for name in ("publisher_size_bytes", "size_bytes"):
            if type(record[name]) is not int or record[name] < 0:
                raise ValueError(f"external file {filename} {name} is invalid")
        if record["publisher_size_bytes"] != record["size_bytes"]:
            raise ValueError(f"external file {filename} publisher size mismatch")
        validated.append(record)
    if set(pairs) != set(tree_ids) or any(parts != {"wood", "leaf"} for parts in pairs.values()):
        raise ValueError("external dataset manifest does not contain ten exact wood/leaf pairs")
    if [record["filename"] for record in validated] != sorted(filenames):
        raise ValueError("external dataset manifest files are not deterministic")
    return validated, tree_ids


def _open3d_points(path: Path) -> np.ndarray:
    import open3d as o3d

    cloud = o3d.io.read_point_cloud(str(path))
    return np.asarray(cloud.points)


def _validated_points(points: Any, filename: str) -> np.ndarray:
    try:
        array = np.asarray(points, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"point loader returned non-numeric coordinates for {filename}") from exc
    if array.ndim != 2 or array.shape[1:] != (3,) or len(array) == 0:
        raise ValueError(f"point file {filename} must contain nonempty Nx3 coordinates")
    if not np.isfinite(array).all():
        raise ValueError(f"point file {filename} contains non-finite coordinates")
    return array


def load_external_trees(
    root: str | Path,
    manifest: dict[str, Any],
    point_loader: Callable[[Path], np.ndarray] | None = None,
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Load verified wood/leaf pairs in deterministic tree order."""

    records, tree_ids = _validate_manifest(manifest)
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError("external dataset root is missing")
    by_identity: dict[tuple[str, str], Path] = {}
    for record in records:
        path = root_path / record["filename"]
        if not path.is_file():
            raise ValueError(f"external file is missing: {record['filename']}")
        if path.stat().st_size != record["size_bytes"]:
            raise ValueError(f"external file size mismatch: {record['filename']}")
        if sha256_file(path) != record["sha256"]:
            raise ValueError(f"external file sha256 mismatch: {record['filename']}")
        by_identity[(record["tree_id"], record["part"])] = path

    loader = point_loader or _open3d_points
    trees = []
    for tree_id in tree_ids:
        wood_path = by_identity[(tree_id, "wood")]
        leaf_path = by_identity[(tree_id, "leaf")]
        wood_points = _validated_points(loader(wood_path), wood_path.name)
        leaf_points = _validated_points(loader(leaf_path), leaf_path.name)
        points = np.vstack([wood_points, leaf_points]).astype(np.float64)
        gt = np.concatenate(
            [
                np.zeros(len(wood_points), dtype=np.uint8),
                np.ones(len(leaf_points), dtype=np.uint8),
            ]
        )
        trees.append((tree_id, points, gt))
    return trees
