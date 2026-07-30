"""Publication-quality matplotlib figures for the turbojet cycle model.

Kept deliberately separate from the physics (:mod:`components`,
:mod:`engine`) and the sweep logic (:mod:`sweep`) — this module only ever
takes a ``pandas.DataFrame`` in and a ``Path`` out. That separation is what
lets :mod:`tests.test_engine` exercise the physics without importing
matplotlib at all.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from ..common.logging_config import get_logger

logger = get_logger(__name__)

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.titleweight": "bold",
    }
)


def plot_performance_map(sweep_df: pd.DataFrame, output_path: Path) -> Path:
    """Four-panel performance map from a pressure-ratio sweep DataFrame.

    Panels: specific thrust vs. rc, TSFC vs. rc, thermal/propulsive/overall
    efficiency vs. rc, and fuel-air ratio vs. rc — each with one curve per
    turbine inlet temperature, the standard layout for a cycle-design
    trade study.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    ax_thrust, ax_tsfc, ax_eff, ax_far = axes.flat

    for tit, group in sweep_df.groupby("turbine_inlet_temp_k"):
        group = group.sort_values("pressure_ratio")
        label = f"TIT = {tit:.0f} K"
        ax_thrust.plot(group["pressure_ratio"], group["specific_thrust_n_s_kg"], marker="o", ms=3, label=label)
        ax_tsfc.plot(group["pressure_ratio"], group["tsfc_kg_n_hr"], marker="o", ms=3, label=label)
        ax_eff.plot(group["pressure_ratio"], group["thermal_efficiency"] * 100, marker="o", ms=3, label=label)
        ax_far.plot(group["pressure_ratio"], group["fuel_air_ratio"] * 1000, marker="o", ms=3, label=label)

    ax_thrust.set_title("Specific Thrust")
    ax_thrust.set_xlabel("Compressor pressure ratio, $r_c$")
    ax_thrust.set_ylabel("$F_s$  [N·s/kg]")
    ax_thrust.legend(fontsize=8)

    ax_tsfc.set_title("Thrust-Specific Fuel Consumption")
    ax_tsfc.set_xlabel("Compressor pressure ratio, $r_c$")
    ax_tsfc.set_ylabel("TSFC  [kg/(N·hr)]")
    ax_tsfc.legend(fontsize=8)

    ax_eff.set_title("Thermal Efficiency")
    ax_eff.set_xlabel("Compressor pressure ratio, $r_c$")
    ax_eff.set_ylabel(r"$\eta_{th}$  [%]")
    ax_eff.legend(fontsize=8)

    ax_far.set_title("Fuel-Air Ratio")
    ax_far.set_xlabel("Compressor pressure ratio, $r_c$")
    ax_far.set_ylabel("f  [g fuel / kg air]")
    ax_far.legend(fontsize=8)

    fig.suptitle("Turbojet Performance Map — Pressure Ratio Sweep (static, sea level)", fontsize=13)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    fig.savefig(output_path)
    plt.close(fig)
    logger.info("Wrote performance map to %s", output_path)
    return output_path


def plot_tit_sweep(sweep_df: pd.DataFrame, output_path: Path) -> Path:
    """Specific thrust and TSFC vs. turbine inlet temperature, one curve per rc."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, (ax_thrust, ax_tsfc) = plt.subplots(1, 2, figsize=(11, 4.5))

    for rc, group in sweep_df.groupby("pressure_ratio"):
        group = group.sort_values("turbine_inlet_temp_k")
        label = f"$r_c$ = {rc:.0f}"
        ax_thrust.plot(
            group["turbine_inlet_temp_k"], group["specific_thrust_n_s_kg"], marker="o", ms=3, label=label
        )
        ax_tsfc.plot(group["turbine_inlet_temp_k"], group["tsfc_kg_n_hr"], marker="o", ms=3, label=label)

    ax_thrust.set_title("Specific Thrust vs. TIT")
    ax_thrust.set_xlabel("Turbine inlet temperature, $T_{04}$  [K]")
    ax_thrust.set_ylabel("$F_s$  [N·s/kg]")
    ax_thrust.legend(fontsize=8)

    ax_tsfc.set_title("TSFC vs. TIT")
    ax_tsfc.set_xlabel("Turbine inlet temperature, $T_{04}$  [K]")
    ax_tsfc.set_ylabel("TSFC  [kg/(N·hr)]")
    ax_tsfc.legend(fontsize=8)

    fig.suptitle("Turbojet Performance Map — Turbine Inlet Temperature Sweep (static, sea level)", fontsize=13)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94))
    fig.savefig(output_path)
    plt.close(fig)
    logger.info("Wrote TIT sweep figure to %s", output_path)
    return output_path
