"""Deterministic tiled inference for fixed-size PointNet++ models."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from training.woodleaf_dataset import normalize_points


@dataclass(frozen=True)
class TiledPrediction:
    """Per-point predictions accumulated across overlapping XY windows."""

    labels: np.ndarray
    logits: np.ndarray
    coverage: np.ndarray


def _validate_parameters(
    points: np.ndarray,
    *,
    window_size_m: float,
    stride_m: float,
    model_points: int,
    query_points: int,
    seed: int,
) -> np.ndarray:
    try:
        validated = np.asarray(points, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("points must be a finite (N, 3) array") from exc
    if validated.ndim != 2 or validated.shape[1] != 3:
        raise ValueError(f"points must be a finite (N, 3) array, got {validated.shape}")
    if len(validated) == 0:
        raise ValueError("points must contain at least one row")
    if not np.all(np.isfinite(validated)):
        raise ValueError("points must be a finite (N, 3) array")

    if not np.isfinite(window_size_m) or window_size_m <= 0:
        raise ValueError("window_size_m must be finite and positive")
    if not np.isfinite(stride_m) or stride_m <= 0:
        raise ValueError("stride_m must be finite and positive")
    if stride_m > window_size_m:
        raise ValueError("stride_m must be less than or equal to window_size_m")
    if (
        isinstance(model_points, (bool, np.bool_))
        or not isinstance(model_points, (int, np.integer))
        or model_points <= 0
    ):
        raise ValueError("model_points must be a positive integer")
    if (
        isinstance(query_points, (bool, np.bool_))
        or not isinstance(query_points, (int, np.integer))
        or query_points <= 0
    ):
        raise ValueError("query_points must be a positive integer")
    if query_points > model_points:
        raise ValueError("query_points must be less than or equal to model_points")
    if (
        isinstance(seed, (bool, np.bool_))
        or not isinstance(seed, (int, np.integer))
        or seed < 0
    ):
        raise ValueError("seed must be a non-negative integer")
    return validated


def _axis_starts(axis: np.ndarray, window_size_m: float, stride_m: float) -> np.ndarray:
    axis_min = float(axis.min())
    span = float(axis.max()) - axis_min
    extra_steps = int(np.ceil(max(0.0, span - window_size_m) / stride_m))
    return axis_min + np.arange(extra_steps + 1, dtype=np.float64) * stride_m


def _context_indices(
    window_indices: np.ndarray,
    query_start: int,
    query_stop: int,
    context_count: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if context_count == 0:
        return np.empty(0, dtype=np.int64)

    remaining = np.concatenate(
        [window_indices[:query_start], window_indices[query_stop:]]
    )
    if len(remaining) >= context_count:
        return rng.choice(remaining, size=context_count, replace=False)
    if len(remaining) > 0:
        extra = rng.choice(
            remaining,
            size=context_count - len(remaining),
            replace=True,
        )
        return np.concatenate([remaining, extra])

    query = window_indices[query_start:query_stop]
    return rng.choice(query, size=context_count, replace=True)


def predict_tiled(
    points: np.ndarray,
    model_logits: Callable[[np.ndarray], np.ndarray],
    *,
    window_size_m: float = 2.5,
    stride_m: float = 1.25,
    model_points: int = 2048,
    query_points: int = 1024,
    seed: int = 0,
) -> TiledPrediction:
    """Run strict fixed-size PointNet inference over overlapping XY windows.

    Original point indices are kept in stable order within every window. Each
    model batch starts with at most ``query_points`` original points and is
    padded to ``model_points`` with deterministic window context. Only logits
    for the leading query positions are accumulated.
    """
    validated = _validate_parameters(
        points,
        window_size_m=window_size_m,
        stride_m=stride_m,
        model_points=model_points,
        query_points=query_points,
        seed=seed,
    )
    n_points = len(validated)
    logits_sum = np.zeros((n_points, 2), dtype=np.float64)
    coverage = np.zeros(n_points, dtype=np.int64)
    x_starts = _axis_starts(validated[:, 0], window_size_m, stride_m)
    y_starts = _axis_starts(validated[:, 1], window_size_m, stride_m)

    for x_number, x_start in enumerate(x_starts):
        x_inside = (validated[:, 0] >= x_start) & (
            validated[:, 0] <= x_start + window_size_m
        )
        for y_number, y_start in enumerate(y_starts):
            inside = (
                x_inside
                & (validated[:, 1] >= y_start)
                & (validated[:, 1] <= y_start + window_size_m)
            )
            window_indices = np.flatnonzero(inside)
            if len(window_indices) == 0:
                continue
            window_indices = np.sort(window_indices, kind="stable")

            for chunk_number, query_start in enumerate(
                range(0, len(window_indices), query_points)
            ):
                query_stop = min(query_start + query_points, len(window_indices))
                query_indices = window_indices[query_start:query_stop]
                rng = np.random.default_rng(
                    np.random.SeedSequence(
                        [int(seed), x_number, y_number, chunk_number]
                    )
                )
                context = _context_indices(
                    window_indices,
                    query_start,
                    query_stop,
                    model_points - len(query_indices),
                    rng,
                )
                batch_indices = np.concatenate([query_indices, context])
                batch = normalize_points(validated[batch_indices])
                if batch.shape != (model_points, 3):
                    raise RuntimeError(
                        f"internal PointNet batch has shape {batch.shape}, "
                        f"expected ({model_points}, 3)"
                    )

                batch_logits = np.asarray(model_logits(batch), dtype=np.float64)
                expected_shape = (model_points, 2)
                if batch_logits.shape != expected_shape or not np.all(
                    np.isfinite(batch_logits)
                ):
                    raise ValueError(
                        "model_logits must return finite "
                        f"{expected_shape} logits, got shape {batch_logits.shape}"
                    )
                query_count = len(query_indices)
                logits_sum[query_indices] += batch_logits[:query_count]
                coverage[query_indices] += 1

    if np.any(coverage == 0):
        missing = int(np.count_nonzero(coverage == 0))
        raise ValueError(f"PointNet tiled inference left {missing} points uncovered")
    mean_logits = logits_sum / coverage[:, None]
    labels = mean_logits.argmax(axis=1).astype(np.int8)
    return TiledPrediction(labels=labels, logits=mean_logits, coverage=coverage)
