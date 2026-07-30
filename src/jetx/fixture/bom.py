"""Bill of materials for the load-cell mounting bracket assembly."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .geometry import BracketGeometry


def build_bom(geom: BracketGeometry) -> pd.DataFrame:
    """Return the assembly BOM as a tidy DataFrame (one row per line item).

    Fastener sizes are picked to match the geometry's bolt clearance hole
    (M8 clearance -> M8 socket-head cap screws) and clevis bore (a
    standard clevis pin + retaining clips), so the BOM stays consistent if
    the geometry parameters change.
    """
    rows = [
        {
            "item": 1,
            "part_number": "JX-FIX-001",
            "description": "Load Cell Mounting Bracket",
            "qty": 1,
            "material": geom.material.name,
            "unit_mass_kg": round(geom.mass_kg, 4),
            "source": "Machined in-house",
        },
        {
            "item": 2,
            "part_number": "DIN 912 - M8x25",
            "description": "Socket Head Cap Screw, M8 x 1.25 x 25mm, Class 12.9",
            "qty": 4,
            "material": "Alloy Steel, Zinc-Plated",
            "unit_mass_kg": 0.021,
            "source": "COTS (McMaster-Carr / Fastenal)",
        },
        {
            "item": 3,
            "part_number": "DIN 125 - M8",
            "description": "Flat Washer, M8",
            "qty": 4,
            "material": "Steel, Zinc-Plated",
            "unit_mass_kg": 0.003,
            "source": "COTS",
        },
        {
            "item": 4,
            "part_number": "DIN 985 - M8",
            "description": "Nylon-Insert Locknut, M8 x 1.25",
            "qty": 4,
            "material": "Steel, Zinc-Plated",
            "unit_mass_kg": 0.005,
            "source": "COTS",
        },
        {
            "item": 5,
            "part_number": f"CLEVIS-PIN-{geom.clevis_bore_diameter_mm:.0f}MM",
            "description": f"Clevis Pin, ⌀{geom.clevis_bore_diameter_mm:.1f}mm, with retaining clips",
            "qty": 1,
            "material": "Steel 4130, Hardened",
            "unit_mass_kg": 0.045,
            "source": "COTS (load-cell manufacturer accessory kit)",
        },
    ]
    df = pd.DataFrame(rows)
    df["extended_mass_kg"] = (df["qty"] * df["unit_mass_kg"]).round(4)
    return df


def save_bom_csv(geom: BracketGeometry, output_path: Path) -> Path:
    """Build and save the BOM as CSV; returns the output path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    build_bom(geom).to_csv(output_path, index=False)
    return output_path


MATERIAL_SELECTION_NOTES: str = """\
MATERIAL SELECTION -- Load Cell Mounting Bracket

Candidates considered: Aluminum 6061-T6, Steel 4130 (normalized), Stainless 303.

Selected: Aluminum 6061-T6
  + Strength-to-weight: 276 MPa yield at 2700 kg/m^3 gives the best
    yield-strength-per-unit-mass of the three candidates, and this is a
    hand-carried test-cell fixture where mass matters for setup time.
  + Machinability: excellent (rated ~90% of the 2011-T3 machinability
    baseline), keeps in-house fabrication turnaround short.
  + Corrosion resistance: naturally passivating oxide layer is adequate
    for an indoor, climate-controlled test-cell environment (no plating
    required).
  + Cost and lead time: readily available as plate stock in the required
    thickness range.
  - Lower absolute strength than steel -> the safety-factor check in
    geometry.BracketGeometry.safety_factor() must be re-run any time the
    expected load changes, and drives the minimum plate thickness.

Steel 4130 would be selected instead if:
  - the expected load exceeds what a reasonable 6061-T6 thickness can
    carry at the target safety factor, or
  - the bracket needs to survive repeated impact/mishandling on an
    outdoor or unconditioned test stand.
"""

MANUFACTURING_NOTES: str = """\
MANUFACTURING NOTES -- Load Cell Mounting Bracket (JX-FIX-001)

Process:  3-axis CNC milling from 1/2" (12.7mm) 6061-T6 plate stock,
          or waterjet/laser blank + drill/ream for the two precision
          bores (bolt clearance holes can be waterjet-cut directly;
          the clevis bore should be reamed to size after cutting to hold
          a tighter tolerance on the pin fit).

Sequence (concept-level, not a released process sheet):
  1. Cut/mill plate to length_mm x width_mm gross blank.
  2. Mill four corner fillets (R = corner_fillet_radius_mm).
  3. Drill + ream central clevis bore to clevis_bore_diameter_mm,
     H7 fit class if a snug pin fit is required.
  4. Drill four corner bolt clearance holes.
  5. Deburr all edges and holes; break sharp corners 0.5mm x 45deg.
  6. Bead-blast or as-machined finish (no plating required for 6061-T6
     in an indoor test-cell environment).

Tolerances (concept-level defaults, see title block on the drawing):
  Linear:  +/-0.13 mm unless noted
  Angular: +/-0.5 deg
  Clevis bore: tighten to +0.02/-0.00 mm if pin slop must be minimized
     for load-cell alignment accuracy.

Inspection: verify clevis bore diameter and the four-bolt-hole pattern
  (position tolerance) with CMM or pin gauges before first assembly.
"""
