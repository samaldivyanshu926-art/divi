"""Calibration pipeline: raw DAQ signals -> engineering units.

This is the direct, per-scan application of the calibration models in
:mod:`sensors` to a whole log DataFrame at once (vectorised via pandas
``.apply``/direct arithmetic — the sensor classes themselves work on
scalars, matching how a calibration is usually specified on a data sheet).
"""

from __future__ import annotations

import pandas as pd

from ..common.logging_config import get_logger
from . import sensors

logger = get_logger(__name__)


def apply_calibration(
    raw_df: pd.DataFrame,
    load_cell_cal: sensors.LoadCellCalibration = sensors.DEFAULT_LOAD_CELL,
    thermocouple_cal: sensors.ThermocoupleCalibration = sensors.DEFAULT_THERMOCOUPLE,
    pressure_cal: sensors.PressureTransducerCalibration = sensors.DEFAULT_PRESSURE_TRANSDUCER,
    rpm_cal: sensors.RpmSensorCalibration = sensors.DEFAULT_RPM_SENSOR,
) -> pd.DataFrame:
    """Convert a raw DAQ log to engineering units using explicit calibrations.

    Returns a *new* DataFrame; the raw columns are preserved alongside the
    new engineering-unit columns so the reduction can always be traced back
    to what the DAQ card actually recorded.
    """
    df = raw_df.copy()
    dt_s = float(df["time_s"].diff().median())

    df["thrust_n"] = load_cell_cal.raw_to_engineering_units(df["load_cell_raw_counts"])
    df["egt_k"] = thermocouple_cal.raw_to_engineering_units(df["thermocouple_raw_mv"])
    df["inlet_pressure_pa"] = pressure_cal.raw_to_engineering_units(df["pressure_transducer_raw_ma"])
    df["rpm"] = rpm_cal.raw_to_engineering_units(df["rpm_sensor_pulse_count"], sample_window_s=dt_s)

    logger.info(
        "Calibrated %d samples (thrust, EGT, inlet pressure, RPM); dt=%.4f s", len(df), dt_s
    )
    return df
