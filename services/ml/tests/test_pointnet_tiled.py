"""Strict tests for deterministic tiled PointNet++ inference."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from pipeline.pointnet_tiled import predict_tiled
from pipeline.wood_leaf_separation import WoodLeafSegmenter


def test_predict_tiled_covers_every_point_and_uses_fixed_normalized_model_size():
    rng = np.random.default_rng(3)
    points = rng.uniform([0, 0, 0], [5, 5, 8], size=(5000, 3))
    calls: list[np.ndarray] = []

    def fake_logits(batch: np.ndarray) -> np.ndarray:
        calls.append(batch.copy())
        assert batch.shape == (2048, 3)
        assert np.allclose(batch.mean(axis=0), 0.0, atol=1e-12)
        assert np.isclose(np.linalg.norm(batch, axis=1).max(), 1.0)
        logits = np.zeros((2048, 2), dtype=np.float64)
        logits[:, 0] = batch[:, 2]
        logits[:, 1] = -batch[:, 2]
        return logits

    first = predict_tiled(
        points,
        fake_logits,
        window_size_m=2.5,
        stride_m=1.25,
        model_points=2048,
        query_points=1024,
        seed=0,
    )
    first_calls = [batch.copy() for batch in calls]
    calls.clear()
    second = predict_tiled(
        points,
        fake_logits,
        window_size_m=2.5,
        stride_m=1.25,
        model_points=2048,
        query_points=1024,
        seed=0,
    )

    assert np.all(first.coverage >= 1)
    assert np.array_equal(first.labels, second.labels)
    assert np.array_equal(first.logits, second.logits)
    assert np.array_equal(first.coverage, second.coverage)
    assert len(first_calls) == len(calls)
    assert all(np.array_equal(left, right) for left, right in zip(first_calls, calls, strict=True))


def test_predict_tiled_puts_stably_sorted_query_points_first():
    points = np.column_stack(
        [
            np.zeros(6),
            np.zeros(6),
            np.arange(6, dtype=np.float64),
        ]
    )
    calls: list[np.ndarray] = []

    def fake_logits(batch: np.ndarray) -> np.ndarray:
        calls.append(batch.copy())
        return np.zeros((8, 2), dtype=np.float64)

    predict_tiled(
        points,
        fake_logits,
        window_size_m=1.0,
        stride_m=1.0,
        model_points=8,
        query_points=4,
        seed=11,
    )

    assert len(calls) == 2
    assert np.all(np.diff(calls[0][:4, 2]) > 0)
    assert calls[1][0, 2] < calls[1][1, 2]


def test_predict_tiled_averages_logits_after_all_overlapping_windows():
    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [2.1, 0.0, 0.0]])
    call_count = 0

    def fake_logits(batch: np.ndarray) -> np.ndarray:
        nonlocal call_count
        call_count += 1
        logits = np.zeros((4, 2), dtype=np.float64)
        logits[:, 0] = float(call_count)
        return logits

    prediction = predict_tiled(
        points,
        fake_logits,
        window_size_m=2.0,
        stride_m=1.0,
        model_points=4,
        query_points=2,
        seed=0,
    )

    assert call_count == 2
    assert np.array_equal(prediction.coverage, np.array([1, 2, 1]))
    assert np.array_equal(prediction.logits[:, 0], np.array([1.0, 1.5, 2.0]))
    assert np.array_equal(prediction.logits[:, 1], np.zeros(3))


def test_predict_tiled_handles_sparse_boundary_windows_deterministically():
    points = np.array([[0.0, 0.0, 4.0], [1.0, 0.0, 5.0], [2.0, 0.0, 6.0]])
    calls: list[np.ndarray] = []

    def fake_logits(batch: np.ndarray) -> np.ndarray:
        calls.append(batch.copy())
        return np.column_stack([batch[:, 2], -batch[:, 2]])

    first = predict_tiled(
        points,
        fake_logits,
        window_size_m=1.0,
        stride_m=1.0,
        model_points=8,
        query_points=4,
        seed=7,
    )
    first_calls = [batch.copy() for batch in calls]
    calls.clear()
    second = predict_tiled(
        points,
        fake_logits,
        window_size_m=1.0,
        stride_m=1.0,
        model_points=8,
        query_points=4,
        seed=7,
    )

    assert np.array_equal(first.coverage, np.array([1, 2, 1]))
    assert np.array_equal(first.coverage, second.coverage)
    assert np.array_equal(first.logits, second.logits)
    assert all(batch.shape == (8, 3) for batch in calls)
    assert all(np.array_equal(left, right) for left, right in zip(first_calls, calls, strict=True))


@pytest.mark.parametrize(
    ("points", "kwargs", "match"),
    [
        (np.zeros(3), {}, r"\(N, 3\)"),
        (np.array([[0.0, np.nan, 0.0]]), {}, "finite"),
        (np.zeros((1, 3)), {"window_size_m": 0.0}, "window_size_m"),
        (np.zeros((1, 3)), {"stride_m": 0.0}, "stride_m"),
        (
            np.zeros((1, 3)),
            {"window_size_m": 1.0, "stride_m": 2.0},
            "stride_m.*window_size_m",
        ),
        (np.zeros((1, 3)), {"model_points": 0}, "model_points"),
        (np.zeros((1, 3)), {"query_points": 0}, "query_points"),
        (
            np.zeros((1, 3)),
            {"model_points": 4, "query_points": 5},
            "query_points.*model_points",
        ),
    ],
)
def test_predict_tiled_rejects_invalid_input_and_parameters(
    points: np.ndarray, kwargs: dict[str, Any], match: str
):
    defaults: dict[str, Any] = {
        "window_size_m": 1.0,
        "stride_m": 1.0,
        "model_points": 8,
        "query_points": 4,
        "seed": 0,
    }
    defaults.update(kwargs)

    with pytest.raises(ValueError, match=match):
        predict_tiled(points, lambda batch: np.zeros((len(batch), 2)), **defaults)


@pytest.mark.parametrize(
    "bad_logits",
    [
        np.zeros((7, 2)),
        np.zeros((8, 3)),
        np.full((8, 2), np.nan),
    ],
)
def test_predict_tiled_rejects_invalid_model_logits(bad_logits: np.ndarray):
    points = np.array([[0.0, 0.0, 0.0]])

    with pytest.raises(ValueError, match=r"finite.*\(8, 2\)|\(8, 2\).*finite"):
        predict_tiled(
            points,
            lambda batch: bad_logits,
            window_size_m=1.0,
            stride_m=1.0,
            model_points=8,
            query_points=4,
            seed=0,
        )


def test_pointnet_logits_preserves_normalized_point_order_and_never_calls_tlsep(monkeypatch):
    torch = pytest.importorskip("torch")
    points = np.linspace(-0.9, 0.9, 512 * 3, dtype=np.float32).reshape(512, 3)
    seen: list[np.ndarray] = []

    class FakeModel:
        def __call__(self, batch):
            seen.append(batch.squeeze(0).cpu().numpy().copy())
            point_ids = torch.arange(batch.shape[1], dtype=torch.float32)
            return torch.stack([point_ids, -point_ids], dim=-1).unsqueeze(0)

    segmenter = WoodLeafSegmenter(backend="pointnet")
    segmenter._model = FakeModel()
    segmenter._device = "cpu"
    segmenter._torch = torch
    monkeypatch.setattr(
        segmenter,
        "_segment_tlsep",
        lambda unused: pytest.fail("pointnet_logits must never call tlsep"),
    )

    logits = segmenter.pointnet_logits(points)

    assert np.array_equal(seen[0], points)
    assert np.array_equal(logits[:, 0], np.arange(512, dtype=np.float32))
    assert np.array_equal(logits[:, 1], -np.arange(512, dtype=np.float32))


def test_pointnet_logits_requires_pointnet_backend_and_minimum_size(monkeypatch):
    points = np.zeros((512, 3), dtype=np.float32)
    with pytest.raises(ValueError, match="backend='pointnet'"):
        WoodLeafSegmenter(backend="tlsep").pointnet_logits(points)

    segmenter = WoodLeafSegmenter(backend="pointnet")
    monkeypatch.setattr(
        segmenter,
        "_segment_tlsep",
        lambda unused: pytest.fail("pointnet_logits must never call tlsep"),
    )
    with pytest.raises(ValueError, match="at least 512"):
        segmenter.pointnet_logits(points[:511])


@pytest.mark.parametrize("kind", ["shape", "nonfinite"])
def test_pointnet_logits_rejects_invalid_model_output(kind: str):
    torch = pytest.importorskip("torch")

    class FakeModel:
        def __call__(self, batch):
            if kind == "shape":
                return torch.zeros((1, batch.shape[1], 3))
            return torch.full((1, batch.shape[1], 2), torch.nan)

    segmenter = WoodLeafSegmenter(backend="pointnet")
    segmenter._model = FakeModel()
    segmenter._device = "cpu"
    segmenter._torch = torch

    with pytest.raises(ValueError, match=r"finite.*\(512, 2\)|\(512, 2\).*finite"):
        segmenter.pointnet_logits(np.zeros((512, 3), dtype=np.float32))


def test_pointnet_checkpoint_load_uses_weights_only(monkeypatch):
    torch = pytest.importorskip("torch")
    from training import pointnet2_seg

    load_calls: list[tuple[str, dict[str, Any]]] = []

    class FakeModel:
        def __init__(self, num_classes: int):
            assert num_classes == 2

        def load_state_dict(self, state_dict):
            assert state_dict == {"weight": "fixture"}

        def to(self, device):
            assert device == "cpu"
            return self

        def eval(self):
            return self

    def fake_load(path: str, **kwargs):
        load_calls.append((path, kwargs))
        return {"state_dict": {"weight": "fixture"}, "num_classes": 2}

    monkeypatch.setattr(torch, "load", fake_load)
    monkeypatch.setattr(pointnet2_seg, "PointNet2SegSSG", FakeModel)

    segmenter = WoodLeafSegmenter(
        model_path="fixture-checkpoint.pt", backend="pointnet", device="cpu"
    )
    segmenter.load()

    assert load_calls == [
        ("fixture-checkpoint.pt", {"map_location": "cpu", "weights_only": True})
    ]
