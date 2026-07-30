"""Synthetic DAQ generator: produces a realistic raw test-cell log.

There is no physical rig behind this data — it is generated from a simple,
documented physical model of how thrust, EGT, inlet pressure and RPM
co-vary during a spool-up / steady-state / spool-down test run, then
corrupted with sensor noise and a handful of deliberately-injected data
defects (dropout, stuck value, spike) so that :mod:`qa` has something real
to catch. The point of this project is the **calibration/reduction/QA
pipeline**, not the synthetic data itself — that is stated here and in the
README rather than left implicit.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import sensors

RPM_RATED: float = 45_000.0  # 100% corrected speed for this notional test article
T_AMBIENT_K: float = 298.15  # ~25 degC test-cell ambient
P_AMBIENT_PA: float = 101_325.0


@dataclass(frozen=True)
class TestRunProfile:
    """Time-domain shape of one synthetic test run."""

    duration_s: float = 120.0
    sample_rate_hz: float = 10.0
    idle_end_s: float = 20.0
    spool_end_s: float = 50.0
    steady_end_s: float = 90.0
    # spool-down runs from steady_end_s to duration_s


def _throttle_profile(t: np.ndarray, profile: TestRunProfile) -> np.ndarray:
    """Commanded throttle fraction (0-1) vs. time: idle -> ramp -> steady -> ramp down."""
    throttle = np.zeros_like(t)
    idle_frac = 0.15

    idle_mask = t <= profile.idle_end_s
    throttle[idle_mask] = idle_frac

    spool_mask = (t > profile.idle_end_s) & (t <= profile.spool_end_s)
    ramp = (t[spool_mask] - profile.idle_end_s) / (profile.spool_end_s - profile.idle_end_s)
    throttle[spool_mask] = idle_frac + (1.0 - idle_frac) * ramp

    steady_mask = (t > profile.spool_end_s) & (t <= profile.steady_end_s)
    throttle[steady_mask] = 1.0

    down_mask = t > profile.steady_end_s
    ramp_down = 1.0 - (t[down_mask] - profile.steady_end_s) / (profile.duration_s - profile.steady_end_s)
    throttle[down_mask] = idle_frac + (1.0 - idle_frac) * np.clip(ramp_down, 0.0, 1.0)

    return throttle


def generate_raw_test_log(
    profile: TestRunProfile | None = None,
    random_seed: int = 42,
    inject_faults: bool = True,
) -> pd.DataFrame:
    """Generate a synthetic raw (uncalibrated) DAQ log for one test run.

    Physical model (all approximate, for realistic *shape* only):
        RPM   = throttle * RPM_RATED                     (first-order lag, tau=2s)
        thrust = k_f * (RPM/RPM_RATED)^2                  (thrust ~ speed^2, typical
                                                             centrifugal-compressor-driven trend)
        EGT   = T_ambient + k_t * (RPM/RPM_RATED)^1.5
        P_inlet = P_ambient * (1 + k_p * (RPM/RPM_RATED)^1.8)

    Each channel is then converted to *raw sensor units* (ADC counts, mV,
    mA, pulses) via the inverse of the calibration in :mod:`sensors`, and
    zero-mean Gaussian noise plus (optionally) a few injected defects are
    added, so the returned DataFrame looks like what actually comes off a
    DAQ card before any reduction is applied.
    """
    profile = profile or TestRunProfile()
    rng = np.random.default_rng(random_seed)

    n_samples = int(profile.duration_s * profile.sample_rate_hz) + 1
    t = np.linspace(0.0, profile.duration_s, n_samples)
    dt = 1.0 / profile.sample_rate_hz

    throttle = _throttle_profile(t, profile)

    # First-order lag on RPM response to throttle (spool inertia), tau = 2 s.
    tau_s = 2.0
    rpm_true = np.zeros_like(t)
    for i in range(1, len(t)):
        rpm_true[i] = rpm_true[i - 1] + dt / tau_s * (throttle[i] * RPM_RATED - rpm_true[i - 1])

    speed_frac = rpm_true / RPM_RATED
    thrust_true_n = 4500.0 * speed_frac**2
    egt_true_k = T_AMBIENT_K + 650.0 * speed_frac**1.5
    p_inlet_true_pa = P_AMBIENT_PA * (1.0 + 0.9 * speed_frac**1.8)
    fuel_flow_true_kg_s = 0.02 + 0.18 * speed_frac**1.7

    # --- Convert true engineering values to raw sensor units (inverse calibration) ---
    load_cell_counts = (
        thrust_true_n / sensors.DEFAULT_LOAD_CELL.slope_n_per_count + sensors.DEFAULT_LOAD_CELL.zero_offset_counts
    )
    tc_millivolts = (egt_true_k - 273.15 - sensors.DEFAULT_THERMOCOUPLE.cold_junction_temp_c) * (
        sensors.DEFAULT_THERMOCOUPLE.seebeck_coefficient_mv_per_c
    )
    pt = sensors.DEFAULT_PRESSURE_TRANSDUCER
    pressure_span_fraction = (p_inlet_true_pa - pt.range_min_pa) / (pt.range_max_pa - pt.range_min_pa)
    pressure_ma = pt.loop_min_ma + pressure_span_fraction * (pt.loop_max_ma - pt.loop_min_ma)
    rpm_pulse_count = rpm_true / 60.0 * sensors.DEFAULT_RPM_SENSOR.pulses_per_revolution * dt

    # --- Add representative per-channel measurement noise ------------------
    load_cell_counts += rng.normal(0.0, 15.0, n_samples)  # ~ +/-0.03% FS
    tc_millivolts += rng.normal(0.0, 0.02, n_samples)  # ~ +/-0.5 K equivalent
    pressure_ma += rng.normal(0.0, 0.01, n_samples)
    rpm_pulse_count += rng.normal(0.0, 0.05, n_samples)
    fuel_flow_kg_s = fuel_flow_true_kg_s + rng.normal(0.0, 0.0008, n_samples)

    df = pd.DataFrame(
        {
            "time_s": t,
            "load_cell_raw_counts": load_cell_counts,
            "thermocouple_raw_mv": tc_millivolts,
            "pressure_transducer_raw_ma": pressure_ma,
            "rpm_sensor_pulse_count": np.clip(rpm_pulse_count, 0.0, None),
            "fuel_flow_kg_s": np.clip(fuel_flow_kg_s, 0.0, None),
            "ambient_temp_k": T_AMBIENT_K + rng.normal(0.0, 0.1, n_samples),
            "ambient_pressure_pa": P_AMBIENT_PA + rng.normal(0.0, 20.0, n_samples),
        }
    )

    if inject_faults:
        df = _inject_faults(df, rng)

    return df


def _inject_faults(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Inject a dropout, a stuck-value run and a single spike, for QA to catch.

    These indices are chosen (not fully random) to land inside the steady
    -state window, so they represent believable in-run instrumentation
    faults rather than start/stop transients.
    """
    df = df.copy()
    n = len(df)

    # 1. Sensor dropout: thermocouple reads NaN for ~1 second.
    dropout_start = int(n * 0.55)
    df.loc[dropout_start : dropout_start + 9, "thermocouple_raw_mv"] = np.nan

    # 2. Stuck value: pressure transducer freezes at its last good reading for ~2 s.
    stuck_start = int(n * 0.65)
    stuck_value = df.loc[stuck_start, "pressure_transducer_raw_ma"]
    df.loc[stuck_start : stuck_start + 19, "pressure_transducer_raw_ma"] = stuck_value

    # 3. Single-sample spike: load cell glitches high for one scan (cable EMI).
    spike_index = int(n * 0.75)
    df.loc[spike_index, "load_cell_raw_counts"] *= 1.35

    return df
