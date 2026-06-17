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
    print(f"+ Saved {FIG_DIR / 'fig10_user_flow.png'}")


# ----------------------------------------------------------------------------
# Figure 14 — System at a Glance (simplified, for non-technical readers)
# ----------------------------------------------------------------------------


def make_system_simplified():
    """3-block INPUT -> AI -> OUTPUT diagram.

    Deliberately minimal so a reader understands the whole system in ~5 sec
    (addresses reviewer feedback: explain system design simply via a diagram).
    """
    fig, ax = plt.subplots(figsize=(14, 5.4))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5.4)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    _box(
        ax, 0.4, 1.4, 3.8, 2.6,
        "1.  ข้อมูลเข้า\n(INPUT)\n\nไฟล์ LiDAR\n.las / .laz / .ply\n— หรือ —\nภาพถ่ายมือถือ 30+ รูป",
        color=FOREST_500, fontsize=12,
    )
    _box(
        ax, 5.1, 1.4, 3.8, 2.6,
        "2.  ประมวลผลด้วย AI\n(AI PIPELINE)\n\nML Pipeline 8 ขั้น\nบน Cloud GPU\n(~10–15 นาที/แปลง)",
        color=ERROR, fontsize=12,
    )
    _box(
        ax, 9.8, 1.4, 3.8, 2.6,
        "3.  ผลลัพธ์\n(OUTPUT)\n\n- ใบรับรองคาร์บอน (PDF)\n- ตลาดซื้อขาย B2B\n- แผนที่ GIS + Audit",
        color=SKY_500, text_color=CHARCOAL, fontsize=12,
    )

    _arrow(ax, 4.3, 2.7, 5.0, 2.7, mutation=28)
    _arrow(ax, 9.0, 2.7, 9.7, 2.7, mutation=28)

    ax.text(7.0, 4.85, "Figure 14 — CarbonScan AI: ระบบใน 1 ภาพ (System at a Glance)",
            ha="center", fontsize=16, fontweight="bold", color=CHARCOAL)
    ax.text(7.0, 4.45,
            "เปลี่ยน LiDAR point cloud  ->  carbon credit ที่ผ่านการตรวจสอบ พร้อมซื้อขาย",
            ha="center", fontsize=11, color=STONE, style="italic")
    ax.text(7.0, 0.65,
            "ผู้ใช้หลัก: Auditor / ผู้รับเหมา carbon survey (LiDAR)   ·   ผู้ใช้รอง: เกษตรกรรายย่อย (มือถือ)   ·   ผู้ซื้อ: โรงงาน CBAM/ESG",
            ha="center", fontsize=9, color=STONE)

    plt.savefig(FIG_DIR / "fig14_system_simplified.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"+ Saved {FIG_DIR / 'fig14_system_simplified.png'}")


# ----------------------------------------------------------------------------
# Figure 15 — "Processing" screen wireframe (async UX for long-running jobs)
# ----------------------------------------------------------------------------


def make_processing_ux():
    """Wireframe of the 'Processing' screen.

    Shows how the UI handles a long-running (10-15 min) LiDAR job: named
    8-stage progress, overall % + ETA, and a clear 'you can leave, we'll
    notify you' message (addresses reviewer feedback: LiDAR processing takes
    a long time, design appropriate UX).
    """
    fig, ax = plt.subplots(figsize=(8.6, 10.6))
    ax.set_xlim(0, 8.6)
    ax.set_ylim(0, 10.6)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # screen frame
    ax.add_patch(FancyBboxPatch(
        (0.6, 0.5), 7.4, 9.3,
        boxstyle="round,pad=0.05,rounding_size=0.25",
        facecolor=SAND, edgecolor=STONE, linewidth=2))

    # header
    ax.add_patch(FancyBboxPatch(
        (0.6, 8.6), 7.4, 1.2,
        boxstyle="round,pad=0.05,rounding_size=0.25",
        facecolor=FOREST_700, edgecolor=FOREST_700))
    ax.text(4.3, 9.35, "กำลังประมวลผล Point Cloud", ha="center", va="center",
            fontsize=14, color="white", fontweight="bold")
    ax.text(4.3, 8.95, "งาน #J-2026-0142  ·  teak_plot_chiangmai.las (212 MB)",
            ha="center", va="center", fontsize=9, color="#CFE6D8")

    # overall progress bar
    ax.text(1.0, 8.18, "ความคืบหน้ารวม", fontsize=10, color=CHARCOAL, fontweight="bold")
    ax.text(7.6, 8.18, "62%", ha="right", fontsize=11, color=ERROR, fontweight="bold")
    ax.add_patch(mpatches.Rectangle((1.0, 7.78), 6.6, 0.28, facecolor="#E5E5DF", edgecolor="none"))
    ax.add_patch(mpatches.Rectangle((1.0, 7.78), 6.6 * 0.62, 0.28, facecolor=FOREST_500, edgecolor="none"))

    # 8 named stages
    stages = [
        ("1. อ่านไฟล์ & ตรวจสอบรูปแบบ", "done"),
        ("2. แยกพื้นดิน (Ground Classification)", "done"),
        ("3. ปรับความสูง (Height Normalization)", "done"),
        ("4. สร้างแบบจำลองเรือนยอด (CHM)", "done"),
        ("5. แยกต้นไม้ทีละต้น (Tree Detection)", "current"),
        ("6. แยกใบ / ลำต้น (Wood-Leaf)", "pending"),
        ("7. วัด DBH · ความสูง · ปริมาตร (QSM)", "pending"),
        ("8. คำนวณคาร์บอน (TGO Allometric)", "pending"),
    ]
    y = 7.15
    for label, st in stages:
        if st == "done":
            mcol, mark, tcol = FOREST_500, "✓", CHARCOAL
        elif st == "current":
            mcol, mark, tcol = ERROR, "", ERROR
        else:
            mcol, mark, tcol = "#B7B7AE", "", STONE
        filled = st != "pending"
        ax.add_patch(plt.Circle((1.3, y), 0.17,
                     facecolor=(mcol if filled else "white"),
                     edgecolor=mcol, linewidth=2, zorder=3))
        if mark:
            ax.text(1.3, y, mark, ha="center", va="center", fontsize=10,
                    color="white", zorder=4, fontweight="bold")
        extra = "   <- กำลังทำ (62%)" if st == "current" else ""
        ax.text(1.75, y, label + extra, va="center", fontsize=10.5, color=tcol,
                fontweight=("bold" if st == "current" else "normal"))
        y -= 0.6

    # ETA
    ax.add_patch(FancyBboxPatch((1.0, 1.7), 6.6, 0.8,
        boxstyle="round,pad=0.05,rounding_size=0.15",
        facecolor="#FFF8E7", edgecolor="#E0C97A", linewidth=1.5))
    ax.text(4.3, 2.1, "เหลือเวลาประมาณ ~6 นาที", ha="center", va="center",
            fontsize=12, color=CHARCOAL, fontweight="bold")

    # leave + notify note
    ax.add_patch(FancyBboxPatch((1.0, 0.8), 6.6, 0.75,
        boxstyle="round,pad=0.05,rounding_size=0.15",
        facecolor="#E9F5EE", edgecolor=FOREST_300, linewidth=1.5))
    ax.text(4.3, 1.18,
            "ปิดหน้านี้ได้เลย — ระบบจะแจ้งเตือน (อีเมล / แจ้งเตือนในแอป) เมื่อเสร็จ\nและดูผลย้อนหลังได้จากหน้า 'งานของฉัน' เสมอ",
            ha="center", va="center", fontsize=9.5, color=FOREST_700)

    ax.text(4.3, 10.3, "Figure 15 — UX หน้าจอ 'กำลังประมวลผล' (Async Processing)",
            ha="center", fontsize=13, fontweight="bold", color=CHARCOAL)

    plt.savefig(FIG_DIR / "fig15_processing_ux.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"+ Saved {FIG_DIR / 'fig15_processing_ux.png'}")


if __name__ == "__main__":
    make_architecture()
    make_user_flow()
    make_system_simplified()
    make_processing_ux()
    print(f"\nAll diagrams saved to: {FIG_DIR}")
