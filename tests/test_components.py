"""Unit tests for the individual turbojet component models."""

import pytest

from jetx.cycle import components as comp


def test_compressor_temp_rise_positive_and_efficiency_penalizes():
    inlet = comp.StationState(pressure_pa=101_325.0, temperature_k=288.15, mass_flow_kg_s=50.0)
    params_ideal = comp.CompressorParams(pressure_ratio=10.0, isentropic_efficiency=1.0)
    params_real = comp.CompressorParams(pressure_ratio=10.0, isentropic_efficiency=0.85)

    ideal_out = comp.compressor(inlet, params_ideal)
    real_out = comp.compressor(inlet, params_real)

    assert real_out.temperature_k > ideal_out.temperature_k > inlet.temperature_k
    assert real_out.pressure_pa == pytest.approx(ideal_out.pressure_pa)  # pressure ratio is fixed by design
    assert real_out.pressure_pa == pytest.approx(1_013_250.0)


def test_compressor_specific_work_matches_cp_delta_t():
    inlet = comp.StationState(pressure_pa=101_325.0, temperature_k=288.15, mass_flow_kg_s=50.0)
    outlet = comp.compressor(inlet, comp.CompressorParams(pressure_ratio=8.0, isentropic_efficiency=0.85))
    work = comp.compressor_specific_work(inlet, outlet)
    assert work == pytest.approx(comp.CP_COLD * (outlet.temperature_k - inlet.temperature_k))


def test_fuel_air_ratio_increases_with_turbine_inlet_temperature():
    f_low = comp.fuel_air_ratio(600.0, 1200.0, 0.98)
    f_high = comp.fuel_air_ratio(600.0, 1600.0, 0.98)
    assert 0.0 < f_low < f_high
    # Realistic turbojet fuel-air ratios sit roughly in the 0.01-0.03 band.
    assert 0.005 < f_low < 0.05
    assert 0.005 < f_high < 0.05


def test_fuel_air_ratio_rejects_non_physical_regime():
    # The energy balance has no physical solution once cph*T04 alone exceeds
    # the fuel's available chemical energy (eta_b*QR) -- roughly T04 > 36,700 K
    # for kerosene, i.e. this guard only ever fires for a clearly bogus input.
    with pytest.raises(ValueError):
        comp.fuel_air_ratio(600.0, 40_000.0, 0.98)


def test_combustor_applies_pressure_loss_and_inflates_mass_flow():
    inlet = comp.StationState(pressure_pa=1_000_000.0, temperature_k=600.0, mass_flow_kg_s=50.0)
    params = comp.CombustorParams(
        turbine_inlet_temp_k=1400.0, combustion_efficiency=0.98, pressure_loss_fraction=0.05
    )
    outlet, f = comp.combustor(inlet, params)
    assert outlet.pressure_pa == pytest.approx(950_000.0)
    assert outlet.temperature_k == pytest.approx(1400.0)
    assert outlet.mass_flow_kg_s == pytest.approx(50.0 * (1.0 + f))
    assert f > 0.0


def test_turbine_work_balances_compressor_work():
    station4 = comp.StationState(pressure_pa=950_000.0, temperature_k=1400.0, mass_flow_kg_s=51.0)
    f = 0.02
    wc = 250_000.0  # J/kg
    params = comp.TurbineParams(isentropic_efficiency=0.90, mechanical_efficiency=0.99)
    station5 = comp.turbine(station4, wc, f, params)

    # Recover the work the turbine delivered and check it balances wc (within mech. losses).
    delivered_work = (1.0 + f) * comp.CP_HOT * (station4.temperature_k - station5.temperature_k)
    assert delivered_work * params.mechanical_efficiency == pytest.approx(wc, rel=1e-6)
    assert station5.temperature_k < station4.temperature_k
    assert station5.pressure_pa < station4.pressure_pa


def test_nozzle_critical_pressure_ratio_matches_ideal_formula_at_eta_one():
    ratio = comp.nozzle_critical_pressure_ratio(eta_n=1.0, gamma=comp.GAMMA_HOT)
    expected = ((comp.GAMMA_HOT + 1.0) / 2.0) ** (comp.GAMMA_HOT / (comp.GAMMA_HOT - 1.0))
    assert ratio == pytest.approx(expected)


def test_nozzle_unchoked_exit_pressure_equals_ambient():
    inlet = comp.StationState(pressure_pa=150_000.0, temperature_k=900.0, mass_flow_kg_s=51.0)
    params = comp.NozzleParams(isentropic_efficiency=0.97)
    result = comp.nozzle(inlet, ambient_pressure_pa=101_325.0, params=params)
    assert not result.is_choked
    assert result.exit_static_pressure_pa == pytest.approx(101_325.0)
    assert result.exit_velocity_m_s > 0.0


def test_nozzle_choked_when_pressure_ratio_high():
    inlet = comp.StationState(pressure_pa=400_000.0, temperature_k=900.0, mass_flow_kg_s=51.0)
    params = comp.NozzleParams(isentropic_efficiency=0.97)
    result = comp.nozzle(inlet, ambient_pressure_pa=101_325.0, params=params)
    assert result.is_choked
    assert result.exit_static_pressure_pa > 101_325.0
