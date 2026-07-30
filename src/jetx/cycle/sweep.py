"""Parametric sweeps used to build turbojet performance maps.

Two sweeps are implemented, matching the two classic performance-map axes
for a single-spool turbojet: compressor pressure ratio, and turbine inlet
temperature (TIT). Both return a tidy ``pandas.DataFrame`` — one row per
cycle evaluation — ready to plot or write to CSV.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from . import components as comp
from .engine import EngineDesign, FlightCondition, TurbojetEngine

DEFAULT_AIR_MASS_FLOW_KG_S: float = 50.0


def _base_design(
    air_mass_flow_kg_s: float,
    pressure_ratio: float,
    turbine_inlet_temp_k: float,
) -> EngineDesign:
    """Build an :class:`EngineDesign` with representative component efficiencies.

    The efficiency/loss values (compressor eta=0.85, turbine eta=0.90,
    combustor pressure loss=5%, etc.) are typical mid-size military/
    commercial turbojet values from published cycle-analysis worked
    examples, not the parameters of any specific named engine.
    """
    return EngineDesign(
        air_mass_flow_kg_s=air_mass_flow_kg_s,
        intake=comp.IntakeParams(pressure_recovery=0.98),
        compressor=comp.CompressorParams(pressure_ratio=pressure_ratio, isentropic_efficiency=0.85),
        combustor=comp.CombustorParams(
            turbine_inlet_temp_k=turbine_inlet_temp_k,
            combustion_efficiency=0.98,
            pressure_loss_fraction=0.05,
        ),
        turbine=comp.TurbineParams(isentropic_efficiency=0.90, mechanical_efficiency=0.99),
        nozzle=comp.NozzleParams(isentropic_efficiency=0.97),
    )


def pressure_ratio_sweep(
    pressure_ratios: Sequence[float],
    turbine_inlet_temps_k: Sequence[float],
    flight_condition: FlightCondition | None = None,
    air_mass_flow_kg_s: float = DEFAULT_AIR_MASS_FLOW_KG_S,
) -> pd.DataFrame:
    """Sweep compressor pressure ratio at each of several fixed TIT values.

    This is the sweep that produces the textbook "specific thrust peaks at
    an intermediate pressure ratio, TSFC has a shallow minimum" performance
    map: for a fixed TIT, raising rc increases thermal efficiency (higher
    peak cycle pressure/temperature) but reduces specific thrust once rc is
    high enough that further compression eats into the turbine's available
    expansion work more than it gains in efficiency.
    """
    flight_condition = flight_condition or FlightCondition(altitude_m=0.0, mach=0.0)
    records = []
    for tit in turbine_inlet_temps_k:
        for rc in pressure_ratios:
            design = _base_design(air_mass_flow_kg_s, rc, tit)
            engine = TurbojetEngine(design)
            result = engine.run(flight_condition)
            records.append(result.to_dict())
    return pd.DataFrame.from_records(records)


def turbine_inlet_temp_sweep(
    turbine_inlet_temps_k: Sequence[float],
    pressure_ratios: Sequence[float],
    flight_condition: FlightCondition | None = None,
    air_mass_flow_kg_s: float = DEFAULT_AIR_MASS_FLOW_KG_S,
) -> pd.DataFrame:
    """Sweep turbine inlet temperature at each of several fixed pressure ratios.

    Complementary view of the same design space: at fixed rc, raising TIT
    reliably increases specific thrust (more energy added per unit mass
    flow) — the reason turbine metallurgy/cooling technology is one of the
    biggest levers on turbojet thrust density. It does *not* reliably
    improve thermal efficiency in this model: with a convergent-only
    nozzle, once the pressure ratio is high enough to choke the nozzle
    (common at the higher rc/TIT combinations here), a growing share of
    the extra combustion enthalpy leaves as unexpanded residual heat
    rather than jet kinetic energy. See
    docs/assumptions_and_limitations.md for the full discussion.
    """
    flight_condition = flight_condition or FlightCondition(altitude_m=0.0, mach=0.0)
    records = []
    for rc in pressure_ratios:
        for tit in turbine_inlet_temps_k:
            design = _base_design(air_mass_flow_kg_s, rc, tit)
            engine = TurbojetEngine(design)
            result = engine.run(flight_condition)
            records.append(result.to_dict())
    return pd.DataFrame.from_records(records)
