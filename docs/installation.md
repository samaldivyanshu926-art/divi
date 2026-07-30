# Installation Guide

## Requirements

- Python 3.12 (the codebase uses only 3.10+-compatible syntax, so 3.10/3.11
  will also work, but 3.12 is the tested/target version)
- ~50 MB free disk space (dependencies + generated CSV/PNG outputs)

## 1. Clone the repository

```bash
git clone https://github.com/<your-username>/jetx-engine-performance-portfolio.git
cd jetx-engine-performance-portfolio
```

## 2. Create a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

## 3. Install dependencies

For running the projects only:

```bash
pip install -r requirements.txt
```

For development (adds `pytest` and `ruff`, and installs the `jetx` package
itself in editable mode so `import jetx` works from anywhere):

```bash
pip install -e ".[dev]"
```

## 4. Run the test suite

```bash
pytest tests/ -v
```

All 60+ tests should pass in a couple of seconds — there is no I/O, network
access, or external service dependency anywhere in the test suite.

## 5. Run each project end to end

```bash
python scripts/run_project1_cycle_sweep.py       # Turbojet performance simulator
python scripts/run_project2_data_reduction.py    # Test-bed data reduction
python scripts/run_project3_fixture_drawing.py   # Test-stand fixture drawing/DXF/BOM
```

Each script is self-contained: it regenerates its CSVs under `data/` and
figures under `figures/` from scratch, so re-running is always safe (no
manual cleanup needed) and the repository's committed outputs can always be
reproduced exactly by re-running the corresponding script.

## 6. Open the interactive dashboard

Project 2 also produces an interactive Plotly dashboard:

```bash
open figures/project2/dashboard.html      # macOS
xdg-open figures/project2/dashboard.html  # Linux
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'jetx'` | Running a script directly without `pip install -e .` | Either install the package (`pip install -e .`), or run scripts from the repo root — each script under `scripts/` adds `src/` to `sys.path` itself, so `python scripts/run_project1_cycle_sweep.py` works even without installing. |
| `ValueError` from `jetx.cycle.components.fuel_air_ratio` | Turbine inlet temperature set unrealistically high (beyond the fuel's adiabatic flame limit for the assumed cp/LHV model) | Use a turbine inlet temperature under ~2000 K, which covers every practical turbojet design point. |
| Plotly dashboard opens blank in an offline environment | `fig.write_html(..., include_plotlyjs="cdn")` needs network access to load `plotly.js` from a CDN | Open the file with network access once, or change `include_plotlyjs="cdn"` to `include_plotlyjs=True` in `src/jetx/daq/dashboard.py` to embed the library inline (adds ~3 MB to the HTML file). |
