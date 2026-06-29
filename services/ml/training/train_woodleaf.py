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
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F  # noqa: N812 (standard PyTorch alias)
from torch.utils.data import DataLoader, TensorDataset

from training.metrics import iou_score
from training.pointnet2_seg import PointNet2SegSSG
from training.woodleaf_dataset import LEAF, WOOD, build_woodleaf_dataset


def _make_loader(n_samples, n_points, seed0, batch_size, shuffle):
    x, y = build_woodleaf_dataset(n_samples=n_samples, n_points=n_points, seed0=seed0)
    ds = TensorDataset(torch.from_numpy(x), torch.from_numpy(y))
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)


def _loader_from_arrays(x, y, batch_size, shuffle):
    """Wrap numpy arrays in a DataLoader (expects float32 x, int64 y)."""
    ds = TensorDataset(torch.from_numpy(x), torch.from_numpy(y))
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)


def _npz_loader(path, batch_size, shuffle):
    """Loader from a converter .npz holding x:(N,P,3) float32 + y:(N,P) int64."""
    data = np.load(path)
    return _loader_from_arrays(
        data["x"].astype(np.float32), data["y"].astype(np.int64), batch_size, shuffle
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
        "wood_iou": round(wood, 4),
        "leaf_iou": round(leaf, 4),
        "mean_iou": round(mean, 4),
        "accuracy": round(float((pf == gf).mean()), 4),
    }


def train(args) -> float:
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[train] device={device}")

    if args.train_npz:
        if not args.val_npz:
            raise SystemExit("--val-npz is required when --train-npz is given")
        data = np.load(args.train_npz)
        x = data["x"].astype(np.float32)
        y = data["y"].astype(np.int64)
        if args.augment_synthetic > 0:
            x, y = _augment_with_synthetic(x, y, args.augment_synthetic)
            print(f"[train] augmented with {args.augment_synthetic} synthetic samples")
        print(f"[train] real data: train={args.train_npz} ({len(x)} samples)  "
              f"val/held-out={args.val_npz}")
        train_loader = _loader_from_arrays(x, y, args.batch_size, True)
        val_loader = _npz_loader(args.val_npz, args.batch_size, False)
    else:
        train_loader = _make_loader(args.n_train, args.n_points, 0, args.batch_size, True)
        val_loader = _make_loader(args.n_val, args.n_points, 10_000, args.batch_size, False)

    model = PointNet2SegSSG(num_classes=2).to(device)
    if args.init_checkpoint:
        ckpt = torch.load(args.init_checkpoint, map_location=device)
        model.load_state_dict(ckpt["state_dict"])
        print(f"[train] fine-tuning from {args.init_checkpoint} "
              f"(prior val_iou={ckpt.get('val_iou')})")
    weight = None
    if args.class_weight == "auto":
        w = _class_weights(train_loader.dataset.tensors[1].numpy(), num_classes=2)
        weight = torch.tensor(w, device=device)
        print(f"[train] class-weighted loss (auto, on training set): "
              f"wood={w[WOOD]:.3f} leaf={w[LEAF]:.3f}")

    opt = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.StepLR(opt, step_size=20, gamma=0.5)

    best_iou = -1.0  # ensure a checkpoint is always saved (even if early IoU is 0)
    out_path = Path(args.out)
    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            logits = model(x).reshape(-1, 2)
            loss = F.cross_entropy(logits, y.reshape(-1), weight=weight)
            opt.zero_grad()
            loss.backward()
            opt.step()
            running += loss.item()
        sched.step()
        val_iou = evaluate(model, val_loader, device)
        print(f"[epoch {epoch:3d}] loss={running/len(train_loader):.4f}  val_wood_IoU={val_iou:.4f}")
        if val_iou > best_iou:
            best_iou = val_iou
            torch.save(
                {"state_dict": model.state_dict(), "num_classes": 2, "val_iou": best_iou},
                out_path,
            )
            print(f"  + saved checkpoint (IoU {best_iou:.4f}) -> {out_path}")

    print(f"[done] best val wood IoU = {best_iou:.4f}  (target >= 0.70)")
    best_ckpt = torch.load(out_path, map_location=device)
    model.load_state_dict(best_ckpt["state_dict"])
    final = evaluate_full(model, val_loader, device)
    print(f"[held-out] wood_iou={final['wood_iou']} leaf_iou={final['leaf_iou']} "
          f"mean_iou={final['mean_iou']} accuracy={final['accuracy']}")
    print("  (note: held-out split is spatially disjoint from train; "
          "also used for best-epoch selection)")
    return best_iou


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train PointNet++ wood-leaf segmenter")
    p.add_argument("--n-train", type=int, default=256)
    p.add_argument("--n-val", type=int, default=48)
    p.add_argument("--n-points", type=int, default=2048)
    p.add_argument("--epochs", type=int, default=60)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--device", type=str, default="auto")
    p.add_argument("--out", type=str, default="woodleaf_pn2.pt")
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
    return p


if __name__ == "__main__":
    train(build_arg_parser().parse_args())
