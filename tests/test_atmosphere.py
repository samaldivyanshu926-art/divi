"""Unit tests for the ISA atmosphere model."""

import pytest

from jetx.cycle.atmosphere import isa, stagnation_pressure, stagnation_temperature


def test_sea_level_matches_isa_standard_values():
    state = isa(0.0)
    assert state.temperature_k == pytest.approx(288.15, abs=1e-6)
    assert state.pressure_pa == pytest.approx(101_325.0, abs=1e-3)
    assert state.density_kg_m3 == pytest.approx(1.225, abs=1e-3)
    assert state.speed_of_sound_m_s == pytest.approx(340.29, abs=0.05)


def test_11km_tropopause_matches_isa_standard_values():
    state = isa(11_000.0)
    assert state.temperature_k == pytest.approx(216.65, abs=1e-2)
    assert state.pressure_pa == pytest.approx(22_632.0, rel=1e-3)


def test_temperature_decreases_monotonically_through_troposphere():
    altitudes = [0.0, 2000.0, 5000.0, 8000.0, 11_000.0]
    temps = [isa(h).temperature_k for h in altitudes]
    assert temps == sorted(temps, reverse=True)


def test_isothermal_stratosphere_holds_temperature_constant():
    t1 = isa(12_000.0).temperature_k
    t2 = isa(18_000.0).temperature_k
    assert t1 == pytest.approx(t2, abs=1e-9)


def test_out_of_range_altitude_raises():
    with pytest.raises(ValueError):
        isa(-1.0)
    with pytest.raises(ValueError):
        isa(25_000.0)


def test_stagnation_temperature_equals_static_at_zero_mach():
    assert stagnation_temperature(288.15, mach=0.0) == pytest.approx(288.15)


def test_stagnation_temperature_rises_with_mach():
    t0_low = stagnation_temperature(288.15, mach=0.5)
    t0_high = stagnation_temperature(288.15, mach=0.9)
    assert t0_high > t0_low > 288.15


def test_stagnation_pressure_equals_static_when_temperatures_equal():
    p0 = stagnation_pressure(101_325.0, 288.15, 288.15)
    assert p0 == pytest.approx(101_325.0)
