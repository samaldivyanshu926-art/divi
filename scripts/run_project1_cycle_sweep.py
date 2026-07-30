#!/usr/bin/env python3
"""Project 1 entry point: run the turbojet cycle sweeps end to end.

Generates:
    data/project1/cycle_performance_table.csv   (pressure-ratio sweep, tidy)
    data/project1/tit_sweep_table.csv           (TIT sweep, tidy)
    figures/project1/performance_map.png
    figures/project1/tit_sweep.png

Usage:
    python scripts/run_project1_cycle_sweep.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import numpy as np  # noqa: E402

from jetx.common.logging_config import get_logger  # noqa: E402
from jetx.cycle import plotting, sweep  # noqa: E402

logger = get_logger(__name__)

DATA_DIR = REPO_ROOT / "data" / "project1"
FIGURES_DIR = REPO_ROOT / "figures" / "project1"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    pressure_ratios = np.arange(4, 26, 2)
    turbine_inlet_temps = [1200.0, 1400.0, 1600.0, 1800.0]

    logger.info("Running pressure-ratio sweep: rc=%s, TIT=%s", list(pressure_ratios), turbine_inlet_temps)
    rc_sweep_df = sweep.pressure_ratio_sweep(pressure_ratios, turbine_inlet_temps)
    rc_sweep_df.to_csv(DATA_DIR / "cycle_performance_table.csv", index=False)
    logger.info("Wrote %d rows to %s", len(rc_sweep_df), DATA_DIR / "cycle_performance_table.csv")

    tit_values = np.arange(1100, 1950, 50)
    fixed_rcs = [8.0, 12.0, 16.0, 20.0]
    logger.info("Running TIT sweep: TIT=%s, rc=%s", list(tit_values), fixed_rcs)
    tit_sweep_df = sweep.turbine_inlet_temp_sweep(tit_values, fixed_rcs)
    tit_sweep_df.to_csv(DATA_DIR / "tit_sweep_table.csv", index=False)
    logger.info("Wrote %d rows to %s", len(tit_sweep_df), DATA_DIR / "tit_sweep_table.csv")

    plotting.plot_performance_map(rc_sweep_df, FIGURES_DIR / "performance_map.png")
    plotting.plot_tit_sweep(tit_sweep_df, FIGURES_DIR / "tit_sweep.png")

    best = rc_sweep_df.loc[rc_sweep_df["tsfc_kg_n_hr"].idxmin()]
    logger.info(
        "Best TSFC in sweep: %.4f kg/(N.hr) at rc=%.1f, TIT=%.0f K",
        best["tsfc_kg_n_hr"],
        best["pressure_ratio"],
        best["turbine_inlet_temp_k"],
    )


if __name__ == "__main__":
    main()
