"""Unit tests for the standalone thrust/efficiency formulae."""

import pytest

from jetx.cycle import performance as perf


def test_net_thrust_matches_hand_calculation_no_pressure_term():
    thrust = perf.net_thrust(
        air_mass_flow_kg_s=50.0,
        fuel_air_ratio_value=0.02,
        exit_velocity_m_s=600.0,
        flight_velocity_m_s=0.0,
        exit_area_m2=0.2,
        exit_static_pressure_pa=101_325.0,
        ambient_pressure_pa=101_325.0,
    )
    expected = 50.0 * (1.02 * 600.0 - 0.0)  # + 0.2*(0) pressure term
    assert thrust == pytest.approx(expected)


def test_net_thrust_includes_pressure_thrust_when_choked():
    thrust = perf.net_thrust(
        air_mass_flow_kg_s=50.0,
        fuel_air_ratio_value=0.02,
        exit_velocity_m_s=600.0,
        flight_velocity_m_s=0.0,
        exit_area_m2=0.2,
        exit_static_pressure_pa=150_000.0,
        ambient_pressure_pa=101_325.0,
    )
    expected = 50.0 * (1.02 * 600.0) + 0.2 * (150_000.0 - 101_325.0)
    assert thrust == pytest.approx(expected)


def test_thermal_efficiency_between_zero_and_one_for_realistic_inputs():
    eta = perf.thermal_efficiency(fuel_air_ratio_value=0.02, exit_velocity_m_s=600.0, flight_velocity_m_s=200.0)
    assert 0.0 < eta < 1.0


def test_propulsive_efficiency_is_one_when_jet_velocity_equals_flight_velocity():
    # As V8 -> V0, propulsive efficiency -> 1 (no kinetic energy wasted in the exhaust).
    eta_p = perf.propulsive_efficiency(
        fuel_air_ratio_value=0.0, exit_velocity_m_s=250.0001, flight_velocity_m_s=250.0
    )
    assert eta_p == pytest.approx(1.0, abs=1e-3)


def test_overall_efficiency_is_product_of_the_two():
    eta_o = perf.overall_efficiency(thermal_eff=0.4, propulsive_eff=0.5)
    assert eta_o == pytest.approx(0.2)


def test_tsfc_scales_linearly_with_fuel_flow():
    tsfc_low = perf.tsfc(fuel_mass_flow_kg_s=1.0, thrust_n=10_000.0)
    tsfc_high = perf.tsfc(fuel_mass_flow_kg_s=2.0, thrust_n=10_000.0)
    assert tsfc_high == pytest.approx(2.0 * tsfc_low)
