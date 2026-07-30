"""Tests for the calibration pipeline (raw log -> engineering units)."""

from jetx.daq import calibration, synthetic


def test_apply_calibration_adds_expected_columns_and_preserves_length():
    raw_df = synthetic.generate_raw_test_log(inject_faults=False)
    calibrated = calibration.apply_calibration(raw_df)

    assert len(calibrated) == len(raw_df)
    for column in ("thrust_n", "egt_k", "inlet_pressure_pa", "rpm"):
        assert column in calibrated.columns

    # Raw columns must be preserved for traceability back to the DAQ card.
    assert "load_cell_raw_counts" in calibrated.columns


def test_calibrated_values_are_physically_reasonable():
    raw_df = synthetic.generate_raw_test_log(inject_faults=False)
    calibrated = calibration.apply_calibration(raw_df)

    assert calibrated["thrust_n"].min() > -100.0  # noise around zero at idle, but not wildly negative
    assert calibrated["thrust_n"].max() < 10_000.0
    assert calibrated["egt_k"].min() > 200.0
    assert calibrated["egt_k"].max() < 1500.0
    assert calibrated["rpm"].max() < 50_000.0
