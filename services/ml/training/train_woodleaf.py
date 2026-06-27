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
from training.woodleaf_dataset import WOOD, build_woodleaf_dataset


def _make_loader(n_samples, n_points, seed0, batch_size, shuffle):
    x, y = build_woodleaf_dataset(n_samples=n_samples, n_points=n_points, seed0=seed0)
    ds = TensorDataset(torch.from_numpy(x), torch.from_numpy(y))
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)


def _npz_loader(path, batch_size, shuffle):
    """Loader from a converter .npz holding x:(N,P,3) float32 + y:(N,P) int64."""
    data = np.load(path)
    x = data["x"].astype(np.float32)
    y = data["y"].astype(np.int64)
    ds = TensorDataset(torch.from_numpy(x), torch.from_numpy(y))
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)


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


def train(args) -> float:
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[train] device={device}")

    if args.train_npz:
        if not args.val_npz:
            raise SystemExit("--val-npz is required when --train-npz is given")
        print(f"[train] real data: train={args.train_npz}  val/held-out={args.val_npz}")
        train_loader = _npz_loader(args.train_npz, args.batch_size, True)
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
            loss = F.cross_entropy(logits, y.reshape(-1))
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
    return p


if __name__ == "__main__":
    train(build_arg_parser().parse_args())
