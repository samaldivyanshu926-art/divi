"""Tests for the parametric cycle sweeps used to build performance maps."""

from jetx.cycle.sweep import pressure_ratio_sweep, turbine_inlet_temp_sweep


def test_pressure_ratio_sweep_shape_and_columns():
    df = pressure_ratio_sweep(pressure_ratios=[6, 10, 14], turbine_inlet_temps_k=[1300.0, 1500.0])
    assert len(df) == 6
    expected_columns = {"pressure_ratio", "turbine_inlet_temp_k", "specific_thrust_n_s_kg", "tsfc_kg_n_hr"}
    assert expected_columns.issubset(df.columns)
    assert set(df["pressure_ratio"].unique()) == {6, 10, 14}
    assert set(df["turbine_inlet_temp_k"].unique()) == {1300.0, 1500.0}


def test_tit_sweep_shape_and_monotonic_thrust_trend():
    df = turbine_inlet_temp_sweep(turbine_inlet_temps_k=[1200.0, 1400.0, 1600.0], pressure_ratios=[10.0])
    df = df.sort_values("turbine_inlet_temp_k")
    thrusts = df["specific_thrust_n_s_kg"].tolist()
    assert thrusts == sorted(thrusts)  # thrust increases monotonically with TIT at fixed rc
