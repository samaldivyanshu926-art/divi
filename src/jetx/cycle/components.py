"""Thermodynamic models for each turbojet component.

Every function takes station conditions in and returns station conditions
out, mirroring how a gas-turbine performance textbook walks the cycle
station by station:

    0 (freestream) -> 2 (compressor inlet) -> 3 (compressor exit /
    combustor inlet) -> 4 (combustor exit / turbine inlet) -> 5 (turbine
    exit / nozzle inlet) -> 8 (nozzle exit)

Two constant-property gas models are used, as is standard practice for a
hand/spreadsheet-level real cycle analysis (Cohen, Rogers & Saravanamuttoo,
*Gas Turbine Theory*, ch. 2):

* "cold" air (stations 0-3, unburned)   : cp = 1005 J/(kg K), gamma = 1.4
* "hot" gas  (stations 4-8, combustion products): cp = 1148 J/(kg K), gamma = 1.333

Using two distinct-but-constant property sets captures most of the effect
of combustion products having a different composition/temperature than
cold air, without requiring a full variable-specific-heat gas table. This
is a deliberate, documented simplification — see docs/assumptions_and_limitations.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --- Gas property constants -------------------------------------------------
CP_COLD: float = 1005.0  # J/(kg*K), cold air
GAMMA_COLD: float = 1.4
CP_HOT: float = 1148.0  # J/(kg*K), hot combustion gas
GAMMA_HOT: float = 1.333
FUEL_LHV_J_KG: float = 43.0e6  # J/kg, kerosene (Jet A) lower heating value


@dataclass(frozen=True)
class StationState:
    """Total (stagnation) conditions and mass flow at one cycle station."""

    pressure_pa: float
    temperature_k: float
    mass_flow_kg_s: float


@dataclass(frozen=True)
class IntakeParams:
    """Subsonic intake (diffuser) parameters."""

    pressure_recovery: float = 0.98  # p02/p0_stagnation-freestream, intake total-pressure loss


@dataclass(frozen=True)
class CompressorParams:
    """Compressor design parameters."""

    pressure_ratio: float  # p03 / p02
    isentropic_efficiency: float = 0.85


@dataclass(frozen=True)
class CombustorParams:
    """Combustor design parameters."""

    turbine_inlet_temp_k: float  # T04, the key cycle design variable
    combustion_efficiency: float = 0.98
    pressure_loss_fraction: float = 0.05  # (p03 - p04) / p03


@dataclass(frozen=True)
class TurbineParams:
    """Turbine design parameters."""

    isentropic_efficiency: float = 0.90
    mechanical_efficiency: float = 0.99  # shaft/bearing losses between turbine and compressor


@dataclass(frozen=True)
class NozzleParams:
    """Convergent propelling-nozzle design parameters."""

    isentropic_efficiency: float = 0.97


def intake(
    freestream_stag_pressure_pa: float, freestream_stag_temp_k: float, params: IntakeParams
) -> StationState:
    """Station 2: compressor-face conditions after intake pressure recovery.

    The intake does no work, so stagnation temperature is unchanged
    (T02 = T0). Stagnation pressure is de-rated by the pressure-recovery
    factor to represent duct friction and (for a real, non-pitot intake)
    spillage/boundary-layer losses:

        p02 = pressure_recovery * p0
    """
    return StationState(
        pressure_pa=params.pressure_recovery * freestream_stag_pressure_pa,
        temperature_k=freestream_stag_temp_k,
        mass_flow_kg_s=float("nan"),  # filled in by the caller (engine.py)
    )


def compressor(inlet: StationState, params: CompressorParams) -> StationState:
    """Station 3: compressor exit conditions.

    Ideal (isentropic) exit temperature from the isentropic p-T relation
    for the pressure ratio rc = p03/p02:

        T03s / T02 = rc ** ((gamma_c - 1) / gamma_c)

    The isentropic efficiency is defined as the ratio of ideal to actual
    specific work for the same pressure rise (it is *less* than 1 because
    real compression generates entropy, so the actual temperature rise is
    always larger than the ideal one for the same pressure ratio):

        eta_c = (T03s - T02) / (T03 - T02)
        =>  T03 = T02 + (T03s - T02) / eta_c
    """
    t03s_over_t02 = params.pressure_ratio ** ((GAMMA_COLD - 1.0) / GAMMA_COLD)
    t03s = inlet.temperature_k * t03s_over_t02
    t03 = inlet.temperature_k + (t03s - inlet.temperature_k) / params.isentropic_efficiency
    p03 = inlet.pressure_pa * params.pressure_ratio
    return StationState(pressure_pa=p03, temperature_k=t03, mass_flow_kg_s=inlet.mass_flow_kg_s)


def compressor_specific_work(inlet: StationState, outlet: StationState) -> float:
    """Specific work absorbed by the compressor, J/kg of air: wc = cpc*(T03-T02)."""
    return CP_COLD * (outlet.temperature_k - inlet.temperature_k)


def fuel_air_ratio(
    compressor_exit_temp_k: float,
    turbine_inlet_temp_k: float,
    combustion_efficiency: float,
    fuel_lhv_j_kg: float = FUEL_LHV_J_KG,
) -> float:
    """Fuel-air ratio ``f = m_dot_fuel / m_dot_air`` from an energy balance.

    Per unit mass of air entering the combustor, energy in (sensible heat
    of the air plus the chemical energy released by burning f kg of fuel
    per kg of air, discounted by combustion efficiency) equals energy out
    (sensible heat of the (1+f) kg of combustion products leaving at T04):

        cpc*T03 + f*eta_b*QR = (1+f)*cph*T04

    Solving for f:

        f = (cph*T04 - cpc*T03) / (eta_b*QR - cph*T04)

    This is the standard combustor energy-balance relation used in
    real-cycle performance analysis (Cohen, Rogers & Saravanamuttoo, ch. 2;
    Mattingly ch. 2). It correctly accounts for the added fuel mass
    flowing through the turbine and nozzle, which a naive
    ``f = cp*(T04-T03)/QR`` approximation ignores.
    """
    numerator = CP_HOT * turbine_inlet_temp_k - CP_COLD * compressor_exit_temp_k
    denominator = combustion_efficiency * fuel_lhv_j_kg - CP_HOT * turbine_inlet_temp_k
    if denominator <= 0.0:
        raise ValueError(
            "Combustor energy balance has no physical solution "
            "(turbine inlet temperature too close to fuel adiabatic flame limit)."
        )
    return numerator / denominator


def combustor(inlet: StationState, params: CombustorParams) -> tuple[StationState, float]:
    """Station 4: combustor exit conditions and fuel-air ratio.

    Pressure loss is modelled as a fixed fraction of the inlet pressure
    (typical values 3-6% for an annular/can-annular combustor):

        p04 = p03 * (1 - pressure_loss_fraction)

    Returns the station-4 state (with mass flow already inflated by the
    fuel addition, m_dot_4 = m_dot_3 * (1 + f)) and the fuel-air ratio f.
    """
    f = fuel_air_ratio(
        compressor_exit_temp_k=inlet.temperature_k,
        turbine_inlet_temp_k=params.turbine_inlet_temp_k,
        combustion_efficiency=params.combustion_efficiency,
    )
    p04 = inlet.pressure_pa * (1.0 - params.pressure_loss_fraction)
    outlet = StationState(
        pressure_pa=p04,
        temperature_k=params.turbine_inlet_temp_k,
        mass_flow_kg_s=inlet.mass_flow_kg_s * (1.0 + f),
    )
    return outlet, f


def turbine(
    inlet: StationState,
    compressor_specific_work_j_kg: float,
    fuel_air_ratio_value: float,
    params: TurbineParams,
) -> StationState:
    """Station 5: turbine exit conditions from a shaft power balance.

    Single-spool, no bleed/offtake: turbine shaft work must supply exactly
    the compressor's work demand, after mechanical losses:

        (1+f) * cph * (T04 - T05) * eta_mech = wc
        =>  T04 - T05 = wc / (eta_mech * (1+f) * cph)

    The corresponding pressure drop follows from the turbine's isentropic
    efficiency, defined (opposite sense to the compressor's) as actual
    work over ideal work for the same temperature drop:

        eta_t = (T04 - T05) / (T04 - T05s)
        =>  T05s = T04 - (T04 - T05) / eta_t
        p05 / p04 = (T05s / T04) ** (gamma_h / (gamma_h - 1))   [isentropic]
    """
    delta_t = compressor_specific_work_j_kg / (
        params.mechanical_efficiency * (1.0 + fuel_air_ratio_value) * CP_HOT
    )
    t05 = inlet.temperature_k - delta_t
    t05s = inlet.temperature_k - delta_t / params.isentropic_efficiency
    p05 = inlet.pressure_pa * (t05s / inlet.temperature_k) ** (GAMMA_HOT / (GAMMA_HOT - 1.0))
    return StationState(pressure_pa=p05, temperature_k=t05, mass_flow_kg_s=inlet.mass_flow_kg_s)


@dataclass(frozen=True)
class NozzleResult:
    """Nozzle exit conditions plus the choked/unchoked flag."""

    exit_velocity_m_s: float
    exit_static_pressure_pa: float
    exit_static_temp_k: float
    exit_area_m2: float
    is_choked: bool


def nozzle_critical_pressure_ratio(eta_n: float, gamma: float = GAMMA_HOT) -> float:
    """Critical (choking) stagnation-to-static pressure ratio p05/p_crit.

    For an ideal (eta_n = 1) convergent nozzle the classical result is

        (p0/p*)_ideal = ((gamma+1)/2) ** (gamma/(gamma-1))

    A non-ideal nozzle needs a slightly higher pressure ratio to choke,
    because friction reduces the achievable exit velocity for a given
    pressure drop. The standard correction (Cohen, Rogers & Saravanamuttoo,
    ch. 2) folds the nozzle isentropic efficiency into the exponent's base:

        (p0/p*) = [1 - (1/eta_n) * (gamma-1)/(gamma+1)] ** (-gamma/(gamma-1))
    """
    base = 1.0 - (1.0 / eta_n) * (gamma - 1.0) / (gamma + 1.0)
    return base ** (-gamma / (gamma - 1.0))


def nozzle(
    inlet: StationState,
    ambient_pressure_pa: float,
    params: NozzleParams,
) -> NozzleResult:
    """Convergent propelling nozzle: expand station-5 gas to (or towards) ambient.

    Two regimes:

    1. **Unchoked** (p05/pa < critical ratio): the jet expands fully to
       ambient static pressure. Ideal exit temperature from the isentropic
       relation, actual exit temperature via the nozzle isentropic
       efficiency (defined as actual/ideal enthalpy drop):

           T8s = T05 * (pa/p05) ** ((gamma_h-1)/gamma_h)
           T8  = T05 - eta_n * (T05 - T8s)
           V8  = sqrt(2 * cph * (T05 - T8))            [steady-flow energy eq.]

       Exit static pressure equals ambient, so there is no pressure-thrust
       term.

    2. **Choked** (p05/pa >= critical ratio): the nozzle throat is at
       Mach 1 and cannot expand further no matter how low pa is. Exit
       (=throat) static temperature and pressure follow from the sonic
       condition, and there is a residual pressure-thrust term because the
       exit static pressure exceeds ambient:

           T8 = 2*T05 / (gamma_h + 1)
           p8 = p05 / (p05/p*)_critical
           V8 = sqrt(gamma_h * R_hot * T8)              [sonic velocity]

    The exit area is sized from mass continuity, rho8*A8*V8 = m_dot_5, so
    that thrust calculations needing A8 (pressure-thrust term) are
    self-consistent.
    """
    r_hot = CP_HOT * (GAMMA_HOT - 1.0) / GAMMA_HOT  # specific gas constant of hot gas, from cp & gamma
    pressure_ratio_available = inlet.pressure_pa / ambient_pressure_pa
    critical_ratio = nozzle_critical_pressure_ratio(params.isentropic_efficiency)

    if pressure_ratio_available >= critical_ratio:
        # Choked: throat is sonic.
        t8 = 2.0 * inlet.temperature_k / (GAMMA_HOT + 1.0)
        p8 = inlet.pressure_pa / critical_ratio
        v8 = float(np.sqrt(GAMMA_HOT * r_hot * t8))
        is_choked = True
    else:
        # Unchoked: fully expanded to ambient.
        t8s = inlet.temperature_k * (ambient_pressure_pa / inlet.pressure_pa) ** (
            (GAMMA_HOT - 1.0) / GAMMA_HOT
        )
        t8 = inlet.temperature_k - params.isentropic_efficiency * (inlet.temperature_k - t8s)
        p8 = ambient_pressure_pa
        v8 = float(np.sqrt(max(2.0 * CP_HOT * (inlet.temperature_k - t8), 0.0)))
        is_choked = False

    rho8 = p8 / (r_hot * t8)
    exit_area_m2 = inlet.mass_flow_kg_s / (rho8 * v8) if v8 > 0.0 else float("nan")

    return NozzleResult(
        exit_velocity_m_s=v8,
        exit_static_pressure_pa=p8,
        exit_static_temp_k=t8,
        exit_area_m2=exit_area_m2,
        is_choked=is_choked,
    )
