"""Project 3 — Test-Stand Fixture: load-cell mounting bracket.

A parametric 2D concept design for the bracket that carries a test-stand
load cell between the engine thrust frame and the stand's fixed structure.
This is a **dimensioned concept sketch**, not parametric CAD (no solid
model, no GD&T) — it defines geometry and design intent precisely enough
to be modelled properly in Siemens NX / CATIA / SolidWorks, which is
explicitly the stated next step (see docs/future_work.md).

Modules
-------
geometry   : ``BracketGeometry`` — the parametric definition of the bracket.
drawing    : Dimensioned 2D engineering drawing, exported to PDF and SVG.
dxf_export : Minimal, dependency-free DXF (R12 ASCII) exporter.
bom        : Bill of materials generation.
"""
