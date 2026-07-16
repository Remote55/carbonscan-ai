import json
from pathlib import Path

import pytest

from training.evidence_protocol import load_protocol


PROTOCOL = Path(__file__).resolve().parents[3] / "docs/evidence/pointnet_independent_eval/protocol.json"


def test_checked_in_protocol_locks_blind_contract():
    p = load_protocol(PROTOCOL)
    assert p["training"]["seeds"] == [20260716, 20260717, 20260718]
    assert p["training"]["synthetic_samples"] == 200
    assert p["training"]["optimizer"] == "Adam"
    assert p["training"]["selection_tie_break"] == "lowest_seed"
    assert p["wan"]["n_off"] == 10000
    assert p["wan"]["per"] == 1500
    assert p["pointnet_inference"] == {
        "window_size_m": 2.5,
        "stride_m": 1.25,
        "model_points": 2048,
        "query_points": 1024,
        "seed": 0,
        "required_coverage": 1.0,
    }
    assert p["external"]["record_id"] == 6831378
    assert p["external"]["expected_trees"] == 10
    assert p["demol"]["expected_trees"] == 65
    assert p["statistics"] == {
        "method": "paired_percentile",
        "resampling_unit": "tree",
        "resamples": 10000,
        "seed": 20260716,
        "confidence": 0.95,
    }


def test_protocol_rejects_changed_seed(tmp_path):
    payload = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    payload["training"]["seeds"] = [1, 2, 3]
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="training.seeds"):
        load_protocol(path)


@pytest.mark.parametrize("replacement", [False, 20260716.0])
def test_protocol_rejects_json_type_aliases(tmp_path, replacement):
    payload = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    payload["training"]["seeds"][0] = replacement
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="training.seeds"):
        load_protocol(path)


def test_protocol_rejects_nested_bool_int_alias(tmp_path):
    payload = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    payload["pointnet_inference"]["seed"] = False
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="pointnet_inference.seed"):
        load_protocol(path)
