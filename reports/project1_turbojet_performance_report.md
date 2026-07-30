# Project 1 — Turbojet Performance Simulator: Results Report

## Objective

Build a station-by-station, real-cycle turbojet performance model and use
it to characterise how compressor pressure ratio (`rc`) and turbine inlet
temperature (TIT) drive specific thrust, TSFC, and the three efficiency
figures of merit, at a static sea-level condition representative of a
ground test-stand run.

## Method

`jetx.cycle.engine.TurbojetEngine` evaluates one design point at a time
(intake → compressor → combustor → turbine → nozzle), following the
real-cycle relations derived in `docs/engineering_theory.md`. Component
efficiencies used for every sweep point are representative mid-size
turbojet values, not the specification of any named engine:

| Component | Parameter | Value |
|---|---|---|
| Intake | pressure recovery | 0.98 |
| Compressor | isentropic efficiency | 0.85 |
| Combustor | combustion efficiency | 0.98 |
| Combustor | pressure loss | 5% |
| Turbine | isentropic efficiency | 0.90 |
| Turbine | mechanical efficiency | 0.99 |
| Nozzle | isentropic efficiency | 0.97 |

`jetx.cycle.sweep.pressure_ratio_sweep` was run for `rc` = 4-24 (step 2)
at four TIT values (1200/1400/1600/1800 K); `turbine_inlet_temp_sweep` was
run for TIT = 1100-1900 K (step 50) at four `rc` values (8/12/16/20).
Air mass flow was fixed at 50 kg/s throughout (specific thrust and TSFC
are size-independent, so this choice does not affect the reported ratios).

## Results

- `data/project1/cycle_performance_table.csv` — 44-row pressure-ratio sweep
- `data/project1/tit_sweep_table.csv` — 68-row TIT sweep
- `figures/project1/performance_map.png` — four-panel performance map
- `figures/project1/tit_sweep.png` — specific thrust / TSFC vs. TIT

### Key findings

1. **Specific thrust peaks at an intermediate pressure ratio** for every
   TIT tested (e.g. `rc ≈ 12` at TIT = 1400 K), matching the textbook
   trend: raising `rc` increases thermal efficiency monotonically, but
   past a certain point it also erodes the turbine's available expansion
   work faster than it gains in cycle efficiency.
2. **TSFC improves monotonically with pressure ratio** at every TIT
   tested, over this sweep range — from 0.136 kg/(N·hr) at `rc=4` down to
   0.090 kg/(N·hr) at `rc=24`, at TIT = 1400 K.
3. **At `rc=12`, TIT=1400 K, static sea level:** specific thrust =
   840 N·s/kg, TSFC = 0.102 kg/(N·hr) (≈1.0 lb/(lbf·hr) — consistent with
   published static TSFC figures for mid-generation turbojets in this
   thrust class, which is the qualitative validation check used here; see
   the Validation section of the top-level README).
4. **Raising TIT increases specific thrust substantially** (618.9 to
   1110.9 N·s/kg across TIT=1100-1900 K at `rc=12`) but **does not
   reliably improve thermal efficiency** in this convergent-nozzle model
   — see `docs/assumptions_and_limitations.md` item 3 for the full
   explanation (nozzle choking limits energy recovery at high TIT/`rc`
   combinations).

## Validation approach

This model is checked against the **qualitative cycle trends** every
gas-turbine textbook predicts (thrust-vs-`rc` peak, TSFC-vs-`rc` monotonic
improvement, TIT-vs-thrust monotonic increase) and against a **known
static TSFC ballpark** (≈1.0 lb/(lbf·hr), typical for this engine class),
rather than a claimed exact match to any specific named engine's published
data sheet, which this project does not have independent access to verify
against.
