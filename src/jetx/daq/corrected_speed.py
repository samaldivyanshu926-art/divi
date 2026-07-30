"""ISA-referenced corrected speed and corrected fuel/mass flow.

Gas-turbine performance parameters depend on inlet temperature and
pressure, so raw test-day values are not directly comparable between two
runs on different days. Corrected parameters (per Buckingham-Pi
non-dimensionalisation of the compressor/turbine similarity groups)
remove that dependence, referenced to sea-level ISA conditions:

    theta = T_inlet / T_ref          T_ref = 288.15 K
    delta = p_inlet / p_ref          p_ref = 101,325 Pa

    N_corrected     = N_actual / sqrt(theta)
    W_corrected     = W_actual * sqrt(theta) / delta      (corrected mass flow)

These are the standard "referred" parameters used throughout gas-turbine
test and performance work (Saravanamuttoo et al., ch. 4; Walsh & Fletcher,
*Gas Turbine Performance*, ch. 3) — they are what lets two test points
taken on a 15 degC morning and a 35 degC afternoon be compared directly.
"""

from __future__ import annotations

import pandas as pd

T_REF_K: float = 288.15
P_REF_PA: float = 101_325.0


def corrected_speed(rpm_actual: pd.Series, inlet_temp_k: pd.Series, t_ref_k: float = T_REF_K) -> pd.Series:
    """Corrected (referred) rotational speed: N / sqrt(theta)."""
    theta = inlet_temp_k / t_ref_k
    return rpm_actual / theta**0.5


def corrected_mass_flow(
    mass_flow_actual_kg_s: pd.Series,
    inlet_temp_k: pd.Series,
    inlet_pressure_pa: pd.Series,
    t_ref_k: float = T_REF_K,
    p_ref_pa: float = P_REF_PA,
) -> pd.Series:
    """Corrected (referred) mass flow: W * sqrt(theta) / delta."""
    theta = inlet_temp_k / t_ref_k
    delta = inlet_pressure_pa / p_ref_pa
    return mass_flow_actual_kg_s * theta**0.5 / delta


def add_corrected_parameters(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``rpm_corrected`` and ``fuel_flow_corrected_kg_s`` columns to a reduced log.

    Expects ``df`` to already have ``rpm``, ``fuel_flow_kg_s``,
    ``ambient_temp_k`` and ``ambient_pressure_pa`` columns (i.e. to have
    already been through :func:`jetx.daq.calibration.apply_calibration`).
    """
    df = df.copy()
    df["rpm_corrected"] = corrected_speed(df["rpm"], df["ambient_temp_k"])
    df["fuel_flow_corrected_kg_s"] = corrected_mass_flow(
        df["fuel_flow_kg_s"], df["ambient_temp_k"], df["ambient_pressure_pa"]
    )
    df["rpm_percent_corrected"] = df["rpm_corrected"] / df["rpm_corrected"].max() * 100.0
    return df
