# Future Work

Concrete, scoped next steps for each project — written as engineering
follow-ups, not vague aspirations.

## Project 1 — Turbojet Performance Simulator

- [ ] Replace the two-constant-cp gas model with a variable-specific-heat
      gas table (e.g. NASA polynomials) for higher accuracy above ~1700 K TIT.
- [ ] Add a convergent-divergent (de Laval) nozzle option, and quantify
      the thrust/efficiency recovery it provides over the convergent-only
      model at high pressure ratio (see `docs/assumptions_and_limitations.md`
      item 3 for why this matters).
- [ ] Add compressor and turbine performance maps (pressure ratio /
      corrected mass flow / corrected speed / efficiency islands) and a
      component-matching solver, to move from cycle **design** analysis to
      off-design **performance** analysis at part-throttle.
- [ ] Add compressor bleed and turbine cooling-air off-takes, which
      reduce net turbine work and are significant above ~1500 K TIT on a
      real engine.
- [ ] Validate the model's static sea-level TSFC/thrust output directly
      against a published data sheet for a specific named engine (the
      current validation is qualitative-trend-only; see the README).

## Project 2 — Test-Bed Data Reduction

- [ ] Replace the synthetic data generator with real DAQ log ingestion —
      the calibration/filtering/QA pipeline's public functions all operate
      on a plain DataFrame with named raw columns, so this should be a
      drop-in swap of `synthetic.generate_raw_test_log()` for a CSV/TDMS
      reader, with no changes needed downstream.
- [ ] Replace the thermocouple's linear EMF-temperature approximation with
      the full NIST ITS-90 polynomial (or a lookup table) for
      certification-grade accuracy.
- [ ] Add a rate-of-change precondition (or a model-based transient
      detector) to the spike-detection QA rule, to eliminate the
      false-positive flags currently seen during spool-up/spool-down
      ramps (documented in `docs/assumptions_and_limitations.md`).
- [ ] Add multi-run comparison to the dashboard (overlay corrected
      parameters from several test runs on one set of axes), which is the
      actual day-to-day use case in a test cell (comparing today's run
      against a baseline).
- [ ] Add an automated PDF test report generator (per-run summary +
      QA pass/fail table + key corrected-parameter results) for archival.

## Project 3 — Test-Stand Fixture

- [ ] **Model the bracket as a real parametric part in Siemens NX or
      CATIA V5** (free student licenses available), with a proper
      GD&T-annotated manufacturing drawing conforming to ASME Y14.5 — the
      explicitly-stated next step for this project.
- [ ] Run a full FEA pass (bolt-hole shear tear-out, fillet stress
      concentration `Kt`, and a fatigue check against the expected
      test-cycle count) rather than the first-pass bearing-stress
      hand-calculation currently implemented.
- [ ] Extend `jetx/fixture/dxf_export.py` with `TEXT`/`MTEXT` entities so
      dimension callouts and the title block export into the DXF itself,
      not only the PDF/SVG drawing.
- [ ] Add supplier, unit cost, and lead-time columns to the BOM for a
      procurement-ready version.

## Cross-cutting

- [ ] Add a `Dockerfile` / `devcontainer.json` for a fully reproducible
      environment beyond `requirements.txt`.
- [ ] Add `mypy` static type checking to the CI workflow (the codebase is
      already fully type-hinted).
- [ ] Publish the generated performance maps and dashboard as a small
      static site (e.g. GitHub Pages) for reviewers who don't want to
      clone and run the repository.
