"""Unit conversion helpers used across all three projects.

Everything internal to the ``jetx`` package works in SI base/derived units
(kelvin, pascal, kilogram, metre, second, newton, watt). These helpers exist
only at the *boundary* — for presenting results in the units a test engineer
actually reads off a data sheet (psi, degF, RPM-vs-percent, lb, etc.).

Keeping a single, well-tested conversion module avoids the classic failure
mode of unit factors being re-typed (and mistyped) in five different files.
"""

from __future__ import annotations

# --- Temperature -----------------------------------------------------------

def celsius_to_kelvin(t_c: float) -> float:
    """Convert Celsius to kelvin."""
    return t_c + 273.15


def kelvin_to_celsius(t_k: float) -> float:
    """Convert kelvin to Celsius."""
    return t_k - 273.15


def fahrenheit_to_kelvin(t_f: float) -> float:
    """Convert Fahrenheit to kelvin."""
    return (t_f - 32.0) * 5.0 / 9.0 + 273.15


def kelvin_to_fahrenheit(t_k: float) -> float:
    """Convert kelvin to Fahrenheit."""
    return (t_k - 273.15) * 9.0 / 5.0 + 32.0


# --- Pressure ----------------------------------------------------------------
# 1 psi = 6894.757293168 Pa (exact definition via 1 lbf/in^2, IEEE/ASTM value)
PSI_TO_PA: float = 6894.757293168
BAR_TO_PA: float = 1.0e5
ATM_TO_PA: float = 101_325.0


def psi_to_pa(p_psi: float) -> float:
    """Convert pounds-force per square inch to pascal."""
    return p_psi * PSI_TO_PA


def pa_to_psi(p_pa: float) -> float:
    """Convert pascal to pounds-force per square inch."""
    return p_pa / PSI_TO_PA


def bar_to_pa(p_bar: float) -> float:
    """Convert bar to pascal."""
    return p_bar * BAR_TO_PA


def pa_to_bar(p_pa: float) -> float:
    """Convert pascal to bar."""
    return p_pa / BAR_TO_PA


# --- Force ---------------------------------------------------------------
# 1 lbf = 4.4482216152605 N (exact, from the standard gravity definition)
LBF_TO_N: float = 4.4482216152605


def lbf_to_n(f_lbf: float) -> float:
    """Convert pounds-force to newtons."""
    return f_lbf * LBF_TO_N


def n_to_lbf(f_n: float) -> float:
    """Convert newtons to pounds-force."""
    return f_n / LBF_TO_N


# --- Mass flow / SFC -------------------------------------------------------
LB_TO_KG: float = 0.45359237
HOUR_TO_S: float = 3600.0


def kg_per_s_to_lb_per_hr(mdot_kg_s: float) -> float:
    """Convert a mass flow rate from kg/s to lb/hr."""
    return mdot_kg_s / LB_TO_KG * HOUR_TO_S


def tsfc_si_to_lb_lbf_hr(tsfc_kg_n_s: float) -> float:
    """Convert TSFC from kg fuel /(N*s) to lb fuel /(lbf*hr).

    This is the unit convention most commonly quoted on US engine data
    sheets (``lb/(lbf*hr)``), so it is kept as an explicit, named
    conversion rather than left to the reader to derive.
    """
    return tsfc_kg_n_s * (1.0 / LB_TO_KG) * LBF_TO_N * HOUR_TO_S


# --- Rotational speed --------------------------------------------------------

def rad_s_to_rpm(omega_rad_s: float) -> float:
    """Convert angular velocity in rad/s to revolutions per minute."""
    return omega_rad_s * 60.0 / (2.0 * 3.141592653589793)


def rpm_to_rad_s(n_rpm: float) -> float:
    """Convert revolutions per minute to angular velocity in rad/s."""
    return n_rpm * 2.0 * 3.141592653589793 / 60.0


# --- Length ------------------------------------------------------------------
MM_TO_M: float = 1.0e-3
IN_TO_M: float = 0.0254


def mm_to_m(length_mm: float) -> float:
    """Convert millimetres to metres."""
    return length_mm * MM_TO_M


def in_to_mm(length_in: float) -> float:
    """Convert inches to millimetres."""
    return length_in * IN_TO_M / MM_TO_M
