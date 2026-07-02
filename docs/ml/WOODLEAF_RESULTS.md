# Wood/Leaf Segmentation — Results Log

> เก็บผลทุก variant (ตามคำแนะนำอาจารย์ "เก็บผลไว้ทุกแบบ แม้ผลจะไม่ดี").
> ทุกตัวเลขเป็น IoU บนชุดทดสอบที่ระบุ (held-out, กันข้อมูลรั่วแบบ spatial สำหรับ Wan).

## Synthetic (held-out synthetic test)
| method | wood IoU | leaf IoU | mean IoU |
|---|---|---|---|
| PCA heuristic (`tlsep`) | 0.769 | – | – |
| PointNet++ (`pointnet`) | 0.978 | – | – |

## Real TLS — Wan 2021 (held-out, spatial split + buffer)

### Prior runs (synthetic-trained → real)
| run | init | augment | class-weight | wood IoU | leaf IoU | mean IoU |
|---|---|---|---|---|---|---|
| zero-shot | synthetic-only | – | – | ~0.18 | ~0.62 | ~0.33 |
| fine-tune | synthetic ckpt | – | none | ~0.19 | ~0.63 | ~0.41 |
| fine-tune + CW | synthetic ckpt | – | auto | ~0.24 | ~0.07 | ~0.16 |

### Same-environment matrix (bigger Wan data, from-scratch) — Colab run 2026-06-29
Held-out = spatial split + buffer (leakage-free); numbers are pooled per-point IoU.
| # | init | augment-synthetic | class-weight | #train tiles | wood IoU | leaf IoU | mean IoU | accuracy |
|---|---|---|---|---|---|---|---|---|
| 1 | scratch | 0 | none | 339 | 0.285 | 0.803 | 0.544 | 0.817 |
| 2 | scratch | 0 | auto | 339 | 0.381 | 0.790 | 0.585 | 0.814 |
| **3** ⭐ | scratch | 200 | none | 539 | **0.418** | **0.808** | **0.613** | **0.831** |
| 4 | scratch | 200 | auto | 539 | 0.332 | 0.770 | 0.551 | 0.793 |

**Best: variant 3** (from-scratch + synthetic augmentation, no class-weight) — wins on every metric.

### Findings
- **Same-environment training works.** Training directly on real Wan (vs synthetic→transfer)
  lifted mean IoU from ~0.41 to **0.61** and wood IoU from ~0.19 to **0.42** (best variant).
- **Synthetic augmentation helps** (advisor's suggestion): v1→v3 wood IoU 0.285 → 0.418.
- **Class-weight helps only without augmentation** (v1→v2: 0.285 → 0.381) but *hurts* once
  augmentation already balances the classes (v4 auto weights ≈ 1.0/1.0, and mean drops vs v3).
- Wood IoU (0.42) still below the 0.70 target — the remaining gap needs more labelled real
  data, especially in-country Thai species (field-data collection, next phase).

### Honest reporting arc (for the report)
synthetic test **0.978** → real zero-shot **0.33** → train-on-real same-environment + augment
**mean 0.61 / wood 0.42** → (roadmap) Thai field data to close the rest.
