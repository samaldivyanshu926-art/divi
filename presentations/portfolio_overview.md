<!--
Marp/reveal.js-compatible slide deck ("---" separates slides).
Render with e.g. `npx @marp-team/marp-cli portfolio_overview.md -o portfolio_overview.pdf`.
-->

# JetX Engine Performance & Testing Portfolio

Three self-directed projects built to demonstrate the core skills of an
**Engine Performance & Testing Engineer**: cycle performance analysis,
test-bed data reduction, and test-stand hardware design.

---

## Why these three projects

| Role requirement | Project |
|---|---|
| Gas-turbine cycle / performance analysis | Project 1 — Turbojet Performance Simulator |
| Test-cell instrumentation & data reduction | Project 2 — Test-Bed Data Reduction |
| Test-stand hardware / fixture design | Project 3 — Test-Stand Fixture |

Each project is a complete, runnable, tested Python package — not a
one-off script — under `src/jetx/`.

---

## Project 1 — Turbojet Performance Simulator

- Full station-by-station real-cycle model: intake → compressor →
  combustor → turbine → nozzle
- Pressure-ratio and turbine-inlet-temperature parametric sweeps
- Publication-quality performance maps

![Performance map](../figures/project1/performance_map.png)

---

## Project 1 — Key Result

At `rc=12`, TIT=1400 K, static sea level:
**specific thrust = 840 N·s/kg, TSFC ≈ 1.0 lb/(lbf·hr)**
— consistent with published static TSFC for this engine class.

Specific thrust peaks at an intermediate pressure ratio for every TIT
tested, exactly as gas-turbine cycle theory predicts.

---

## Project 2 — Test-Bed Data Reduction

- Synthetic raw DAQ generation (load cell, thermocouple, pressure
  transducer, RPM pickup)
- Calibration → Butterworth filtering → ISA-referenced corrected speed →
  automated QA flagging
- Interactive Plotly dashboard + static summary figure

![Test run summary](../figures/project2/test_run_summary.png)

---

## Project 2 — Key Result

All three deliberately-injected instrumentation faults (dropout, stuck
value, EMI spike) were **correctly caught** by the automated QA pipeline,
verified against the raw log and by unit test.

4.6% of samples flagged in a 120 s run — traceable, not a black box.

---

## Project 3 — Test-Stand Fixture

- Parametric load-cell mounting bracket geometry
- Dimensioned 2-view drawing (PDF/SVG/PNG)
- Exact DXF export (LINE/ARC/CIRCLE entities)
- Bill of materials + material selection + manufacturing notes

![Bracket sketch](../figures/project3/bracket_sketch.png)

---

## Project 3 — Key Result

**291.7 g** estimated mass, **13.25x safety factor** against yield at the
clevis bearing interface under a representative 5,000 N test load.

Status: concept sketch — next step is a real parametric model in Siemens
NX / CATIA V5, tracked explicitly in `docs/future_work.md`.

---

## Honest Scope

- Project 1's cycle model uses simplifying assumptions (two constant-cp
  gas models, no bleed, convergent-only nozzle) documented in
  `docs/assumptions_and_limitations.md`.
- Project 2's raw test data is synthetic; the reduction **pipeline** is
  real, general-purpose code.
- Project 3 is a concept sketch, not a released manufacturing drawing.

All of this is stated directly in the documentation rather than implied
otherwise — see `README.md` and `docs/assumptions_and_limitations.md`.

---

## Thank You

Repository: `jetx-engine-performance-portfolio/`
62 passing unit tests · full CI · every equation documented and derived in
`docs/engineering_theory.md`
