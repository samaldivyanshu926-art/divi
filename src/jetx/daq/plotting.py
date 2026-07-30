"""Static matplotlib summary plots: raw vs. filtered vs. QA-flagged data.

Complements the interactive Plotly dashboard (:mod:`dashboard`) with a
single publication-quality PNG suitable for a written report or slide,
which an HTML dashboard is not.
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
        "font.size": 9,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.titleweight": "bold",
    }
)


def plot_test_run_summary(df: pd.DataFrame, output_path: Path) -> Path:
    """Six-panel test-run summary: thrust, EGT, corrected speed, fuel flow,
    inlet pressure, and a QA flag timeline.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(3, 2, figsize=(12, 9), sharex=True)
    (ax_thrust, ax_egt), (ax_speed, ax_fuel), (ax_pressure, ax_qa) = axes

    t = df["time_s"]
    qa_fail = ~df["qa_pass"] if "qa_pass" in df.columns else pd.Series(False, index=df.index)

    def _plot_channel(ax, column: str, filtered_column: str | None, ylabel: str, title: str) -> None:
        ax.plot(t, df[column], color="tab:gray", alpha=0.5, lw=0.8, label="calibrated")
        if filtered_column and filtered_column in df.columns:
            ax.plot(t, df[filtered_column], color="tab:blue", lw=1.4, label="filtered")
        if qa_fail.any():
            ax.scatter(
                t[qa_fail], df.loc[qa_fail, column], color="red", marker="x", s=25, zorder=5, label="QA flag"
            )
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=7, loc="best")

    _plot_channel(ax_thrust, "thrust_n", "thrust_n_filtered", "Thrust [N]", "Thrust")
    _plot_channel(ax_egt, "egt_k", "egt_k_filtered", "EGT [K]", "Exhaust Gas Temperature")
    _plot_channel(
        ax_speed, "rpm_percent_corrected", None, "Corrected Speed [% N1c]", "Corrected Shaft Speed"
    )
    _plot_channel(ax_fuel, "fuel_flow_corrected_kg_s", None, "Fuel Flow [kg/s]", "Corrected Fuel Flow")
    _plot_channel(
        ax_pressure, "inlet_pressure_pa", "inlet_pressure_pa_filtered", "Pressure [Pa]", "Inlet Pressure"
    )

    ax_qa.plot(t, (~df["qa_pass"]).astype(int), color="tab:red", drawstyle="steps-post")
    ax_qa.set_title("QA Fail Timeline")
    ax_qa.set_ylabel("QA fail (1=yes)")
    ax_qa.set_ylim(-0.1, 1.1)

    for ax in (ax_speed, ax_fuel, ax_pressure, ax_qa):
        ax.set_xlabel("Time [s]")

    fig.suptitle("Test-Bed Run Summary — Raw/Filtered Channels + QA Flags", fontsize=13)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    fig.savefig(output_path)
    plt.close(fig)
    logger.info("Wrote test-run summary figure to %s", output_path)
    return output_path
