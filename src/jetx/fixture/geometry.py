"""Parametric geometry for the load-cell mounting bracket.

The bracket is a flat rectangular plate with:

* four corner bolt holes (mounts the bracket to the fixed test-stand frame),
* a central clevis bore (pins to the load cell body),
* filleted corners (stress-concentration relief — a sharp corner is the
  single most common place a fatigue crack initiates in a bolted plate).

All dimensions are stored in millimetres (the standard convention for a
mechanical detail drawing) and derived properties (area, hole positions,
mass) are computed from them, so changing one parameter (e.g. plate
thickness) automatically propagates to the drawing, DXF export and BOM
mass estimate — the point of keeping this parametric rather than a fixed
set of numbers baked into a drawing.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MaterialProperties:
    """Minimal material property set needed for a first-pass strength/mass check."""

    name: str
    density_kg_m3: float
    yield_strength_mpa: float
    ultimate_strength_mpa: float


# Al 6061-T6: good strength-to-weight, widely available, easy to machine —
# the default choice for a non-flight, ground-test-stand bracket. See
# docs/engineering_theory.md for the material-selection trade study.
AL_6061_T6 = MaterialProperties(
    name="Aluminum 6061-T6", density_kg_m3=2700.0, yield_strength_mpa=276.0, ultimate_strength_mpa=310.0
)
STEEL_4130 = MaterialProperties(
    name="Steel 4130 (normalized)", density_kg_m3=7850.0, yield_strength_mpa=460.0, ultimate_strength_mpa=670.0
)


@dataclass(frozen=True)
class BracketGeometry:
    """Parametric definition of the load-cell mounting bracket.

    Parameters
    ----------
    length_mm, width_mm, thickness_mm:
        Overall plate envelope.
    corner_fillet_radius_mm:
        Fillet radius applied to all four plate corners.
    bolt_hole_diameter_mm:
        Clearance-hole diameter for the four corner mounting bolts.
    bolt_hole_edge_margin_mm:
        Distance from each plate edge to the centre of the nearest bolt
        hole (standard practice: >= 2x hole diameter, to keep enough
        material around the hole to avoid edge tear-out).
    clevis_bore_diameter_mm:
        Central through-bore diameter, sized to the load cell's clevis pin.
    material:
        :class:`MaterialProperties` used for the mass estimate.
    """

    length_mm: float = 120.0
    width_mm: float = 80.0
    thickness_mm: float = 12.0
    corner_fillet_radius_mm: float = 8.0
    bolt_hole_diameter_mm: float = 8.5  # clearance for M8 bolt
    bolt_hole_edge_margin_mm: float = 17.0
    clevis_bore_diameter_mm: float = 20.0
    material: MaterialProperties = field(default_factory=lambda: AL_6061_T6)

    def __post_init__(self) -> None:
        if self.bolt_hole_edge_margin_mm < self.bolt_hole_diameter_mm:
            raise ValueError("bolt_hole_edge_margin_mm must be >= bolt_hole_diameter_mm")
        min_dim = min(self.length_mm, self.width_mm)
        if self.corner_fillet_radius_mm >= min_dim / 2.0:
            raise ValueError("corner_fillet_radius_mm too large for the plate envelope")

    @property
    def bolt_hole_centers_mm(self) -> tuple[tuple[float, float], ...]:
        """(x, y) centre coordinates of the four corner bolt holes, plate-centred origin."""
        half_l = self.length_mm / 2.0 - self.bolt_hole_edge_margin_mm
        half_w = self.width_mm / 2.0 - self.bolt_hole_edge_margin_mm
        return (
            (-half_l, -half_w),
            (half_l, -half_w),
            (half_l, half_w),
            (-half_l, half_w),
        )

    @property
    def plate_area_mm2(self) -> float:
        """Plate area, corrected for four corner fillets and all cut-outs.

        Each fillet removes a corner square of side r and replaces it with
        a quarter circle, i.e. removes ``r^2 * (1 - pi/4)`` per corner.
        """
        gross_area = self.length_mm * self.width_mm
        fillet_loss = 4.0 * self.corner_fillet_radius_mm**2 * (1.0 - 3.141592653589793 / 4.0)
        bolt_hole_area = 4.0 * 3.141592653589793 / 4.0 * self.bolt_hole_diameter_mm**2
        clevis_area = 3.141592653589793 / 4.0 * self.clevis_bore_diameter_mm**2
        return gross_area - fillet_loss - bolt_hole_area - clevis_area

    @property
    def mass_kg(self) -> float:
        """Estimated part mass from net area x thickness x material density."""
        volume_mm3 = self.plate_area_mm2 * self.thickness_mm
        volume_m3 = volume_mm3 * 1e-9
        return volume_m3 * self.material.density_kg_m3

    @property
    def bearing_area_mm2(self) -> float:
        """Bearing (projected) area at the clevis bore: diameter x plate thickness.

        Used for a first-pass bearing-stress check on the clevis pin
        interface: sigma_bearing = F / (d * t).
        """
        return self.clevis_bore_diameter_mm * self.thickness_mm

    def bearing_stress_mpa(self, applied_load_n: float) -> float:
        """First-pass bearing stress at the clevis bore for a given applied load.

            sigma_bearing = F / (d_bore * t)

        This is a simple projected-area bearing check, standard for a
        first-pass pin-joint sizing estimate (Shigley's *Mechanical
        Engineering Design*, ch. on pin/clevis joints); it does not
        replace a full FEA or a fatigue analysis, both flagged as future
        work.
        """
        area_mm2 = self.bearing_area_mm2
        stress_n_mm2 = applied_load_n / area_mm2  # N/mm^2 == MPa
        return stress_n_mm2

    def safety_factor(self, applied_load_n: float) -> float:
        """Safety factor against yield at the clevis bearing interface."""
        return self.material.yield_strength_mpa / self.bearing_stress_mpa(applied_load_n)
