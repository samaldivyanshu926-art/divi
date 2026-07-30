"""``TurbojetEngine``: wires the component models into a full cycle.

This is the "orchestration" layer — it owns no thermodynamics itself
(that all lives in :mod:`components` and :mod:`performance`); it just
calls each component in the right order, station by station, and packages
the result into a single dataclass that is easy to dump to a CSV row or
plot.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from . import components as comp
from . import performance as perf
from .atmosphere import GAMMA_AIR, isa, stagnation_pressure, stagnation_temperature


@dataclass(frozen=True)
class FlightCondition:
    """Operating point at which the cycle is evaluated.

    ``mach`` = 0 with ``altitude_m`` = 0 represents a static, sea-level
    test-bed run — the condition used throughout Project 2.
    """

    altitude_m: float = 0.0
    mach: float = 0.0


@dataclass(frozen=True)
class EngineDesign:
    """The five design choices that define a turbojet cycle."""

    air_mass_flow_kg_s: float
    intake: comp.IntakeParams
    compressor: comp.CompressorParams
    combustor: comp.CombustorParams
    turbine: comp.TurbineParams
    nozzle: comp.NozzleParams


@dataclass(frozen=True)
class CycleResult:
    """Full station-by-station and bulk-performance result of one cycle run.

    Flattened (rather than nested) deliberately, so ``asdict(result)`` is
    already a single-level dict suitable for a pandas DataFrame row / CSV
    column set.
    """

    altitude_m: float
    mach: float
    pressure_ratio: float
    turbine_inlet_temp_k: float

    t0_k: float
    p0_pa: float
    t02_k: float
    p02_pa: float
    t03_k: float
    p03_pa: float
    t04_k: float
    p04_pa: float
    t05_k: float
    p05_pa: float
    t8_k: float
    p8_pa: float
    v8_m_s: float
    nozzle_choked: bool

    fuel_air_ratio: float
    fuel_mass_flow_kg_s: float
    net_thrust_n: float
    specific_thrust_n_s_kg: float
    tsfc_kg_n_s: float
    tsfc_kg_n_hr: float
    thermal_efficiency: float
    propulsive_efficiency: float
    overall_efficiency: float

    def to_dict(self) -> dict:
        """Flat dict representation, e.g. for ``pandas.DataFrame(records)``."""
        return asdict(self)


class TurbojetEngine:
    """A single-spool turbojet, evaluated at a chosen design point.

    Example
    -------
    >>> design = EngineDesign(
    ...     air_mass_flow_kg_s=50.0,
    ...     intake=comp.IntakeParams(),
    ...     compressor=comp.CompressorParams(pressure_ratio=12.0),
    ...     combustor=comp.CombustorParams(turbine_inlet_temp_k=1400.0),
    ...     turbine=comp.TurbineParams(),
    ...     nozzle=comp.NozzleParams(),
    ... )
    >>> engine = TurbojetEngine(design)
    >>> result = engine.run(FlightCondition(altitude_m=0.0, mach=0.0))
    >>> round(result.net_thrust_n, 0) > 0
    True
    """

    def __init__(self, design: EngineDesign):
        self.design = design

    def run(self, flight_condition: FlightCondition) -> CycleResult:
        """Evaluate the full cycle at ``flight_condition`` and return results."""
        atm = isa(flight_condition.altitude_m)
        v0 = flight_condition.mach * atm.speed_of_sound_m_s

        # Station 0: freestream stagnation conditions.
        t0_stag = stagnation_temperature(atm.temperature_k, flight_condition.mach, GAMMA_AIR)
        p0_stag = stagnation_pressure(atm.pressure_pa, atm.temperature_k, t0_stag, GAMMA_AIR)

        station0 = comp.StationState(
            pressure_pa=p0_stag, temperature_k=t0_stag, mass_flow_kg_s=self.design.air_mass_flow_kg_s
        )

        # Station 2: after the intake.
        station2 = comp.intake(p0_stag, t0_stag, self.design.intake)
        station2 = comp.StationState(
            pressure_pa=station2.pressure_pa,
            temperature_k=station2.temperature_k,
            mass_flow_kg_s=self.design.air_mass_flow_kg_s,
        )

        # Station 3: after the compressor.
        station3 = comp.compressor(station2, self.design.compressor)
        wc = comp.compressor_specific_work(station2, station3)

        # Station 4: after the combustor.
        station4, f = comp.combustor(station3, self.design.combustor)

        # Station 5: after the turbine.
        station5 = comp.turbine(station4, wc, f, self.design.turbine)

        # Station 8: nozzle exit.
        nozzle_result = comp.nozzle(station5, atm.pressure_pa, self.design.nozzle)

        fuel_mass_flow = f * self.design.air_mass_flow_kg_s

        thrust = perf.net_thrust(
            air_mass_flow_kg_s=self.design.air_mass_flow_kg_s,
            fuel_air_ratio_value=f,
            exit_velocity_m_s=nozzle_result.exit_velocity_m_s,
            flight_velocity_m_s=v0,
            exit_area_m2=nozzle_result.exit_area_m2,
            exit_static_pressure_pa=nozzle_result.exit_static_pressure_pa,
            ambient_pressure_pa=atm.pressure_pa,
        )
        specific_thrust = thrust / self.design.air_mass_flow_kg_s
        tsfc_val = perf.tsfc(fuel_mass_flow, thrust)

        if v0 > 0.0:
            eta_th = perf.thermal_efficiency(f, nozzle_result.exit_velocity_m_s, v0)
            eta_p = perf.propulsive_efficiency(f, nozzle_result.exit_velocity_m_s, v0)
        else:
            # At V0 = 0 (static test-bed condition) propulsive efficiency is
            # zero by definition (no thrust power is done on the vehicle),
            # so overall efficiency is also zero; thermal efficiency is
            # still meaningful and is reported on its own.
            eta_th = perf.thermal_efficiency(f, nozzle_result.exit_velocity_m_s, max(v0, 1e-6))
            eta_p = 0.0
        eta_o = perf.overall_efficiency(eta_th, eta_p)

        return CycleResult(
            altitude_m=flight_condition.altitude_m,
            mach=flight_condition.mach,
            pressure_ratio=self.design.compressor.pressure_ratio,
            turbine_inlet_temp_k=self.design.combustor.turbine_inlet_temp_k,
            t0_k=station0.temperature_k,
            p0_pa=station0.pressure_pa,
            t02_k=station2.temperature_k,
            p02_pa=station2.pressure_pa,
            t03_k=station3.temperature_k,
            p03_pa=station3.pressure_pa,
            t04_k=station4.temperature_k,
            p04_pa=station4.pressure_pa,
            t05_k=station5.temperature_k,
            p05_pa=station5.pressure_pa,
            t8_k=nozzle_result.exit_static_temp_k,
            p8_pa=nozzle_result.exit_static_pressure_pa,
            v8_m_s=nozzle_result.exit_velocity_m_s,
            nozzle_choked=nozzle_result.is_choked,
            fuel_air_ratio=f,
            fuel_mass_flow_kg_s=fuel_mass_flow,
            net_thrust_n=thrust,
            specific_thrust_n_s_kg=specific_thrust,
            tsfc_kg_n_s=tsfc_val,
            tsfc_kg_n_hr=tsfc_val * 3600.0,
            thermal_efficiency=eta_th,
            propulsive_efficiency=eta_p,
            overall_efficiency=eta_o,
        )
