"""Tests for ISA-referenced corrected speed / corrected mass flow."""

import pandas as pd
import pytest

from jetx.daq.corrected_speed import P_REF_PA, T_REF_K, corrected_mass_flow, corrected_speed


def test_corrected_speed_equals_actual_at_reference_conditions():
    rpm = pd.Series([10_000.0, 20_000.0])
    result = corrected_speed(rpm, inlet_temp_k=pd.Series([T_REF_K, T_REF_K]))
    assert result.tolist() == pytest.approx(rpm.tolist())


def test_corrected_speed_is_higher_on_a_hot_day():
    # A hotter-than-reference inlet temperature means the same actual RPM
    # corresponds to a *lower* corrected speed (theta > 1 => divide by
    # sqrt(theta) > 1), i.e. the engine is doing "less" in referred terms.
    rpm = pd.Series([20_000.0])
    hot_day = corrected_speed(rpm, inlet_temp_k=pd.Series([308.15]))  # 35 degC
    assert hot_day.iloc[0] < rpm.iloc[0]


def test_corrected_mass_flow_equals_actual_at_reference_conditions():
    w = pd.Series([5.0, 10.0])
    ref_temps = pd.Series([T_REF_K, T_REF_K])
    ref_pressures = pd.Series([P_REF_PA, P_REF_PA])
    result = corrected_mass_flow(w, inlet_temp_k=ref_temps, inlet_pressure_pa=ref_pressures)
    assert result.tolist() == pytest.approx(w.tolist())
