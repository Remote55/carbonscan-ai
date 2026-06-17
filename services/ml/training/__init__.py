"""Training utilities for Phase 2 PointNet++ wood-leaf segmentation.

Torch-free parts (dataset building, metrics) are importable + testable on any
machine. The model + training loop (pointnet2_seg.py, train_woodleaf.py) require
PyTorch and are intended to run on a free GPU (Google Colab / Kaggle).
"""
