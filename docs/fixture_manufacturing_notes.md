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
