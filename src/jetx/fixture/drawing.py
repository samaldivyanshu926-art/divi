"""Dimensioned 2D engineering drawing of the bracket, rendered with matplotlib.

Produces a two-view concept sketch (top view + side/thickness view) with
dimension lines, hole callouts and a title block — the level of detail
expected of a hand concept sketch that precedes formal CAD, not a
production drawing (no GD&T frames, no tolerance stack-up). Both PDF and
SVG are native matplotlib output formats, so no extra CAD library is
needed to produce either.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

from .geometry import BracketGeometry

plt.rcParams.update({"font.size": 8, "font.family": "monospace"})


def _dimension_line(ax, p1: tuple[float, float], p2: tuple[float, float], text: str, offset: float = 0.0) -> None:
    """Draw a double-headed dimension arrow between p1 and p2 with a centred label."""
    ax.annotate(
        "",
        xy=p2,
        xytext=p1,
        arrowprops=dict(arrowstyle="<->", color="tab:blue", lw=0.8),
    )
    mid = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0 + offset)
    ax.text(mid[0], mid[1], text, ha="center", va="center", fontsize=7, color="tab:blue",
             bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))


def _draw_top_view(ax, geom: BracketGeometry) -> None:
    half_l, half_w = geom.length_mm / 2.0, geom.width_mm / 2.0
    r = geom.corner_fillet_radius_mm

    plate = FancyBboxPatch(
        (-half_l + r, -half_w + r),
        geom.length_mm - 2 * r,
        geom.width_mm - 2 * r,
        boxstyle=f"round,pad=0,rounding_size={r}",
        linewidth=1.4,
        edgecolor="black",
        facecolor="#e8eef7",
    )
    ax.add_patch(plate)

    for cx, cy in geom.bolt_hole_centers_mm:
        ax.add_patch(Circle((cx, cy), geom.bolt_hole_diameter_mm / 2.0, fc="white", ec="black", lw=1.0))
        ax.plot([cx - 4, cx + 4], [cy, cy], color="black", lw=0.4)
        ax.plot([cx, cx], [cy - 4, cy + 4], color="black", lw=0.4)

    ax.add_patch(Circle((0, 0), geom.clevis_bore_diameter_mm / 2.0, fc="white", ec="black", lw=1.4))
    ax.plot([-geom.clevis_bore_diameter_mm, geom.clevis_bore_diameter_mm], [0, 0], color="black", lw=0.4)
    ax.plot([0, 0], [-geom.clevis_bore_diameter_mm, geom.clevis_bore_diameter_mm], color="black", lw=0.4)

    _dimension_line(ax, (-half_l, half_w + 14), (half_l, half_w + 14), f"{geom.length_mm:.1f}")
    _dimension_line(ax, (half_l + 14, -half_w), (half_l + 14, half_w), f"{geom.width_mm:.1f}")
    _dimension_line(
        ax,
        (0, 0),
        (geom.clevis_bore_diameter_mm / 2.0, 0),
        f"⌀{geom.clevis_bore_diameter_mm:.1f} CLEVIS BORE",
        offset=6,
    )
    bx, by = geom.bolt_hole_centers_mm[1]
    _dimension_line(
        ax, (half_l, by), (bx, by), f"{geom.bolt_hole_edge_margin_mm:.1f}", offset=-6
    )
    ax.text(
        bx, by - 10, f"4x ⌀{geom.bolt_hole_diameter_mm:.1f}\nCLEARANCE", ha="center", va="top", fontsize=6.5
    )
    ax.text(-half_l + r * 0.6, -half_w + r * 0.6, f"R{r:.1f} TYP\n4 PLACES", fontsize=6.5, ha="left", va="bottom")

    ax.set_xlim(-half_l - 30, half_l + 30)
    ax.set_ylim(-half_w - 30, half_w + 30)
    ax.set_aspect("equal")
    ax.set_title("TOP VIEW", fontsize=9, fontweight="bold")
    ax.axis("off")


def _draw_side_view(ax, geom: BracketGeometry) -> None:
    half_l = geom.length_mm / 2.0
    t = geom.thickness_mm

    ax.add_patch(
        plt.Rectangle((-half_l, 0), geom.length_mm, t, linewidth=1.4, edgecolor="black", facecolor="#e8eef7")
    )
    for cx, _ in geom.bolt_hole_centers_mm[:2]:
        ax.plot([cx, cx], [-6, t + 6], color="black", lw=0.4, ls="--")

    _dimension_line(ax, (half_l + 14, 0), (half_l + 14, t), f"{t:.1f}", offset=0)
    _dimension_line(ax, (-half_l, -14), (half_l, -14), f"{geom.length_mm:.1f}")

    ax.set_xlim(-half_l - 30, half_l + 30)
    ax.set_ylim(-30, t + 20)
    ax.set_aspect("equal")
    ax.set_title("SIDE VIEW (THICKNESS)", fontsize=9, fontweight="bold")
    ax.axis("off")


def _draw_title_block(ax, geom: BracketGeometry, part_name: str, drawing_number: str) -> None:
    ax.axis("off")
    lines = [
        f"PART:        {part_name}",
        f"DWG NO:      {drawing_number}      REV: A",
        f"MATERIAL:    {geom.material.name}",
        f"MASS (est.): {geom.mass_kg * 1000:.1f} g",
        "UNITS:       mm   |   SCALE: NTS   |   PROJECTION: 3rd angle",
        "FINISH:      as-machined, deburr all edges",
        "TOLERANCES:  +/-0.13 mm (linear, unless noted) | +/-0.5 deg (angular)",
        "STATUS:      CONCEPT SKETCH -- not released for manufacture",
    ]
    ax.text(0.0, 1.0, "\n".join(lines), transform=ax.transAxes, fontsize=7.5, va="top", family="monospace")


def render_bracket_drawing(
    geom: BracketGeometry,
    output_path: Path,
    part_name: str = "Load Cell Mounting Bracket",
    drawing_number: str = "JX-FIX-001",
) -> Path:
    """Render the two-view dimensioned drawing and save it to ``output_path``.

    The output format (PDF or SVG) is taken from ``output_path``'s
    extension — both are native matplotlib backends.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(11, 8.5))
    grid = fig.add_gridspec(2, 2, height_ratios=[3, 1])
    ax_top = fig.add_subplot(grid[0, 0])
    ax_side = fig.add_subplot(grid[0, 1])
    ax_title = fig.add_subplot(grid[1, :])

    _draw_top_view(ax_top, geom)
    _draw_side_view(ax_side, geom)
    _draw_title_block(ax_title, geom, part_name, drawing_number)

    fig.suptitle(f"{part_name} — Concept Sketch", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    fig.savefig(output_path)
    plt.close(fig)
    return output_path
