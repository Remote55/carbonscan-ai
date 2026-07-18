"""Train the Phase 2 PointNet++ wood-leaf segmentation model.

Designed to run on a free GPU (Google Colab / Kaggle). Training data is
generated on the fly from the synthetic forest generator — no download needed.

Example (Colab):
    !pip install torch
    !python -m training.train_woodleaf --epochs 60 --n-train 256 --out woodleaf_pn2.pt

Goal (Sprint P1 / G2): val wood IoU >= 0.70, compared against the PCA baseline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F  # noqa: N812 (standard PyTorch alias)
from torch.utils.data import DataLoader, TensorDataset

from pipeline.provenance import sha256_file
from training.evidence_training import canonical_state_dict_sha256, set_global_determinism
from training.metrics import iou_score
from training.pointnet2_seg import PointNet2SegSSG
from training.woodleaf_dataset import LEAF, WOOD, build_woodleaf_dataset


def _make_loader(n_samples, n_points, seed0, batch_size, shuffle, *, generator=None):
    x, y = build_woodleaf_dataset(n_samples=n_samples, n_points=n_points, seed0=seed0)
    ds = TensorDataset(torch.from_numpy(x), torch.from_numpy(y))
    return DataLoader(
        ds,
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=0,
    )


def _loader_from_arrays(x, y, batch_size, shuffle, *, generator=None):
    """Wrap numpy arrays in a DataLoader (expects float32 x, int64 y)."""
    ds = TensorDataset(torch.from_numpy(x), torch.from_numpy(y))
    return DataLoader(
        ds,
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=0,
    )


def _npz_loader(path, batch_size, shuffle, *, generator=None):
    """Loader from a converter .npz holding x:(N,P,3) float32 + y:(N,P) int64."""
    data = np.load(path)
    return _loader_from_arrays(
        data["x"].astype(np.float32),
        data["y"].astype(np.int64),
        batch_size,
        shuffle,
        generator=generator,
    )


def _class_weights(labels: np.ndarray, num_classes: int = 2) -> np.ndarray:
    """Inverse-frequency ('balanced') class weights to counter imbalance.

    weight[c] = total / (num_classes * count[c]) — the sklearn 'balanced' rule.
    Up-weights the rare class (wood) so the loss stops ignoring it. Returns
    float32 weights aligned to class index.
    """
    counts = np.bincount(np.asarray(labels).reshape(-1), minlength=num_classes).astype(np.float64)
    counts = np.where(counts == 0, 1.0, counts)  # guard against a missing class
    return (counts.sum() / (num_classes * counts)).astype(np.float32)


def _iou_triple(preds: np.ndarray, gts: np.ndarray) -> tuple[float, float, float]:
    """Pooled per-point (wood_iou, leaf_iou, mean_iou) over flat label arrays."""
    wood = iou_score(preds, gts, positive_class=WOOD)
    leaf = iou_score(preds, gts, positive_class=LEAF)
    return wood, leaf, (wood + leaf) / 2.0


def _augment_with_synthetic(
    x: np.ndarray, y: np.ndarray, n: int, seed: int = 50_000
) -> tuple[np.ndarray, np.ndarray]:
    """Append `n` synthetic samples (matching point count) to a real (npz) set.

    seed0 is set high to avoid overlapping the synthetic train (0) / val (10_000) seeds.
    """
    sx, sy = build_woodleaf_dataset(n_samples=n, n_points=x.shape[1], seed0=seed)
    x_out = np.concatenate([x, sx.astype(np.float32)], axis=0)
    y_out = np.concatenate([y, sy.astype(np.int64)], axis=0)
    return x_out, y_out


@torch.no_grad()
def evaluate(model, loader, device) -> float:
    """Mean wood-class IoU over a loader."""
    model.eval()
    ious = []
    for x, y in loader:
        pred = model(x.to(device)).argmax(dim=-1).cpu().numpy()
        gt = y.numpy()
        for b in range(len(pred)):
            ious.append(iou_score(pred[b], gt[b], positive_class=WOOD))
    return float(np.mean(ious)) if ious else 0.0


@torch.no_grad()
def evaluate_full(model, loader, device) -> dict:
    """Pooled per-point wood/leaf/mean IoU + accuracy over a loader."""
    model.eval()
    preds, gts = [], []
    for x, y in loader:
        p = model(x.to(device)).argmax(dim=-1).cpu().numpy().reshape(-1)
        preds.append(p)
        gts.append(y.numpy().reshape(-1))
    if not preds:
        return {"wood_iou": 0.0, "leaf_iou": 0.0, "mean_iou": 0.0, "accuracy": 0.0}
    pf = np.concatenate(preds)
    gf = np.concatenate(gts)
    wood, leaf, mean = _iou_triple(pf, gf)
    return {
        "wood_iou": float(wood),
        "leaf_iou": float(leaf),
        "mean_iou": float(mean),
        "accuracy": float((pf == gf).mean()),
    }


def train(args) -> dict:
    set_global_determinism(args.seed)
    train_generator = torch.Generator().manual_seed(args.seed)
    dev_generator = torch.Generator().manual_seed(args.seed)
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    if args.train_npz:
        if not args.val_npz:
            raise SystemExit("--val-npz is required when --train-npz is given")
        data = np.load(args.train_npz)
        x = data["x"].astype(np.float32)
        y = data["y"].astype(np.int64)
        if args.augment_synthetic > 0:
            x, y = _augment_with_synthetic(
                x,
                y,
                args.augment_synthetic,
                seed=args.synthetic_seed_start,
            )
        train_loader = _loader_from_arrays(
            x,
            y,
            args.batch_size,
            True,
            generator=train_generator,
        )
        val_loader = _npz_loader(
            args.val_npz,
            args.batch_size,
            False,
            generator=dev_generator,
        )
    else:
        train_loader = _make_loader(
            args.n_train,
            args.n_points,
            0,
            args.batch_size,
            True,
            generator=train_generator,
        )
        val_loader = _make_loader(
            args.n_val,
            args.n_points,
            10_000,
            args.batch_size,
            False,
            generator=dev_generator,
        )

    model = PointNet2SegSSG(num_classes=2).to(device)
    if args.init_checkpoint:
        ckpt = torch.load(
            args.init_checkpoint,
            map_location=device,
            weights_only=True,
        )
        model.load_state_dict(ckpt["state_dict"])
    weight = None
    if args.class_weight == "auto":
        w = _class_weights(train_loader.dataset.tensors[1].numpy(), num_classes=2)
        weight = torch.tensor(w, device=device)

    opt = torch.optim.Adam(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    sched = torch.optim.lr_scheduler.StepLR(
        opt,
        step_size=args.scheduler_step,
        gamma=args.scheduler_gamma,
    )

    best_iou = -1.0  # ensure a checkpoint is always saved (even if early IoU is 0)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, args.epochs + 1):
        model.train()
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            logits = model(x).reshape(-1, 2)
            loss = F.cross_entropy(logits, y.reshape(-1), weight=weight)
            opt.zero_grad()
            loss.backward()
            opt.step()
        sched.step()
        final_metrics = evaluate_full(model, val_loader, device)
        val_iou = evaluate(model, val_loader, device)
        if val_iou > best_iou:
            best_iou = val_iou
            checkpoint = {
                "schema_version": "2",
                "state_dict": model.state_dict(),
                "num_classes": 2,
                "seed": args.seed,
                "selected_epoch": epoch,
                "dev_metrics": final_metrics,
                "protocol_sha256": args.protocol_sha256,
                "wan_manifest_sha256": args.wan_manifest_sha256,
                "training_git_commit": args.training_git_commit,
            }
            torch.save(
                checkpoint,
                out_path,
            )

    best_ckpt = torch.load(
        out_path,
        map_location=device,
        weights_only=True,
    )
    model.load_state_dict(best_ckpt["state_dict"])
    return {
        "seed": args.seed,
        "best_epoch": best_ckpt["selected_epoch"],
        "best_macro_tile_wood_iou": float(best_iou),
        "dev_metrics": best_ckpt["dev_metrics"],
        "state_dict_sha256": canonical_state_dict_sha256(best_ckpt["state_dict"]),
        "checkpoint_sha256": sha256_file(out_path),
        "checkpoint_path": str(out_path),
        "protocol_sha256": args.protocol_sha256,
        "wan_manifest_sha256": args.wan_manifest_sha256,
        "training_git_commit": args.training_git_commit,
    }


def _presentation_summary(record: dict) -> dict:
    return {
        "seed": record["seed"],
        "best_epoch": record["best_epoch"],
        "best_macro_tile_wood_iou": round(record["best_macro_tile_wood_iou"], 4),
        "checkpoint_file": Path(record["checkpoint_path"]).name,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train PointNet++ wood-leaf segmenter")
    p.add_argument("--n-train", type=int, default=256)
    p.add_argument("--n-val", type=int, default=48)
    p.add_argument("--n-points", type=int, default=2048)
    p.add_argument("--epochs", type=int, default=60)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--scheduler-step", type=int, default=20)
    p.add_argument("--scheduler-gamma", type=float, default=0.5)
    p.add_argument("--device", type=str, default="auto")
    p.add_argument("--out", type=str, default="woodleaf_pn2.pt")
    p.add_argument("--seed", type=int, default=20260716)
    p.add_argument("--protocol-sha256", required=True)
    p.add_argument("--wan-manifest-sha256", required=True)
    p.add_argument("--training-git-commit", required=True)
    # Real-data fine-tuning (overrides the synthetic generator when given)
    p.add_argument("--train-npz", type=str, default=None,
                   help="real training samples .npz (x,y); overrides synthetic")
    p.add_argument("--val-npz", type=str, default=None,
                   help="real held-out test samples .npz (x,y)")
    p.add_argument("--init-checkpoint", type=str, default=None,
                   help="checkpoint to fine-tune from (e.g. the synthetic woodleaf_pn2.pt)")
    p.add_argument("--class-weight", choices=["none", "auto"], default="none",
                   help="auto = inverse-frequency weighted loss (lifts the minority wood class)")
    p.add_argument("--augment-synthetic", type=int, default=0,
                   help="add N synthetic samples to the (npz) training set as augmentation")
    p.add_argument("--synthetic-seed-start", type=int, default=50_000)
    return p


if __name__ == "__main__":
    result = train(build_arg_parser().parse_args())
    print(json.dumps(_presentation_summary(result), ensure_ascii=True, separators=(",", ":")))
