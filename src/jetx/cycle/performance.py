"""Overall engine figures of merit: thrust, TSFC and the three efficiencies.

All formulae follow the standard turbojet performance definitions (Cohen,
Rogers & Saravanamuttoo, *Gas Turbine Theory*, ch. 2-3; Mattingly,
*Elements of Gas Turbine Propulsion*, ch. 3), specialised to a single
(cold) air intake stream and a convergent nozzle.
"""

from __future__ import annotations

from dataclasses import dataclass

from .components import FUEL_LHV_J_KG


@dataclass(frozen=True)
class PerformanceResult:
    """Bulk (whole-engine) performance figures, all in SI units."""

    net_thrust_n: float
    specific_thrust_n_s_kg: float  # thrust per unit *air* mass flow
    tsfc_kg_n_s: float  # fuel mass flow per unit thrust
    thermal_efficiency: float
    propulsive_efficiency: float
    overall_efficiency: float


def net_thrust(
    air_mass_flow_kg_s: float,
    fuel_air_ratio_value: float,
    exit_velocity_m_s: float,
    flight_velocity_m_s: float,
    exit_area_m2: float,
    exit_static_pressure_pa: float,
    ambient_pressure_pa: float,
) -> float:
    """Net (installed) thrust from the momentum + pressure-thrust equation.

        F = m_dot_a * [(1+f) * V8 - V0] + A8 * (p8 - pa)

    The first term is the net momentum flux change (exhaust momentum minus
    the intake ram-drag momentum); the second is the pressure-thrust term,
    which is zero for a fully-expanded (unchoked) nozzle since p8 = pa
    there, and positive for a choked nozzle where p8 > pa.
    """
    momentum_thrust = air_mass_flow_kg_s * ((1.0 + fuel_air_ratio_value) * exit_velocity_m_s - flight_velocity_m_s)
    pressure_thrust = exit_area_m2 * (exit_static_pressure_pa - ambient_pressure_pa)
    return momentum_thrust + pressure_thrust


def thermal_efficiency(
    fuel_air_ratio_value: float,
    exit_velocity_m_s: float,
    flight_velocity_m_s: float,
    fuel_lhv_j_kg: float = FUEL_LHV_J_KG,
) -> float:
    """Thermal efficiency: kinetic-energy gain rate / fuel chemical energy rate.

        eta_th = [(1+f)*V8^2 - V0^2] / (2*f*QR)

    This is the fraction of the fuel's chemical energy that ends up as
    useful kinetic-energy rise of the working fluid (the rest is exhausted
    as waste heat/entropy). It says nothing about how well that KE rise is
    converted into thrust power — that is the propulsive efficiency below.
    """
    numerator = (1.0 + fuel_air_ratio_value) * exit_velocity_m_s**2 - flight_velocity_m_s**2
    denominator = 2.0 * fuel_air_ratio_value * fuel_lhv_j_kg
    return numerator / denominator


def propulsive_efficiency(
    fuel_air_ratio_value: float,
    exit_velocity_m_s: float,
    flight_velocity_m_s: float,
) -> float:
    """Propulsive (Froude) efficiency: thrust power / kinetic-energy gain rate.

        eta_p = 2*V0*[(1+f)*V8 - V0] / [(1+f)*V8^2 - V0^2]

    Physically: for a fixed kinetic-energy addition rate, propulsive
    efficiency is maximised by accelerating a *large* mass of air by a
    *small* amount (turbofan/propeller territory) rather than a small mass
    by a large amount (turbojet territory) — which is exactly why turbojets
    have historically been noisy and fuel-thirsty compared to high-bypass
    turbofans at the same thrust.
    """
    thrust_term = (1.0 + fuel_air_ratio_value) * exit_velocity_m_s - flight_velocity_m_s
    ke_term = (1.0 + fuel_air_ratio_value) * exit_velocity_m_s**2 - flight_velocity_m_s**2
    return 2.0 * flight_velocity_m_s * thrust_term / ke_term


def overall_efficiency(thermal_eff: float, propulsive_eff: float) -> float:
    """Overall efficiency is simply the product of the two: eta_o = eta_th * eta_p.

    Equivalently, eta_o = (thrust power delivered) / (fuel chemical power
    supplied) = F*V0 / (m_dot_f * QR) — the single number that determines
    fuel burn for a given thrust and flight speed.
    """
    return thermal_eff * propulsive_eff


def tsfc(fuel_mass_flow_kg_s: float, thrust_n: float) -> float:
    """Thrust-specific fuel consumption, kg fuel per (newton * second).

        TSFC = m_dot_f / F

    Multiply by 3600 for kg/(N*h), or use
    ``jetx.common.units.tsfc_si_to_lb_lbf_hr`` for the US ``lb/(lbf*hr)``
    convention seen on most engine data sheets.
    """
    return fuel_mass_flow_kg_s / thrust_n
