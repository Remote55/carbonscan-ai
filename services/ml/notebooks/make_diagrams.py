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
    """v2 — LiDAR-primary architecture diagram.

    Layout intentionally emphasizes LiDAR as the main input path and
    Mobile photogrammetry as an optional 'smallholder' fallback, then
    funnels both through the same software platform to a tri-output of
    Certificate + Marketplace + Audit log.
    """
    fig, ax = plt.subplots(figsize=(14, 10.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 11.5)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#FAFAF8")

    # === Layer banners ===
    def banner(y_top, y_bot, label, color):
        ax.add_patch(
            mpatches.Rectangle((0, y_bot), 14, y_top - y_bot, facecolor=color, edgecolor="none", zorder=0)
        )
        ax.text(0.2, y_top - 0.18, label, fontsize=9, color=STONE, fontweight="bold")

    banner(10.9, 8.6, "[1]  INPUT LAYER", "#F0F9F4")
    banner(8.5, 6.9, "[2]  WEB / API GATEWAY", "#E9F5EE")
    banner(6.8, 4.1, "[3]  PROCESSING — ML PIPELINE + DATABASE", "#FAFAF8")
    banner(4.0, 1.4, "[4]  OUTPUT — 3 deliverables to the user", "#FFF8E7")

    # === INPUT LAYER ===
    # LiDAR — BIG, PRIMARY
    _box(
        ax, 0.4, 9.0, 7.5, 1.6,
        "LiDAR Upload  (PRIMARY)\nTLS · Drone · ALS\n.las / .laz / .ply  (up to 500 MB)",
        color=FOREST_500, fontsize=12,
    )
    ax.text(4.1, 8.75, "Auditor / Carbon Survey Contractor — เหมาะกับแปลงใหญ่",
            ha="center", fontsize=9, color=STONE, style="italic")

    # Mobile — SMALLER, SECONDARY
    _box(
        ax, 8.3, 9.0, 5.3, 1.6,
        "Mobile Photogrammetry\n(optional, smallholder)\n30 JPG → COLMAP → .ply",
        color=FOREST_300, text_color=CHARCOAL, fontsize=10,
    )
    ax.text(10.95, 8.75, "ชุมชน / เกษตรกรรายย่อย <1 ไร่",
            ha="center", fontsize=9, color=STONE, style="italic")

    # === WEB / API GATEWAY ===
    _box(
        ax, 0.5, 7.3, 6.5, 1.0,
        "Web Dashboard (Next.js 14)\nUpload UI · 3D Viewer · GIS Map · Marketplace",
        color=SKY_500, text_color=CHARCOAL, fontsize=10.5,
    )
    _box(
        ax, 7.3, 7.3, 6.3, 1.0,
        "FastAPI Service (Railway)\n/upload · /jobs · /trees · /marketplace · WebSocket",
        color=SKY_500, text_color=CHARCOAL, fontsize=10.5,
    )

    # === PROCESSING LAYER ===
    # Database (left)
    _box(
        ax, 0.4, 4.4, 4.0, 2.2,
        "Supabase\nPostgreSQL 16 + PostGIS\nStorage + Auth + RLS",
        color=FOREST_700, fontsize=11,
    )
    ax.text(2.4, 4.65, "trees · plots · jobs · transactions · audit_log",
            ha="center", fontsize=8.5, color="white", style="italic")

    # Queue (center)
    _box(
        ax, 4.7, 5.4, 2.4, 1.2,
        "Job Queue\n(Supabase PGMQ)",
        color=STONE, fontsize=10,
    )
    # Photogrammetry worker (smaller, below queue)
    _box(
        ax, 4.7, 4.4, 2.4, 0.8,
        "COLMAP + OpenMVS\n(photo path only)",
        color=FOREST_300, text_color=CHARCOAL, fontsize=9,
    )

    # GPU Worker (right)
    _box(
        ax, 7.4, 5.4, 6.2, 1.2,
        "RunPod Serverless GPU\nML Pipeline · PyTorch · Open3D",
        color=ERROR, fontsize=11,
    )
    # ML pipeline details
    pipeline_text = (
        "1. Ground  2. Normalize  3. CHM  4. Tree Seg.\n"
        "5. Wood-Leaf  6. QSM (DBH/H/V)  7. Species  8. Allometric"
    )
    ax.add_patch(
        FancyBboxPatch(
            (7.4, 4.3), 6.2, 1.0,
            boxstyle="round,pad=0.05,rounding_size=0.08",
            facecolor="white", edgecolor=ERROR, linewidth=1.5, linestyle="--",
        )
    )
    ax.text(10.5, 4.8, pipeline_text, ha="center", va="center", fontsize=9, color=CHARCOAL, family="monospace")

    # === OUTPUT LAYER ===
    _box(
        ax, 0.5, 2.0, 4.0, 1.6,
        "Verified Carbon\nCertificate (PDF)\nTGO 2017 aligned",
        color=FOREST_700, fontsize=11,
    )
    _box(
        ax, 5.0, 2.0, 4.0, 1.6,
        "B2B Marketplace\nชุมชน ↔ โรงงาน\nCBAM / ESG offset",
        color=FOREST_500, fontsize=11,
    )
    _box(
        ax, 9.5, 2.0, 4.1, 1.6,
        "GIS Map + Audit Log\nGPS dedup · multi-temporal\n(Additionality tracking)",
        color=SKY_500, text_color=CHARCOAL, fontsize=11,
    )

    # === Arrows: top-down flow ===
    # Inputs → Web/API gateway
    _arrow(ax, 4.0, 9.0, 3.5, 8.3, label="upload")
    _arrow(ax, 10.95, 9.0, 10.5, 8.3, label="upload")

    # Web ↔ API
    _arrow(ax, 7.0, 7.8, 7.3, 7.8, mutation=12)
    _arrow(ax, 7.3, 7.6, 7.0, 7.6, mutation=12)

    # API → Queue
    _arrow(ax, 10.5, 7.3, 6.0, 6.6, label="dispatch")

    # API ↔ DB
    _arrow(ax, 7.3, 7.5, 2.4, 6.6)

    # Queue → Worker (GPU)
    _arrow(ax, 7.1, 6.0, 7.4, 6.0, mutation=12)

    # Queue → Photogrammetry
    _arrow(ax, 5.9, 5.4, 5.9, 5.2, mutation=12)

    # Photogrammetry → Worker
    _arrow(ax, 7.1, 4.8, 7.4, 5.4, mutation=12)

    # Worker → Pipeline detail
    _arrow(ax, 10.5, 5.4, 10.5, 5.3, mutation=10)

    # Processing → Outputs
    _arrow(ax, 2.4, 4.4, 2.4, 3.7, label="results")
    _arrow(ax, 7.0, 4.3, 7.0, 3.7)
    _arrow(ax, 11.5, 4.3, 11.5, 3.7)

    # === Title ===
    ax.text(7.0, 11.15, "Figure 9 — CarbonScan AI System Architecture (v2)",
            ha="center", fontsize=16, fontweight="bold", color=CHARCOAL)
    ax.text(7.0, 10.78, "LiDAR-primary input · End-to-end pipeline · Tri-output (Certificate / Marketplace / Audit)",
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
