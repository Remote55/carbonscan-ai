"""Generate system architecture + user flow diagrams for the NSC Proposal.

Run from services/ml/ with the venv active:
    python notebooks/make_diagrams.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

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
    fig, ax = plt.subplots(figsize=(13, 8.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9.5)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor(SAND)

    # Layer banner
    ax.text(0.2, 9.0, "CLIENT LAYER", fontsize=9, color=STONE, fontweight="bold")
    ax.add_patch(mpatches.Rectangle((0, 6.6), 13, 2.4, facecolor="#F0F9F4", edgecolor="none", zorder=0))

    ax.text(0.2, 6.3, "API GATEWAY", fontsize=9, color=STONE, fontweight="bold")
    ax.add_patch(mpatches.Rectangle((0, 4.7), 13, 1.6, facecolor="#E9F5EE", edgecolor="none", zorder=0))

    ax.text(0.2, 4.4, "DATA / QUEUE / WORKER LAYER", fontsize=9, color=STONE, fontweight="bold")
    ax.add_patch(mpatches.Rectangle((0, 0.2), 13, 4.2, facecolor="#FAFAF8", edgecolor="none", zorder=0))

    # === Client Layer ===
    # Mobile (Flutter)
    _box(ax, 0.6, 7.4, 4.2, 1.3, "📱 Mobile App (Flutter)\nCamera + GPS + TFLite", color=FOREST_500)
    ax.text(2.7, 7.2, "Android · iOS · Riverpod · go_router", ha="center", fontsize=8, color=STONE)

    # Web (Next.js)
    _box(ax, 8.2, 7.4, 4.2, 1.3, "💻 Web Dashboard (Next.js 14)\n3D Viewer + GIS + Marketplace", color=FOREST_500)
    ax.text(10.3, 7.2, "Three.js · Leaflet · shadcn/ui · TanStack Query", ha="center", fontsize=8, color=STONE)

    # === API Gateway ===
    _box(
        ax,
        2.5,
        5.0,
        8.0,
        1.0,
        "🔌 FastAPI Service (Railway)\n/auth · /upload · /jobs · /trees · /marketplace · WebSocket",
        color=SKY_500,
        text_color=CHARCOAL,
    )

    # === Data Layer ===
    # Database
    _box(
        ax,
        0.5,
        2.7,
        3.8,
        1.5,
        "🗄 Supabase\nPostgreSQL 16 + PostGIS\nStorage + Auth",
        color=FOREST_700,
    )

    # Queue
    _box(ax, 4.7, 3.2, 2.7, 1.0, "📨 Job Queue\n(Supabase PGMQ)", color=STONE)

    # GPU Worker
    _box(
        ax,
        7.8,
        2.7,
        4.6,
        1.5,
        "🤖 RunPod GPU Worker\nML Pipeline (8 steps)\nPyTorch + Open3D + PDAL",
        color=ERROR,
    )

    # Pipeline steps under worker (small box)
    pipeline_text = (
        "1. Ground (CSF)   2. Normalize   3. CHM\n"
        "4. Tree Seg.   5. Wood-Leaf (DL)   6. QSM\n"
        "7. Species (CNN)   8. Allometric → Carbon"
    )
    ax.add_patch(
        FancyBboxPatch(
            (7.8, 0.4),
            4.6,
            2.0,
            boxstyle="round,pad=0.05,rounding_size=0.1",
            facecolor="white",
            edgecolor=ERROR,
            linewidth=1.5,
            linestyle="--",
        )
    )
    ax.text(
        10.1,
        1.4,
        pipeline_text,
        ha="center",
        va="center",
        fontsize=8.5,
        color=CHARCOAL,
        family="monospace",
    )

    # Photogrammetry
    _box(ax, 4.7, 0.5, 2.7, 1.5, "📸 Photogrammetry\nCOLMAP + OpenMVS\n(30-50 JPG → .ply)", color=FOREST_300, text_color=CHARCOAL)

    # === Arrows ===
    # Client → API
    _arrow(ax, 2.7, 7.4, 3.5, 6.0, label="HTTPS")
    _arrow(ax, 10.3, 7.4, 9.5, 6.0, label="HTTPS/WS")

    # API ↔ DB
    _arrow(ax, 4.0, 5.0, 2.5, 4.2)
    _arrow(ax, 2.5, 4.0, 4.0, 4.8, color=FOREST_700)

    # API → Queue
    _arrow(ax, 6.0, 5.0, 6.0, 4.2)

    # Queue → Worker
    _arrow(ax, 7.4, 3.7, 7.8, 3.5)
    _arrow(ax, 7.4, 3.4, 7.4, 1.7)  # Queue → Photogrammetry

    # Worker → Pipeline steps box
    _arrow(ax, 10.1, 2.7, 10.1, 2.4)

    # Photogrammetry → Worker
    _arrow(ax, 7.4, 1.3, 7.8, 3.0)

    # Title + subtitle
    ax.text(6.5, 9.25, "Figure 9 — CarbonScan AI System Architecture", ha="center", fontsize=15, fontweight="bold", color=CHARCOAL)

    plt.savefig(FIG_DIR / "fig09_architecture.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"✓ Saved {FIG_DIR / 'fig09_architecture.png'}")


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
