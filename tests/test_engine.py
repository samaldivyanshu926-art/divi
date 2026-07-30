"""Integration tests for the full TurbojetEngine cycle."""

import pytest

from jetx.cycle import components as comp
from jetx.cycle.engine import EngineDesign, FlightCondition, TurbojetEngine


def _make_engine(
    pressure_ratio: float = 12.0, tit_k: float = 1400.0, air_mass_flow: float = 50.0
) -> TurbojetEngine:
    design = EngineDesign(
        air_mass_flow_kg_s=air_mass_flow,
        intake=comp.IntakeParams(pressure_recovery=0.98),
        compressor=comp.CompressorParams(pressure_ratio=pressure_ratio, isentropic_efficiency=0.85),
        combustor=comp.CombustorParams(
            turbine_inlet_temp_k=tit_k, combustion_efficiency=0.98, pressure_loss_fraction=0.05
        ),
        turbine=comp.TurbineParams(isentropic_efficiency=0.90, mechanical_efficiency=0.99),
        nozzle=comp.NozzleParams(isentropic_efficiency=0.97),
    )
    return TurbojetEngine(design)


def test_static_sea_level_produces_positive_thrust_and_realistic_tsfc():
    engine = _make_engine()
    result = engine.run(FlightCondition(altitude_m=0.0, mach=0.0))

    assert result.net_thrust_n > 0.0
    assert result.fuel_air_ratio > 0.0
    # Realistic static TSFC for a mid-generation turbojet: roughly 0.7-1.3 lb/(lbf*hr),
    # i.e. about 0.07-0.135 kg/(N*hr).
    assert 0.06 < result.tsfc_kg_n_hr < 0.16


def test_station_temperatures_increase_then_decrease_through_the_cycle():
    result = _make_engine().run(FlightCondition())
    assert result.t02_k < result.t03_k < result.t04_k
    assert result.t05_k < result.t04_k


def test_station_pressures_rise_through_compressor_and_fall_after():
    result = _make_engine().run(FlightCondition())
    assert result.p03_pa > result.p02_pa
    assert result.p04_pa < result.p03_pa  # combustor pressure loss
    assert result.p05_pa < result.p04_pa  # turbine expansion


def test_specific_thrust_peaks_at_intermediate_pressure_ratio():
    """Textbook trend: for fixed TIT, specific thrust peaks at an intermediate rc."""
    ratios = [4.0, 8.0, 12.0, 16.0, 20.0, 24.0]
    thrusts = [_make_engine(pressure_ratio=rc).run(FlightCondition()).specific_thrust_n_s_kg for rc in ratios]
    peak_index = thrusts.index(max(thrusts))
    assert 0 < peak_index < len(thrusts) - 1  # peak is interior, not at either sweep boundary


def test_higher_turbine_inlet_temperature_increases_thrust_and_fuel_air_ratio():
    """Raising TIT at fixed rc reliably increases specific thrust and fuel-air ratio.

    Thermal efficiency is *not* asserted to increase here: with this
    model's convergent-only nozzle, a high enough pressure ratio (as seen
    at both these design points) keeps the nozzle choked across the whole
    TIT sweep, so a growing share of the extra combustion enthalpy leaves
    as unexpanded residual heat rather than jet kinetic energy. That is a
    real, documented consequence of the convergent-nozzle simplification
    (see docs/assumptions_and_limitations.md) — a convergent-divergent
    nozzle would recover more of it as additional thrust.
    """
    low = _make_engine(tit_k=1200.0).run(FlightCondition())
    high = _make_engine(tit_k=1700.0).run(FlightCondition())
    assert high.specific_thrust_n_s_kg > low.specific_thrust_n_s_kg
    assert high.fuel_air_ratio > low.fuel_air_ratio


def test_static_condition_has_zero_propulsive_and_overall_efficiency():
    result = _make_engine().run(FlightCondition(altitude_m=0.0, mach=0.0))
    assert result.propulsive_efficiency == pytest.approx(0.0)
    assert result.overall_efficiency == pytest.approx(0.0)


def test_cruise_condition_has_positive_propulsive_efficiency():
    result = _make_engine().run(FlightCondition(altitude_m=9000.0, mach=0.8))
    assert 0.0 < result.propulsive_efficiency < 1.0
    assert 0.0 < result.overall_efficiency < 1.0


def test_result_is_flattenable_to_dict():
    result = _make_engine().run(FlightCondition())
    d = result.to_dict()
    assert d["net_thrust_n"] == result.net_thrust_n
    assert isinstance(d, dict)
