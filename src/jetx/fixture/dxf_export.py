"""Minimal, dependency-free DXF (AutoCAD R12 ASCII) exporter.

Rather than pull in a third-party CAD library, this module writes the DXF
``ENTITIES`` section directly as plain text. DXF R12 ASCII is a
well-documented, simple group-code format, and only three entity types
are needed to represent this bracket's outline:

* ``LINE``   — straight edges,
* ``ARC``    — the four rounded corners,
* ``CIRCLE`` — the bolt holes and clevis bore.

The result opens correctly in any DXF-capable CAD package (AutoCAD,
Fusion 360, SolidWorks, LibreCAD, etc.) — "DXF-compatible sketch" in the
sense of a real, standards-conformant DXF file, not a look-alike text
file with a ``.dxf`` extension.
"""

from __future__ import annotations

import math
from pathlib import Path

from .geometry import BracketGeometry


class DxfWriter:
    """Accumulates DXF entities and serialises them to R12 ASCII group codes."""

    def __init__(self) -> None:
        self._entities: list[str] = []

    def add_line(self, p1: tuple[float, float], p2: tuple[float, float], layer: str = "OUTLINE") -> None:
        self._entities.append(
            "0\nLINE\n8\n{layer}\n10\n{x1}\n20\n{y1}\n30\n0.0\n11\n{x2}\n21\n{y2}\n31\n0.0".format(
                layer=layer, x1=p1[0], y1=p1[1], x2=p2[0], y2=p2[1]
            )
        )

    def add_arc(
        self,
        center: tuple[float, float],
        radius: float,
        start_angle_deg: float,
        end_angle_deg: float,
        layer: str = "OUTLINE",
    ) -> None:
        self._entities.append(
            "0\nARC\n8\n{layer}\n10\n{cx}\n20\n{cy}\n30\n0.0\n40\n{r}\n50\n{a0}\n51\n{a1}".format(
                layer=layer, cx=center[0], cy=center[1], r=radius, a0=start_angle_deg, a1=end_angle_deg
            )
        )

    def add_circle(self, center: tuple[float, float], radius: float, layer: str = "HOLES") -> None:
        self._entities.append(
            "0\nCIRCLE\n8\n{layer}\n10\n{cx}\n20\n{cy}\n30\n0.0\n40\n{r}".format(
                layer=layer, cx=center[0], cy=center[1], r=radius
            )
        )

    def to_string(self) -> str:
        body = "\n".join(self._entities)
        return f"0\nSECTION\n2\nENTITIES\n{body}\n0\nENDSEC\n0\nEOF\n"

    def save(self, output_path: Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_string(), encoding="ascii")
        return output_path


def build_bracket_outline(writer: DxfWriter, geom: BracketGeometry) -> None:
    """Add the rounded-rectangle plate outline (4 lines + 4 corner arcs)."""
    half_l, half_w = geom.length_mm / 2.0, geom.width_mm / 2.0
    r = geom.corner_fillet_radius_mm

    # Straight edges, stopping short of each corner to leave room for the fillet arc.
    writer.add_line((-half_l + r, -half_w), (half_l - r, -half_w))  # bottom
    writer.add_line((half_l, -half_w + r), (half_l, half_w - r))  # right
    writer.add_line((half_l - r, half_w), (-half_l + r, half_w))  # top
    writer.add_line((-half_l, half_w - r), (-half_l, -half_w + r))  # left

    # Corner arcs, centered r-in from each corner, sweeping 90 degrees.
    writer.add_arc((half_l - r, -half_w + r), r, 270, 360)  # bottom-right
    writer.add_arc((half_l - r, half_w - r), r, 0, 90)  # top-right
    writer.add_arc((-half_l + r, half_w - r), r, 90, 180)  # top-left
    writer.add_arc((-half_l + r, -half_w + r), r, 180, 270)  # bottom-left


def build_bracket_dxf(geom: BracketGeometry) -> DxfWriter:
    """Build the complete DXF entity set for a bracket geometry."""
    writer = DxfWriter()
    build_bracket_outline(writer, geom)

    for cx, cy in geom.bolt_hole_centers_mm:
        writer.add_circle((cx, cy), geom.bolt_hole_diameter_mm / 2.0)

    writer.add_circle((0.0, 0.0), geom.clevis_bore_diameter_mm / 2.0)

    return writer


def export_bracket_dxf(geom: BracketGeometry, output_path: Path) -> Path:
    """Build and save the bracket DXF file in one call."""
    writer = build_bracket_dxf(geom)
    return writer.save(output_path)


# Sanity check helper: DXF ARC angles are measured counter-clockwise from
# the positive X axis, in degrees — used only by the unit tests to verify
# the four corner arcs are wired to the correct quadrant/geometry.
def arc_endpoint(center: tuple[float, float], radius: float, angle_deg: float) -> tuple[float, float]:
    angle_rad = math.radians(angle_deg)
    return center[0] + radius * math.cos(angle_rad), center[1] + radius * math.sin(angle_rad)
