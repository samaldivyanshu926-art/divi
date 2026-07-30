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
