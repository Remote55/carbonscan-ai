"""Generate system architecture + user flow diagrams for the NSC Proposal.

Run from services/ml/ with the venv active:
    python notebooks/make_diagrams.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# Use a Thai-capable font (Tahoma is bundled with Windows, supports Thai + Latin
# without needing an external download). Falls back to DejaVu Sans for emoji
# glyphs the chosen font may not have.
_thai_capable = [
    "Tahoma",
    "Leelawadee UI",
    "Microsoft Sans Serif",
    "Sarabun",
    "Noto Sans Thai",
]
_available = {f.name for f in font_manager.fontManager.ttflist}
_picked = next((f for f in _thai_capable if f in _available), None)
if _picked:
    plt.rcParams["font.family"] = _picked
    plt.rcParams["font.sans-serif"] = [_picked, "DejaVu Sans"]
    print(f"[font] using {_picked} for Thai+Latin")
else:
    print("[font] no Thai-capable font found; sticking with default")

# Output: docs/proposal/figures/
FIG_DIR = Path(__file__).resolve().parents[3] / "docs" / "proposal" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Brand colors (consistent with apps/web Tailwind config + Flutter app_colors.dart)
FOREST_700 = "#1B4332"
FOREST_500 = "#2D6A4F"
FOREST_300 = "#7CC59A"
SKY_500 = "#74C0FC"
SAND = "#FAFAF8"
STONE = "#5C5C52"
CHARCOAL = "#14140F"
ERROR = "#E63946"


# ----------------------------------------------------------------------------
# Figure 9 — System Architecture
# ----------------------------------------------------------------------------


def _box(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    *,
    color: str = FOREST_500,
    text_color: str = "white",
    fontsize: int = 11,
    bold: bool = True,
):
    """Draw a rounded box with a label."""
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.05,rounding_size=0.15",
        facecolor=color,
        edgecolor=color,
        linewidth=2,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2,
        y + h / 2,
        label,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=text_color,
        fontweight=("bold" if bold else "normal"),
    )


def _arrow(ax, x1, y1, x2, y2, *, color=STONE, label: str | None = None, mutation=15):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="->",
            mutation_scale=mutation,
            color=color,
            linewidth=1.6,
        )
    )
    if label:
        ax.text(
            (x1 + x2) / 2,
            (y1 + y2) / 2 + 0.15,
            label,
            ha="center",
            fontsize=8,
            color=color,
            style="italic",
        )


def make_architecture():
    """v3 — LiDAR-primary architecture, layout cleaned up.

    Each of the 4 layers gets a dedicated y-band with explicit padding so
    nothing overlaps. Banner labels live in a gutter row above each layer
    instead of inside the layer rectangle.
    """
    fig, ax = plt.subplots(figsize=(15, 13))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 14)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # ----- Layer Y bands -----
    #   gutter_top : label above each layer
    #   bg_top/bot : the tinted background rectangle
    #   inside_top/bot: where boxes live
    layers = [
        # name           bg_color   bg_bot bg_top   label_y    boxes_bot boxes_top
        ("[1]  INPUT LAYER",                                "#F0F9F4", 10.8, 13.0, 13.1,  11.0, 12.5),
        ("[2]  WEB  /  API GATEWAY",                        "#E9F5EE",  8.8, 10.4, 10.5,   9.0, 10.0),
        ("[3]  PROCESSING  —  ML PIPELINE + DATABASE",      "#FAFAF8",  3.6,  8.4,  8.5,   3.9,  8.0),
        ("[4]  OUTPUT  —  3 deliverables to the user",      "#FFF8E7",  0.3,  3.2,  3.3,   0.6,  2.6),
    ]
    for label, color, bg_bot, bg_top, label_y, *_ in layers:
        ax.add_patch(mpatches.Rectangle(
            (0, bg_bot), 15, bg_top - bg_bot,
            facecolor=color, edgecolor="none", zorder=0))
        ax.text(0.2, label_y, label, fontsize=10, color=STONE, fontweight="bold")

    # ===========================  INPUT LAYER  ===========================
    # LiDAR — BIG, PRIMARY  (left 8 of 15)
    _box(
        ax, 0.5, 11.0, 8.0, 1.5,
        "LiDAR Upload   (PRIMARY)\nTLS · Drone · ALS\n.las / .laz / .ply   (up to 500 MB)",
        color=FOREST_500, fontsize=12,
    )

    # Mobile — SMALLER, SECONDARY  (right 5.5)
    _box(
        ax, 9.0, 11.0, 5.5, 1.5,
        "Mobile Photogrammetry\n(optional, smallholder)\n30 JPG  →  COLMAP  →  .ply",
        color=FOREST_300, text_color=CHARCOAL, fontsize=10,
    )

    # Sub-captions sit in the small gap between INPUT background and GATEWAY background
    ax.text(4.5, 10.62, "Auditor / Carbon Survey — for plots ≥ 1 rai",
            ha="center", fontsize=9, color=STONE, style="italic")
    ax.text(11.75, 10.62, "Community / smallholder farmer (<1 ไร่)",
            ha="center", fontsize=9, color=STONE, style="italic")

    # ===========================  GATEWAY  ===========================
    _box(
        ax, 0.5, 9.0, 7.0, 1.0,
        "Web Dashboard (Next.js 14)\nUpload UI · 3D Viewer · GIS Map · Marketplace",
        color=SKY_500, text_color=CHARCOAL, fontsize=11,
    )
    _box(
        ax, 7.9, 9.0, 6.6, 1.0,
        "FastAPI Service (Railway)\n/upload · /jobs · /trees · /marketplace · WebSocket",
        color=SKY_500, text_color=CHARCOAL, fontsize=11,
    )

    # ===========================  PROCESSING  ===========================
    # Database — leftmost full-height column
    _box(
        ax, 0.5, 3.9, 4.0, 4.1,
        "Supabase\n\nPostgreSQL 16 + PostGIS\nStorage  +  Auth  +  RLS",
        color=FOREST_700, fontsize=12,
    )
    ax.text(2.5, 4.3,
            "trees · plots · jobs\ntransactions · audit_log",
            ha="center", fontsize=9, color="white", style="italic")

    # Center column: Queue (top) + COLMAP (below)
    _box(
        ax, 4.8, 6.5, 3.4, 1.5,
        "Job Queue\n(Supabase PGMQ)",
        color=STONE, fontsize=11,
    )
    _box(
        ax, 4.8, 3.9, 3.4, 2.0,
        "COLMAP  +  OpenMVS\n\nPhotogrammetry Worker\n(photo path only)\n30 JPG  →  .ply",
        color=FOREST_300, text_color=CHARCOAL, fontsize=10,
    )

    # Right column: GPU Worker (top) + ML pipeline detail (below)
    _box(
        ax, 8.5, 6.5, 6.0, 1.5,
        "RunPod Serverless GPU\nPyTorch · Open3D · PDAL",
        color=ERROR, fontsize=12,
    )
    ax.add_patch(FancyBboxPatch(
        (8.5, 3.9), 6.0, 2.2,
        boxstyle="round,pad=0.05,rounding_size=0.1",
        facecolor="white", edgecolor=ERROR, linewidth=1.6, linestyle="--",
    ))
    ax.text(11.5, 5.7, "ML Pipeline  (8 stages)",
            ha="center", va="center", fontsize=11, color=ERROR, fontweight="bold")
    pipeline_text = (
        "1.  Ground classification\n"
        "2.  Height normalization\n"
        "3.  Canopy Height Model\n"
        "4.  Individual Tree Detection\n"
        "5.  Wood / Leaf segmentation\n"
        "6.  QSM  (DBH · Height · Volume)\n"
        "7.  Species classification\n"
        "8.  TGO Allometric  →  Carbon"
    )
    ax.text(11.5, 4.65, pipeline_text,
            ha="center", va="center", fontsize=8.5, color=CHARCOAL, family="monospace")

    # ===========================  OUTPUT  ===========================
    _box(
        ax, 0.5, 0.7, 4.3, 1.8,
        "Verified Carbon\nCertificate (PDF)\n\nTGO 2017 aligned",
        color=FOREST_700, fontsize=12,
    )
    _box(
        ax, 5.2, 0.7, 4.6, 1.8,
        "B2B Marketplace\nชุมชน  <->  โรงงาน\n\nCBAM / ESG offset",
        color=FOREST_500, fontsize=12,
    )
    _box(
        ax, 10.2, 0.7, 4.3, 1.8,
        "GIS Map  +  Audit Log\nGPS dedup · multi-temporal\n\n(Additionality tracking)",
        color=SKY_500, text_color=CHARCOAL, fontsize=12,
    )

    # ===========================  Arrows  ===========================
    # INPUT  →  GATEWAY  (single converging arrow each)
    _arrow(ax, 4.5, 11.0, 4.0, 10.0, mutation=14)
    _arrow(ax, 11.75, 11.0, 11.2, 10.0, mutation=14)

    # Web  <->  API gateway (horizontal twin)
    _arrow(ax, 7.5, 9.6, 7.9, 9.6, mutation=12)
    _arrow(ax, 7.9, 9.4, 7.5, 9.4, mutation=12)

    # API  →  Queue  +  API  ↔  DB
    _arrow(ax, 11.2, 9.0, 6.5, 8.0, mutation=14)   # API → Queue
    _arrow(ax, 7.9,  9.0, 4.5, 8.0, mutation=14)   # API → DB

    # Queue  →  GPU  &  Queue  →  COLMAP
    _arrow(ax, 8.2, 7.2, 8.5, 7.2, mutation=12)
    _arrow(ax, 6.5, 6.5, 6.5, 5.9, mutation=12)

    # COLMAP  →  GPU  (photo path → ML pipeline)
    _arrow(ax, 8.2, 4.9, 8.5, 6.5, mutation=12)

    # PROCESSING  →  OUTPUT  (3 fan-out arrows)
    _arrow(ax, 2.5, 3.9, 2.5, 2.6, mutation=14)
    _arrow(ax, 7.5, 3.9, 7.5, 2.6, mutation=14)
    _arrow(ax, 12.0, 3.9, 12.0, 2.6, mutation=14)

    # ===========================  Title  ===========================
    ax.text(7.5, 13.6, "Figure 9 — CarbonScan AI System Architecture (v2)",
            ha="center", fontsize=16, fontweight="bold", color=CHARCOAL)
    ax.text(7.5, 13.27,
            "LiDAR-primary input  ·  End-to-end pipeline  ·  Tri-output (Certificate / Marketplace / Audit)",
            ha="center", fontsize=10, color=STONE, style="italic")

    plt.savefig(FIG_DIR / "fig09_architecture.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"+ Saved {FIG_DIR / 'fig09_architecture.png'}")


# ----------------------------------------------------------------------------
# Figure 10 — User Journey (Mobile → Cloud → Result)
# ----------------------------------------------------------------------------


def make_user_flow():
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    steps = [
        ("1", "Open\nMobile App", 0.8, FOREST_300),
        ("2", "Pre-scan\nChecklist", 2.4, FOREST_300),
        ("3", "Capture\n30-50 photos\n+ GPS", 4.0, FOREST_500),
        ("4", "Upload\nto Cloud", 5.6, SKY_500),
        ("5", "Photogrammetry\n(.ply)", 7.2, ERROR),
        ("6", "ML Pipeline\n8 steps", 8.8, ERROR),
        ("7", "Carbon\nResult", 10.4, FOREST_700),
        ("8", "Marketplace\n(B2B)", 12.0, FOREST_700),
    ]

    y = 3.5
    for num, label, x, color in steps:
        # Numbered circle
        circle = plt.Circle((x, y + 1.2), 0.32, facecolor=color, edgecolor="white", linewidth=2.5, zorder=3)
        ax.add_patch(circle)
        ax.text(x, y + 1.2, num, ha="center", va="center", color="white", fontsize=13, fontweight="bold", zorder=4)
        # Label
        ax.text(x, y - 0.3, label, ha="center", va="center", fontsize=9.5, color=CHARCOAL)

    # Connection line under circles
    ax.plot([0.8, 12.0], [y + 1.2, y + 1.2], color=STONE, linewidth=2, alpha=0.4, zorder=1)

    # Phase brackets (group steps)
    def _phase(x1, x2, label, color, y_pos):
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (x1 - 0.5, y_pos),
                x2 - x1 + 1.0,
                0.45,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor=color,
                edgecolor=color,
                alpha=0.18,
            )
        )
        ax.text((x1 + x2) / 2, y_pos + 0.22, label, ha="center", va="center", fontsize=10, color=CHARCOAL, fontweight="bold")

    _phase(0.8, 4.0, "📱 ON DEVICE  (Mobile, ~2 min)", FOREST_500, 6.2)
    _phase(5.6, 8.8, "☁️  IN THE CLOUD  (~10-15 min)", ERROR, 6.2)
    _phase(10.4, 12.0, "💰 IN MARKET", FOREST_700, 6.2)

    # Key annotations under each phase
    ax.text(2.4, 1.2, "GPS embedded\nin every photo\n(EXIF + 6 decimals)", ha="center", fontsize=8.5, color=STONE, style="italic")
    ax.text(7.2, 1.2, "AI segments wood vs leaf,\nfits cylinders, applies\nTGO allometric equation", ha="center", fontsize=8.5, color=STONE, style="italic")
    ax.text(11.2, 1.2, "Factories buy carbon\ncredits with full\n3D + GPS evidence", ha="center", fontsize=8.5, color=STONE, style="italic")

    # Title
    ax.text(6.5, 6.85, "Figure 10 — User Journey (Path A: Community → Marketplace)", ha="center", fontsize=15, fontweight="bold", color=CHARCOAL)

    plt.savefig(FIG_DIR / "fig10_user_flow.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"✓ Saved {FIG_DIR / 'fig10_user_flow.png'}")


if __name__ == "__main__":
    make_architecture()
    make_user_flow()
    print(f"\nBoth diagrams saved to: {FIG_DIR}")
