# Architecture

## Design principle

Every project follows the same three-layer split, so the pattern only
needs to be learned once:

1. **Physics/domain layer** (`components.py`, `sensors.py`, `geometry.py`)
   — pure functions and frozen dataclasses. No file I/O, no plotting, no
   logging side effects beyond what the caller asks for. This is the layer
   the unit tests exercise directly, and the layer that is safe to import
   without pulling in matplotlib/plotly.

2. **Orchestration layer** (`engine.py`, `calibration.py`/`qa.py`/etc.,
   `bom.py`) — wires the domain functions together into a full
   station-by-station cycle, a full reduction pipeline, or a full BOM. It
   still returns data (a dataclass or a DataFrame), not files.

3. **I/O layer** (`plotting.py`, `dashboard.py`, `drawing.py`,
   `dxf_export.py`, and `scripts/run_project*.py`) — takes the
   orchestration layer's output and writes CSV/PNG/PDF/SVG/DXF/HTML. This
   is the only layer that touches the filesystem or a plotting library.

This split is why, for example, `tests/test_engine.py` can run 60+ cycle
evaluations in a fraction of a second with zero matplotlib import — the
physics has no idea plotting exists.

## Repository layout

```
jetx-engine-performance-portfolio/
├── src/jetx/                  # the actual package (installable, importable)
│   ├── cycle/                 # Project 1 — turbojet performance simulator
│   │   ├── atmosphere.py      #   ISA atmosphere model
│   │   ├── components.py      #   intake/compressor/combustor/turbine/nozzle physics
│   │   ├── engine.py          #   TurbojetEngine — orchestrates one full cycle
│   │   ├── performance.py     #   thrust / TSFC / efficiency formulae
│   │   ├── sweep.py           #   pressure-ratio and TIT parametric sweeps
│   │   └── plotting.py        #   performance-map figures
│   ├── daq/                   # Project 2 — test-bed data reduction
│   │   ├── sensors.py         #   per-sensor calibration models
│   │   ├── synthetic.py       #   synthetic raw DAQ log generator
│   │   ├── calibration.py     #   raw -> engineering-unit reduction
│   │   ├── filtering.py       #   moving-average / Butterworth filters
│   │   ├── corrected_speed.py #   ISA-referenced corrected parameters
│   │   ├── qa.py               #   automated QA flagging
│   │   ├── dashboard.py       #   interactive Plotly dashboard
│   │   └── plotting.py        #   static matplotlib summary figure
│   ├── fixture/                # Project 3 — test-stand fixture
│   │   ├── geometry.py         #   parametric bracket geometry + strength check
│   │   ├── drawing.py          #   dimensioned 2D drawing (PDF/SVG/PNG)
│   │   ├── dxf_export.py       #   dependency-free DXF (R12 ASCII) writer
│   │   └── bom.py              #   bill of materials + material/mfg notes
│   └── common/                  # shared, cross-project utilities
│       ├── units.py             #   unit conversions (SI <-> psi/degF/RPM/etc.)
│       └── logging_config.py    #   one shared logging setup
├── scripts/                     # thin CLI entry points, one per project
├── tests/                       # pytest suite, mirrors the src/ layout
├── data/                        # generated CSV outputs (tracked, reproducible)
├── figures/                     # generated PNG/PDF/SVG/HTML outputs (tracked, reproducible)
├── docs/                        # this file + theory/installation/assumptions/future-work
├── reports/                     # per-project written summaries
├── notebooks/                   # exploratory Jupyter notebooks
└── presentations/                # slide-style summary of all three projects
```

## Why this split

- **Testability.** Every physics function takes plain values/dataclasses
  in and returns plain values/dataclasses out — no hidden state, no
  filesystem access — so it can be unit-tested with exact hand-calculated
  expected values (see `tests/test_components.py`).
- **Reusability.** `jetx.cycle.components` has no idea `sweep.py` or
  `plotting.py` exist. Someone wanting only the compressor model for a
  different project can import exactly that, with no matplotlib/pandas
  dependency pulled in transitively.
- **Traceability.** The orchestration layer (e.g. `engine.py`) is a short,
  readable, station-by-station function precisely because it does not also
  contain the thermodynamics — reading `TurbojetEngine.run()` top to
  bottom *is* reading the cycle diagram.
- **One way to run each project.** `scripts/run_project*.py` is the single
  source of truth for "how do I regenerate this repo's data and figures,"
  rather than that logic being duplicated across notebooks and reports.
