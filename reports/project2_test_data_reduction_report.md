# Project 2 — Test-Bed Data Reduction: Results Report

## Objective

Build a complete test-cell data-reduction pipeline — synthetic raw DAQ
signal generation, sensor calibration, noise filtering, ISA-referenced
corrected-parameter normalisation, and automated QA flagging — and
demonstrate it end to end on a representative 120-second spool-up /
steady-state / spool-down test run.

## Method

`jetx.daq.synthetic.generate_raw_test_log()` generates raw signals (load
cell counts, thermocouple mV, pressure transducer mA, RPM pulse counts,
fuel flow) at 10 Hz for a 120 s run, following a documented physical model
(throttle profile → first-order-lag RPM response → power-law thrust/EGT/
pressure/fuel-flow relationships — see `docs/engineering_theory.md`), with
realistic per-channel noise added. Three faults are deliberately injected
to exercise the QA logic: a 1 s thermocouple dropout, a 2 s pressure
transducer stuck-value fault, and a single-scan load-cell EMI spike.

The reduction pipeline then runs, in order:

1. `jetx.daq.calibration.apply_calibration` — raw signals to engineering units.
2. `jetx.daq.filtering.filter_channel` — Butterworth low-pass (fc = 1.0 Hz) on thrust, EGT, and inlet pressure.
3. `jetx.daq.corrected_speed.add_corrected_parameters` — ISA-referenced corrected speed and fuel flow.
4. `jetx.daq.qa.evaluate_log_qa` — dropout / stuck / spike / out-of-range flagging on all four monitored channels.

## Results

- `data/project2/raw_test_log.csv` — 1,201-sample raw DAQ log
- `data/project2/reduced_test_log.csv` — full reduced log (calibrated, filtered, corrected, QA-flagged)
- `figures/project2/test_run_summary.png` — six-panel static summary
- `figures/project2/dashboard.html` — interactive multi-panel Plotly dashboard

### Key findings

1. **Peak thrust 6,113 N** — this is the deliberately-injected load-cell
   spike (true steady-state peak thrust is ≈4,500 N); it is correctly
   caught by `qa_thrust_n_spike`, demonstrating exactly the kind of
   single-scan glitch a real strain-gauge load cell can show under cable
   EMI.
2. **55 of 1,201 samples (4.6%) were QA-flagged.** Of these, 10 are the
   injected thermocouple dropout, 12 are the injected pressure stuck-value
   fault (flagged after an 8-sample confirmation window — see
   `docs/assumptions_and_limitations.md`), 7 are the injected/related
   load-cell spike region, and the remainder are false-positive spike
   flags during the fast spool-up/spool-down ramps — a known, documented
   characteristic of the windowed robust-z-score spike detector, not a
   pipeline defect.
3. **All three deliberately-injected faults were correctly caught** by
   their respective QA rules, verified both by direct inspection of
   `reduced_test_log.csv` and by `tests/test_qa.py`.
4. **Corrected speed and corrected fuel flow track raw RPM/fuel-flow
   closely** in this run because ambient conditions were generated close
   to the ISA reference (25 degC test-cell) — the value of the correction
   becomes larger on test days further from reference conditions.

## Honesty note

The raw data is entirely synthetic — there is no physical rig behind it.
The calibration/filtering/corrected-speed/QA pipeline is real,
general-purpose code that operates on any DataFrame with the same raw
column names; that pipeline, not the synthetic signal itself, is the
skill being demonstrated here.
