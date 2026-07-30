# Project 3 — Test-Stand Fixture: Results Report

## Objective

Produce a dimensioned concept sketch for the load-cell mounting bracket
that carries a test-stand load cell between the engine thrust frame and
the stand's fixed structure — precise enough to define geometry and
design intent ahead of modelling it properly in real parametric CAD.

## Method

`jetx.fixture.geometry.BracketGeometry` parametrically defines the
bracket: a 120 x 80 x 12 mm 6061-T6 aluminum plate, four filleted corners
(R8 mm), four M8 clearance bolt holes (17 mm edge margin), and a central
⌀20 mm clevis bore.

A first-pass bearing-stress check at the clevis bore was run at a
representative maximum test-stand load of 5,000 N:

```
sigma_bearing = F / (d_bore * t) = 5000 / (20.0 * 12.0) = 20.8 MPa
safety_factor = sigma_yield / sigma_bearing = 276 / 20.8 = 13.25
```

A safety factor of 13.25 against yield is comfortably above the
recommended minimum of 2.0 for a ground test fixture — the bracket's
sizing here is dominated by the bolt-pattern edge-margin and clearance-hole
practice, not by the bearing-stress limit, which is typical for a bracket
this size at moderate test loads.

## Results

- `figures/project3/bracket_drawing.pdf`, `.svg`, `.png` — two-view dimensioned drawing
- `figures/project3/bracket_sketch.dxf` — DXF (R12 ASCII), opens in any DXF-capable CAD package
- `data/project3/bracket_bom.csv` — 5-line-item bill of materials
- `docs/fixture_material_selection.md` — material trade study
- `docs/fixture_manufacturing_notes.md` — process/tolerance/inspection notes

### Key findings

1. **Estimated part mass: 291.7 g** in 6061-T6 aluminum (net area
   9,004 mm², corrected for four corner fillets and all three hole types).
2. **13.25x safety factor** against yield at the clevis bearing interface
   under a 5,000 N representative load — comfortable margin for a ground
   test fixture, leaving room to either reduce plate thickness (lower
   mass) or accept higher test loads without redesign.
3. **DXF export is exact, not approximated** — the filleted-rectangle
   outline uses true `ARC` entities for the four corners (not a
   many-segment polyline approximation), so the DXF opens identically to
   the vector drawing in any DXF-capable CAD package.

## Status

This is a **concept sketch**, explicitly not released for manufacture (see
the drawing's title block). The stated next step — modelling this as a
real parametric part in Siemens NX or CATIA V5 with a GD&T-annotated
manufacturing drawing — is tracked in `docs/future_work.md`.
