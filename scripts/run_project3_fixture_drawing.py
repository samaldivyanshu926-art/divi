#!/usr/bin/env python3
"""Project 3 entry point: generate the bracket drawing, DXF and BOM.

Generates:
    figures/project3/bracket_drawing.pdf
    figures/project3/bracket_drawing.svg
    figures/project3/bracket_sketch.png     (quick-look raster preview)
    data/project3/bracket_bom.csv

Usage:
    python scripts/run_project3_fixture_drawing.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from jetx.common.logging_config import get_logger  # noqa: E402
from jetx.fixture import bom, drawing, dxf_export  # noqa: E402
from jetx.fixture.geometry import BracketGeometry  # noqa: E402

logger = get_logger(__name__)

DATA_DIR = REPO_ROOT / "data" / "project3"
FIGURES_DIR = REPO_ROOT / "figures" / "project3"
DOCS_DIR = REPO_ROOT / "docs"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    geom = BracketGeometry()
    logger.info(
        "Bracket geometry: %.0fx%.0fx%.0f mm, mass=%.1f g, plate area=%.0f mm^2",
        geom.length_mm,
        geom.width_mm,
        geom.thickness_mm,
        geom.mass_kg * 1000,
        geom.plate_area_mm2,
    )

    applied_load_n = 5000.0  # representative max test-stand thrust load
    sf = geom.safety_factor(applied_load_n)
    logger.info(
        "Bearing check at clevis bore, F=%.0f N: stress=%.1f MPa, safety factor=%.2f",
        applied_load_n,
        geom.bearing_stress_mpa(applied_load_n),
        sf,
    )
    if sf < 2.0:
        logger.warning("Safety factor %.2f is below the recommended minimum of 2.0 for a ground test fixture.", sf)

    drawing.render_bracket_drawing(geom, FIGURES_DIR / "bracket_drawing.pdf")
    drawing.render_bracket_drawing(geom, FIGURES_DIR / "bracket_drawing.svg")
    drawing.render_bracket_drawing(geom, FIGURES_DIR / "bracket_sketch.png")
    logger.info("Wrote dimensioned drawing (PDF/SVG/PNG) to %s", FIGURES_DIR)

    dxf_path = dxf_export.export_bracket_dxf(geom, FIGURES_DIR / "bracket_sketch.dxf")
    logger.info("Wrote DXF sketch to %s", dxf_path)

    bom_path = bom.save_bom_csv(geom, DATA_DIR / "bracket_bom.csv")
    logger.info("Wrote BOM to %s", bom_path)

    (DOCS_DIR / "fixture_material_selection.md").write_text(bom.MATERIAL_SELECTION_NOTES, encoding="utf-8")
    (DOCS_DIR / "fixture_manufacturing_notes.md").write_text(bom.MANUFACTURING_NOTES, encoding="utf-8")
    logger.info("Wrote material-selection and manufacturing notes to %s", DOCS_DIR)


if __name__ == "__main__":
    main()
