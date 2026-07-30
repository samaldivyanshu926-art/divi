"""Tests for the noise-filtering module."""

import numpy as np
import pandas as pd

from jetx.daq.filtering import butterworth_lowpass_filter, moving_average_filter


def _noisy_step_signal(n: int = 400, sample_rate_hz: float = 10.0, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    signal = np.concatenate([np.zeros(n // 2), np.ones(n - n // 2) * 10.0])
    noise = rng.normal(0.0, 0.5, n)
    return pd.Series(signal + noise)


def test_moving_average_reduces_variance_relative_to_raw_noise():
    series = _noisy_step_signal()
    filtered = moving_average_filter(series, window_samples=7)
    raw_high_freq_energy = series.diff().dropna().var()
    filtered_high_freq_energy = filtered.diff().dropna().var()
    assert filtered_high_freq_energy < raw_high_freq_energy


def test_butterworth_filter_reduces_noise_and_preserves_length():
    series = _noisy_step_signal()
    filtered = butterworth_lowpass_filter(series, sample_rate_hz=10.0, cutoff_hz=1.0)
    assert len(filtered) == len(series)
    raw_high_freq_energy = series.diff().dropna().var()
    filtered_high_freq_energy = filtered.diff().dropna().var()
    assert filtered_high_freq_energy < raw_high_freq_energy


def test_butterworth_filter_interpolates_short_gaps():
    series = _noisy_step_signal()
    series.iloc[100:103] = np.nan  # short 3-sample gap
    filtered = butterworth_lowpass_filter(series, sample_rate_hz=10.0, cutoff_hz=1.0)
    assert not filtered.iloc[95:110].isna().any()
