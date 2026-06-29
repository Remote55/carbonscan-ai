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

### Same-environment matrix (bigger Wan data, from-scratch) — fill from Colab `[held-out]` line
| # | init | augment-synthetic | class-weight | #train tiles | wood IoU | leaf IoU | mean IoU |
|---|---|---|---|---|---|---|---|
| 1 | scratch | 0 | none | _ | _ | _ | _ |
| 2 | scratch | 0 | auto | _ | _ | _ | _ |
| 3 | scratch | 200 | none | _ | _ | _ | _ |
| 4 | scratch | 200 | auto | _ | _ | _ | _ |

> วิธีกรอก: รันแต่ละ variant บน Colab (ดู docs/ml/FINETUNE_REALDATA.md) แล้วก็อปเลขจากบรรทัด
> `[held-out] wood_iou=... leaf_iou=... mean_iou=...` มาใส่ในแถวที่ตรงกัน
