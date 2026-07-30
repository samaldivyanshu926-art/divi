"""International Standard Atmosphere (ISA), troposphere + lower stratosphere.

Reference: ICAO Doc 7488, *Manual of the ICAO Standard Atmosphere* (1993).
Valid from sea level to 20 km, which covers every altitude this simulator
is used at.

Model
-----
Troposphere (0 - 11 000 m): temperature falls linearly with altitude,
    T(h) = T_sl - L * h
and pressure follows the hydrostatic + ideal-gas-law integral of a linear
temperature lapse:
    p(h) = p_sl * (T(h) / T_sl) ** (g0 / (L * R))

Isothermal lower stratosphere (11 000 - 20 000 m): temperature is constant
at T_11 = 216.65 K, and pressure follows the isothermal hydrostatic
integral:
    p(h) = p_11 * exp(-g0 * (h - 11000) / (R * T_11))

Density follows from the ideal gas law, rho = p / (R * T), and the local
speed of sound from a0 = sqrt(gamma * R * T).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --- ISA sea-level reference values and physical constants -----------------
T_SL: float = 288.15  # K, sea-level standard temperature
P_SL: float = 101_325.0  # Pa, sea-level standard pressure
L: float = 0.0065  # K/m, troposphere temperature lapse rate
G0: float = 9.80665  # m/s^2, standard gravitational acceleration
R_AIR: float = 287.05287  # J/(kg*K), specific gas constant for dry air
GAMMA_AIR: float = 1.4  # ratio of specific heats for cold (unburned) air
TROPOPAUSE_ALTITUDE: float = 11_000.0  # m
T_TROPOPAUSE: float = T_SL - L * TROPOPAUSE_ALTITUDE  # 216.65 K
STRATOSPHERE_CEILING: float = 20_000.0  # m, upper limit of this model


@dataclass(frozen=True)
class AtmosphericState:
    """Static (i.e. not stagnation) atmospheric properties at one altitude."""

    altitude_m: float
    temperature_k: float
    pressure_pa: float
    density_kg_m3: float
    speed_of_sound_m_s: float


def isa(altitude_m: float) -> AtmosphericState:
    """Return ISA static conditions at ``altitude_m`` (0-20,000 m).

    Parameters
    ----------
    altitude_m:
        Geopotential altitude above sea level, in metres.

    Raises
    ------
    ValueError
        If ``altitude_m`` is outside the [0, 20000] m validity range of
        this two-layer model.
    """
    if not (0.0 <= altitude_m <= STRATOSPHERE_CEILING):
        raise ValueError(
            f"altitude_m={altitude_m} outside supported ISA range "
            f"[0, {STRATOSPHERE_CEILING}] m"
        )

    if altitude_m <= TROPOPAUSE_ALTITUDE:
        temperature_k = T_SL - L * altitude_m
        pressure_pa = P_SL * (temperature_k / T_SL) ** (G0 / (L * R_AIR))
    else:
        temperature_k = T_TROPOPAUSE
        p_tropopause = P_SL * (T_TROPOPAUSE / T_SL) ** (G0 / (L * R_AIR))
        pressure_pa = p_tropopause * np.exp(
            -G0 * (altitude_m - TROPOPAUSE_ALTITUDE) / (R_AIR * T_TROPOPAUSE)
        )

    density_kg_m3 = pressure_pa / (R_AIR * temperature_k)
    speed_of_sound_m_s = float(np.sqrt(GAMMA_AIR * R_AIR * temperature_k))

    return AtmosphericState(
        altitude_m=altitude_m,
        temperature_k=temperature_k,
        pressure_pa=pressure_pa,
        density_kg_m3=density_kg_m3,
        speed_of_sound_m_s=speed_of_sound_m_s,
    )


def stagnation_temperature(static_temp_k: float, mach: float, gamma: float = GAMMA_AIR) -> float:
    """Stagnation (total) temperature from static temperature and Mach number.

    Derived from the steady-flow energy equation for an adiabatic,
    work-free duct (h0 = h + V^2/2), written in terms of Mach number:

        T0 / T = 1 + (gamma - 1) / 2 * M^2
    """
    return static_temp_k * (1.0 + (gamma - 1.0) / 2.0 * mach**2)


def stagnation_pressure(
    static_press_pa: float, static_temp_k: float, stagnation_temp_k: float, gamma: float = GAMMA_AIR
) -> float:
    """Stagnation (total) pressure via the isentropic T-p relation.

        p0 / p = (T0 / T) ** (gamma / (gamma - 1))

    This is only valid for an isentropic (reversible, adiabatic)
    deceleration; any real stagnation-pressure loss (e.g. intake spillage,
    duct friction) must be applied afterwards as a separate efficiency or
    pressure-recovery factor.
    """
    return static_press_pa * (stagnation_temp_k / static_temp_k) ** (gamma / (gamma - 1.0))
