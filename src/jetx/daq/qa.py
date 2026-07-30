"""Automated QA flagging for reduced test-bed data.

Four independent, per-sample flags are computed for each monitored
channel, mirroring the checks a test engineer would apply by eye when
scanning a strip-chart:

* ``dropout``  — the raw sample is missing (NaN).
* ``stuck``    — the signal has not changed for an implausibly long run of
  consecutive samples (transducer or cabling fault), detected as N
  consecutive zero first-differences.
* ``spike``    — the sample deviates from a local rolling median by more
  than ``n_sigma`` rolling standard deviations (single-scan EMI glitch).
* ``out_of_range`` — the calibrated value falls outside a physically
  plausible engineering range for that channel (sensor rated capacity,
  material temperature limit, or overspeed limit).

A row's overall QA status is "pass" only if none of its flags (across all
monitored channels) are set.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..common.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ChannelQaLimits:
    """Physical validity range and fault-detection thresholds for one channel."""

    valid_min: float
    valid_max: float
    stuck_window_samples: int = 8
    spike_rolling_window: int = 11
    spike_n_sigma: float = 6.0


DEFAULT_LIMITS: dict[str, ChannelQaLimits] = {
    "thrust_n": ChannelQaLimits(valid_min=-50.0, valid_max=10_000.0),
    "egt_k": ChannelQaLimits(valid_min=250.0, valid_max=1400.0),
    "inlet_pressure_pa": ChannelQaLimits(valid_min=50_000.0, valid_max=250_000.0),
    "rpm": ChannelQaLimits(valid_min=-50.0, valid_max=47_250.0),  # 105% of RPM_RATED
}


def _flag_dropout(raw_series: pd.Series) -> pd.Series:
    return raw_series.isna()


def _flag_stuck(series: pd.Series, window: int) -> pd.Series:
    unchanged = series.diff().fillna(1.0) == 0.0
    # A run counts as "stuck" once it has held for `window` consecutive samples.
    run_length = unchanged.groupby((~unchanged).cumsum()).cumsum()
    return run_length >= window


def _flag_spike(series: pd.Series, window: int, n_sigma: float) -> pd.Series:
    """Flag samples far from a local, outlier-robust centre and spread.

    Uses the rolling median and rolling median-absolute-deviation (MAD)
    rather than the rolling mean/std: a single-scan spike inside a small
    window inflates the *mean* and *std* enough to mask itself (the
    classic failure mode of a naive rolling z-score), whereas the median
    and MAD are, by construction, robust to exactly one outlier in the
    window. ``1.4826 * MAD`` is the standard consistency-corrected
    estimator of the standard deviation for normally-distributed data.
    """
    rolling_median = series.rolling(window, center=True, min_periods=3).median()
    abs_deviation = (series - rolling_median).abs()
    rolling_mad = abs_deviation.rolling(window, center=True, min_periods=3).median()
    robust_std = 1.4826 * rolling_mad
    threshold = n_sigma * robust_std.replace(0.0, np.nan)
    return (abs_deviation > threshold).fillna(False)


def _flag_out_of_range(series: pd.Series, valid_min: float, valid_max: float) -> pd.Series:
    return (series < valid_min) | (series > valid_max)


def evaluate_channel_qa(
    calibrated_series: pd.Series,
    raw_series: pd.Series,
    limits: ChannelQaLimits,
) -> pd.DataFrame:
    """Compute the four QA flags for one channel; returns a 4-column DataFrame."""
    return pd.DataFrame(
        {
            "dropout": _flag_dropout(raw_series),
            "stuck": _flag_stuck(calibrated_series, limits.stuck_window_samples),
            "spike": _flag_spike(calibrated_series, limits.spike_rolling_window, limits.spike_n_sigma),
            "out_of_range": _flag_out_of_range(calibrated_series, limits.valid_min, limits.valid_max),
        }
    )


_CHANNEL_TO_RAW_COLUMN: dict[str, str] = {
    "thrust_n": "load_cell_raw_counts",
    "egt_k": "thermocouple_raw_mv",
    "inlet_pressure_pa": "pressure_transducer_raw_ma",
    "rpm": "rpm_sensor_pulse_count",
}


def evaluate_log_qa(df: pd.DataFrame, limits: dict[str, ChannelQaLimits] | None = None) -> pd.DataFrame:
    """Add per-channel QA flag columns and an overall ``qa_pass`` column.

    Expects ``df`` to already carry both the raw columns (from
    :mod:`jetx.daq.synthetic`) and the calibrated columns (from
    :mod:`jetx.daq.calibration`).
    """
    limits = limits or DEFAULT_LIMITS
    df = df.copy()
    any_flag = pd.Series(False, index=df.index)

    for channel, channel_limits in limits.items():
        raw_column = _CHANNEL_TO_RAW_COLUMN[channel]
        flags = evaluate_channel_qa(df[channel], df[raw_column], channel_limits)
        for flag_name, flag_series in flags.items():
            column_name = f"qa_{channel}_{flag_name}"
            df[column_name] = flag_series
            any_flag = any_flag | flag_series.fillna(False)

    df["qa_pass"] = ~any_flag
    n_failed = int((~df["qa_pass"]).sum())
    logger.info("QA evaluation: %d/%d samples flagged (%.1f%%)", n_failed, len(df), 100.0 * n_failed / len(df))
    return df
