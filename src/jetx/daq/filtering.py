"""Noise filtering for calibrated DAQ channels.

Two filters are provided, matching the two most common approaches in a
test-cell data system:

* a simple moving-average (boxcar) filter — cheap, causal-enough for
  quick-look plots, but with well-known drawbacks (lag, no frequency-domain
  control);
* a zero-phase Butterworth low-pass filter (``scipy.signal.butter`` +
  ``filtfilt``) — the standard choice for post-test data reduction, since
  ``filtfilt`` applies the filter forward and backward to cancel phase lag,
  which a moving average cannot do.

NaN handling: both filters interpolate short NaN gaps (sensor dropouts)
linearly before filtering, since neither a boxcar nor a Butterworth filter
is defined across missing samples. The interpolation is intentionally
*not* extrapolated across long gaps (see ``max_gap_samples``), so a real
sensor dropout still shows up as missing/QA-flagged data rather than being
silently invented.
"""

from __future__ import annotations

import pandas as pd
from scipy.signal import butter, filtfilt

from ..common.logging_config import get_logger

logger = get_logger(__name__)


def _interpolate_short_gaps(series: pd.Series, max_gap_samples: int) -> pd.Series:
    """Linearly interpolate NaN runs no longer than ``max_gap_samples``."""
    return series.interpolate(method="linear", limit=max_gap_samples, limit_area="inside")


def moving_average_filter(series: pd.Series, window_samples: int = 5, max_gap_samples: int = 20) -> pd.Series:
    """Centered moving-average (boxcar) filter.

    ``window_samples`` should be odd so the filter is exactly centered
    (symmetric) around each sample.
    """
    filled = _interpolate_short_gaps(series, max_gap_samples)
    return filled.rolling(window=window_samples, center=True, min_periods=1).mean()


def butterworth_lowpass_filter(
    series: pd.Series,
    sample_rate_hz: float,
    cutoff_hz: float = 1.0,
    order: int = 4,
    max_gap_samples: int = 20,
) -> pd.Series:
    """Zero-phase digital Butterworth low-pass filter.

    Design equation (normalised cutoff, since ``scipy.signal.butter``
    expects frequencies as a fraction of the Nyquist frequency):

        Wn = cutoff_hz / (sample_rate_hz / 2)

    ``filtfilt`` runs the filter twice (once forward, once time-reversed)
    so the combined phase response is zero — critical for test data, where
    a phase-shifted filter would misalign a filtered channel against
    unfiltered event markers (e.g. throttle command timestamps).
    """
    filled = _interpolate_short_gaps(series, max_gap_samples)
    valid = filled.dropna()
    if len(valid) < 3 * order:
        logger.warning(
            "Not enough valid samples (%d) to apply order-%d Butterworth filter; returning unfiltered series.",
            len(valid),
            order,
        )
        return filled

    nyquist_hz = sample_rate_hz / 2.0
    normalized_cutoff = cutoff_hz / nyquist_hz
    b, a = butter(N=order, Wn=normalized_cutoff, btype="low")

    result = filled.copy()
    valid_mask = filled.notna()
    result.loc[valid_mask] = filtfilt(b, a, filled.loc[valid_mask].to_numpy())
    return result


def filter_channel(
    df: pd.DataFrame,
    column: str,
    sample_rate_hz: float,
    cutoff_hz: float = 1.0,
) -> pd.Series:
    """Convenience wrapper: Butterworth-filter one named column of ``df``."""
    return butterworth_lowpass_filter(df[column], sample_rate_hz=sample_rate_hz, cutoff_hz=cutoff_hz)
