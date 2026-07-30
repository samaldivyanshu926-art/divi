# Assumptions & Limitations

Being explicit about what a model does *not* capture is as important as
the model itself. This document lists every deliberate simplification
made in this repository, why it was made, and what its consequences are —
found either analytically or by actually running the code and looking at
the output, not asserted from memory.

## Project 1 — Turbojet Performance Simulator

1. **Two constant-property gas models (cold/hot), not a full gas table.**
   Real specific heats vary continuously with temperature and combustion
   product composition. Using two constant-but-different `(cp, gamma)`
   sets (cold air vs. hot combustion gas) captures most of that effect
   without a variable-property gas table, and is standard practice for
   hand/spreadsheet-level cycle analysis. It will diverge from a full
   variable-cp model by a few percent at the highest TIT values in the
   sweep (>1700 K).

2. **No bleed air, no variable geometry, no power off-take.** The turbine
   supplies *exactly* the compressor's work demand (single-spool, no
   accessory drive, no customer bleed). Real engines bleed compressor air
   for cooling and cabin/ECS air, which reduces available turbine work and
   is not modelled here.

3. **Convergent-only nozzle, and what it does to the TIT sweep.** This is
   the most important limitation to understand, because it produces a
   genuinely counter-intuitive result if you don't know it's there: **at a
   fixed pressure ratio, raising turbine inlet temperature increases
   specific thrust, but does *not* reliably increase thermal efficiency in
   this model** (see `figures/project1/tit_sweep.png` output and
   `tests/test_engine.py::test_higher_turbine_inlet_temperature_increases_thrust_and_fuel_air_ratio`).
   The reason: once the pressure ratio is high enough to choke the nozzle
   (which happens across most of this repo's default sweep range), the
   flow can never fully expand to ambient pressure. As TIT rises, more of
   the extra combustion enthalpy shows up as *unexpanded residual heat and
   pressure* in the exhaust rather than jet kinetic energy — a real
   physical effect of a purely convergent nozzle, not a bug. A
   convergent-divergent (de Laval) nozzle, standard on real supersonic-
   capable or high-pressure-ratio engines, would recover much more of that
   energy as additional thrust. This is exactly why nozzle design becomes
   a first-order lever once cycle pressure ratios climb — a genuine
   "aha" a student should take away from running this simulator, not a
   modeling error to be papered over.

4. **No off-design (part-throttle) matching.** Every sweep point is an
   independent *design* point (compressor and turbine sized exactly for
   that pressure ratio and TIT). A real engine's compressor and turbine
   are fixed hardware; running it away from its design point requires
   compressor/turbine maps and a component-matching iteration, which this
   simulator does not do. This is a **cycle design** tool, not an
   **off-design performance** tool.

5. **No losses from inlet distortion, Reynolds number effects, or
   variable-geometry devices** (variable stators, bleed valves, etc).

## Project 2 — Test-Bed Data Reduction

1. **The raw test data is entirely synthetic.** There is no physical rig
   behind it — `jetx/daq/synthetic.py` generates it from a simple,
   documented physical model (RPM tracks throttle with a first-order lag;
   thrust/EGT/pressure/fuel flow all follow simple power-law functions of
   RPM). The point of this project is the **calibration → filtering →
   corrected-speed → QA pipeline**, which is real, general-purpose code
   that would work unchanged on genuine DAQ output in the same raw-column
   format. This is stated here, in the top-level README, and in the
   module docstring rather than left implicit anywhere.

2. **Thermocouple calibration is linear, not the full NIST polynomial.**
   A real Type-K thermocouple's EMF-temperature relationship is an
   8th/9th-order polynomial (NIST ITS-90 reference tables). The linear
   approximation used here (nominal Seebeck coefficient ≈0.041 mV/°C) is
   accurate to within a few degrees over a few-hundred-degree span around
   the reference point, which is adequate for this portfolio but would
   need the full polynomial (or a lookup table) for certified test data.

3. **QA stuck-value detection has a built-in detection lag.** The flag
   only fires once a channel has held `stuck_window_samples` (default 8)
   consecutive exact-zero readings — so a real stuck sensor is correctly
   caught, but only starting `stuck_window_samples` scans after it first
   froze, not on the very first repeated sample. This is a deliberate
   precision/recall trade-off (a shorter window would false-positive on
   any two genuinely-identical noisy samples); it is documented here
   rather than tuned away silently. Running `scripts/run_project2_data_reduction.py`
   and comparing the injected 20-sample stuck fault against the 12 flagged
   samples in `data/project2/reduced_test_log.csv` shows this lag directly.

4. **QA spike detection can false-positive during fast transients** (the
   spool-up and spool-down ramps). The median/MAD-based robust z-score
   assumes the *local* signal is roughly constant aside from noise; a fast
   monotonic ramp inside a small rolling window looks statistically
   similar to a spike. This is a known, standard limitation of any simple
   windowed outlier detector and is visible in the generated
   `figures/project2/test_run_summary.png` (extra QA marks scattered
   through the 20–50 s and 90–120 s ramp regions, not just at the three
   deliberately-injected faults). A production system would typically
   gate this detector on a "rate of change is otherwise small" precondition,
   or use a model-based (not purely statistical) transient detector —
   flagged in `docs/future_work.md`.

5. **Corrected speed/mass-flow use a single reference condition** (sea
   level ISA). This is the standard convention, but a real test cell would
   also track barometric drift within a single day's testing, which this
   synthetic run does not model (ambient conditions are generated with
   small random noise only, no systematic drift).

## Project 3 — Test-Stand Fixture

1. **This is a dimensioned concept sketch, not parametric CAD.** There is
   no solid model, no GD&T (geometric dimensioning & tolerancing) frames,
   and no formal drawing-standard compliance (ASME Y14.5, etc.). It is
   precise enough to define geometry and intent for modelling properly in
   Siemens NX / CATIA / SolidWorks — explicitly flagged as the next step
   in `docs/future_work.md`, not implied to already be production-ready.

2. **Only a first-pass bearing-stress check, no fatigue or FEA.** The
   safety-factor calculation (`geometry.BracketGeometry.safety_factor`)
   checks projected bearing stress at the clevis bore only. It does not
   check shear tear-out at the bolt holes, stress concentration at the
   fillets (`Kt`), fatigue life under repeated test-stand loading cycles,
   or buckling. A released manufacturing drawing would need a full FEA
   pass and a fatigue analysis against the expected test-cycle count.

3. **DXF export supports LINE, ARC and CIRCLE only.** This covers this
   bracket's geometry completely and exactly (no faceted-arc
   approximation), but is not a general-purpose DXF writer — a part with
   splines, hatching, or text annotations would need additional entity
   types added to `jetx/fixture/dxf_export.py`.

4. **BOM fastener/material costs and lead times are not included** — the
   BOM lists part numbers, quantities, and mass only. A procurement-ready
   BOM would add supplier, unit cost, and lead time columns.
