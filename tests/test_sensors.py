"""Unit tests for the sensor calibration models."""

import pytest

from jetx.daq import sensors


def test_load_cell_two_point_calibration_recovers_zero_and_cal_point():
    cal = sensors.LoadCellCalibration.from_two_point(
        zero_counts=1000.0, cal_counts=48000.0, cal_force_n=5000.0, rated_capacity_n=10_000.0
    )
    assert cal.raw_to_engineering_units(1000.0) == pytest.approx(0.0)
    assert cal.raw_to_engineering_units(48000.0) == pytest.approx(5000.0)


def test_load_cell_is_linear():
    cal = sensors.DEFAULT_LOAD_CELL
    f1 = cal.raw_to_engineering_units(10_000.0)
    f2 = cal.raw_to_engineering_units(20_000.0)
    f3 = cal.raw_to_engineering_units(30_000.0)
    assert (f2 - f1) == pytest.approx(f3 - f2)


def test_thermocouple_round_trip():
    cal = sensors.ThermocoupleCalibration(seebeck_coefficient_mv_per_c=0.041, cold_junction_temp_c=25.0)
    # At 0 mV (isothermal, no EMF), reported temp should equal the cold-junction reference.
    assert cal.raw_to_engineering_units(0.0) == pytest.approx(25.0 + 273.15)
    # Known EMF corresponds to a known temperature rise above the reference.
    temp_k = cal.raw_to_engineering_units(20.5)  # 20.5 mV / 0.041 mV/degC = 500 degC rise
    assert temp_k == pytest.approx(25.0 + 500.0 + 273.15, rel=1e-6)


def test_pressure_transducer_endpoints():
    cal = sensors.PressureTransducerCalibration(range_min_pa=0.0, range_max_pa=1_000_000.0)
    assert cal.raw_to_engineering_units(4.0) == pytest.approx(0.0)
    assert cal.raw_to_engineering_units(20.0) == pytest.approx(1_000_000.0)
    assert cal.raw_to_engineering_units(12.0) == pytest.approx(500_000.0)


def test_rpm_sensor_conversion():
    cal = sensors.RpmSensorCalibration(pulses_per_revolution=60)
    # 60 pulses/rev, 60 pulses counted in 1 second == 1 rev/s == 60 RPM.
    assert cal.raw_to_engineering_units(pulse_count=60.0, sample_window_s=1.0) == pytest.approx(60.0)
    # Same pulse count over a shorter window means a higher speed.
    assert cal.raw_to_engineering_units(pulse_count=60.0, sample_window_s=0.5) == pytest.approx(120.0)
