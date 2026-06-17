"""PointNet++ (SSG) semantic segmentation network — Phase 2 wood-leaf model.

A compact, self-contained PyTorch implementation of PointNet++ single-scale
grouping for per-point segmentation (Qi et al. 2017, NeurIPS). Pure PyTorch —
no custom CUDA ops — so it runs on a free Colab/Kaggle GPU (or CPU for tests).

Input : (B, N, 3) XYZ point clouds (normalised to the unit sphere)
Output: (B, N, num_classes) per-point logits

This is the `backend="pointnet"` model behind pipeline.wood_leaf_separation.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812 (standard PyTorch alias)


def square_distance(src: torch.Tensor, dst: torch.Tensor) -> torch.Tensor:
    """Pairwise squared distances. src (B,N,3), dst (B,M,3) -> (B,N,M)."""
    B, N, _ = src.shape
    M = dst.shape[1]
    dist = -2 * torch.matmul(src, dst.permute(0, 2, 1))
    dist += torch.sum(src**2, -1).view(B, N, 1)
    dist += torch.sum(dst**2, -1).view(B, 1, M)
    return dist


def index_points(points: torch.Tensor, idx: torch.Tensor) -> torch.Tensor:
    """Gather points by index. points (B,N,C), idx (B,S) or (B,S,K)."""
    B = points.shape[0]
    view_shape = [B, *([1] * (idx.dim() - 1))]
    repeat_shape = [1, *idx.shape[1:]]
    batch_indices = (
        torch.arange(B, dtype=torch.long, device=points.device)
        .view(view_shape)
        .repeat(repeat_shape)
    )
    return points[batch_indices, idx, :]


def farthest_point_sample(xyz: torch.Tensor, npoint: int) -> torch.Tensor:
    """Iterative farthest point sampling. xyz (B,N,3) -> idx (B,npoint)."""
    device = xyz.device
    B, N, _ = xyz.shape
    centroids = torch.zeros(B, npoint, dtype=torch.long, device=device)
    distance = torch.ones(B, N, device=device) * 1e10
    farthest = torch.randint(0, N, (B,), dtype=torch.long, device=device)
    batch_indices = torch.arange(B, dtype=torch.long, device=device)
    for i in range(npoint):
        centroids[:, i] = farthest
        centroid = xyz[batch_indices, farthest, :].view(B, 1, 3)
        dist = torch.sum((xyz - centroid) ** 2, -1)
        distance = torch.minimum(distance, dist)
        farthest = torch.max(distance, -1)[1]
    return centroids


def query_ball_point(
    radius: float, nsample: int, xyz: torch.Tensor, new_xyz: torch.Tensor
) -> torch.Tensor:
    """Group up to nsample neighbours within radius. -> idx (B,S,nsample)."""
    device = xyz.device
    B, N, _ = xyz.shape
    S = new_xyz.shape[1]
    group_idx = (
        torch.arange(N, dtype=torch.long, device=device)
        .view(1, 1, N)
        .repeat(B, S, 1)
    )
    sqrdists = square_distance(new_xyz, xyz)
    group_idx[sqrdists > radius**2] = N
    group_idx = group_idx.sort(dim=-1)[0][:, :, :nsample]
    # Replace out-of-range fills with the nearest (first) neighbour
    group_first = group_idx[:, :, 0].view(B, S, 1).repeat(1, 1, nsample)
    mask = group_idx == N
    group_idx[mask] = group_first[mask]
    return group_idx


class SetAbstraction(nn.Module):
    """Sampling + grouping + PointNet (single-scale grouping)."""

    def __init__(self, npoint, radius, nsample, in_channel, mlp):
        super().__init__()
        self.npoint = npoint
        self.radius = radius
        self.nsample = nsample
        self.mlp_convs = nn.ModuleList()
        self.mlp_bns = nn.ModuleList()
        last = in_channel + 3  # + relative xyz
        for out in mlp:
            self.mlp_convs.append(nn.Conv2d(last, out, 1))
            self.mlp_bns.append(nn.BatchNorm2d(out))
            last = out

    def forward(self, xyz, features):
        """xyz (B,N,3), features (B,N,C) or None -> new_xyz (B,S,3), feat (B,S,mlp[-1])."""
        B = xyz.shape[0]
        fps_idx = farthest_point_sample(xyz, self.npoint)
        new_xyz = index_points(xyz, fps_idx)
        idx = query_ball_point(self.radius, self.nsample, xyz, new_xyz)
        grouped_xyz = index_points(xyz, idx) - new_xyz.view(B, self.npoint, 1, 3)
        if features is not None:
            grouped_feat = index_points(features, idx)
            grouped = torch.cat([grouped_xyz, grouped_feat], dim=-1)
        else:
            grouped = grouped_xyz
        # (B, S, nsample, C+3) -> (B, C+3, nsample, S)
        grouped = grouped.permute(0, 3, 2, 1)
        for conv, bn in zip(self.mlp_convs, self.mlp_bns, strict=True):
            grouped = F.relu(bn(conv(grouped)))
        new_features = torch.max(grouped, 2)[0]  # (B, mlp[-1], S)
        return new_xyz, new_features.permute(0, 2, 1)


class FeaturePropagation(nn.Module):
    """Interpolate coarse features back to finer points (3-NN inverse-dist)."""

    def __init__(self, in_channel, mlp):
        super().__init__()
        self.mlp_convs = nn.ModuleList()
        self.mlp_bns = nn.ModuleList()
        last = in_channel
        for out in mlp:
            self.mlp_convs.append(nn.Conv1d(last, out, 1))
            self.mlp_bns.append(nn.BatchNorm1d(out))
            last = out

    def forward(self, xyz1, xyz2, feat1, feat2):
        """Propagate feat2@xyz2 onto xyz1; concat with feat1. -> (B,N1,mlp[-1])."""
        B, N, _ = xyz1.shape
        dists = square_distance(xyz1, xyz2)
        dists, idx = dists.sort(dim=-1)
        dists, idx = dists[:, :, :3], idx[:, :, :3]
        dist_recip = 1.0 / (dists + 1e-8)
        weight = dist_recip / torch.sum(dist_recip, dim=2, keepdim=True)
        interp = torch.sum(index_points(feat2, idx) * weight.view(B, N, 3, 1), dim=2)
        new_feat = torch.cat([feat1, interp], dim=-1) if feat1 is not None else interp
        new_feat = new_feat.permute(0, 2, 1)  # (B, C, N)
        for conv, bn in zip(self.mlp_convs, self.mlp_bns, strict=True):
            new_feat = F.relu(bn(conv(new_feat)))
        return new_feat.permute(0, 2, 1)


class PointNet2SegSSG(nn.Module):
    """PointNet++ SSG segmentation head for wood/leaf (default 2 classes)."""

    def __init__(self, num_classes: int = 2):
        super().__init__()
        self.sa1 = SetAbstraction(512, 0.1, 32, in_channel=0, mlp=[32, 32, 64])
        self.sa2 = SetAbstraction(128, 0.2, 32, in_channel=64, mlp=[64, 64, 128])
        self.sa3 = SetAbstraction(32, 0.4, 32, in_channel=128, mlp=[128, 128, 256])
        self.fp3 = FeaturePropagation(256 + 128, [256, 128])
        self.fp2 = FeaturePropagation(128 + 64, [128, 64])
        self.fp1 = FeaturePropagation(64, [64, 64])
        self.head = nn.Sequential(
            nn.Conv1d(64, 64, 1), nn.BatchNorm1d(64), nn.ReLU(),
            nn.Dropout(0.5), nn.Conv1d(64, num_classes, 1),
        )

    def forward(self, xyz: torch.Tensor) -> torch.Tensor:
        """xyz (B, N, 3) -> logits (B, N, num_classes)."""
        l0_xyz = xyz
        l1_xyz, l1_feat = self.sa1(l0_xyz, None)
        l2_xyz, l2_feat = self.sa2(l1_xyz, l1_feat)
        l3_xyz, l3_feat = self.sa3(l2_xyz, l2_feat)
        l2_feat = self.fp3(l2_xyz, l3_xyz, l2_feat, l3_feat)
        l1_feat = self.fp2(l1_xyz, l2_xyz, l1_feat, l2_feat)
        l0_feat = self.fp1(l0_xyz, l1_xyz, None, l1_feat)
        logits = self.head(l0_feat.permute(0, 2, 1))  # (B, num_classes, N)
        return logits.permute(0, 2, 1)
