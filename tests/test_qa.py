"""Tests for the automated QA flagging rules."""

from jetx.daq import calibration, qa, synthetic


def test_qa_catches_injected_dropout_stuck_and_spike_faults():
    raw_df = synthetic.generate_raw_test_log(inject_faults=True)
    calibrated = calibration.apply_calibration(raw_df)
    result = qa.evaluate_log_qa(calibrated)

    assert result["qa_egt_k_dropout"].sum() > 0
    assert result["qa_inlet_pressure_pa_stuck"].sum() > 0
    assert result["qa_thrust_n_spike"].sum() > 0
    assert (~result["qa_pass"]).sum() > 0


def test_qa_pass_rate_is_high_without_injected_faults():
    raw_df = synthetic.generate_raw_test_log(inject_faults=False)
    calibrated = calibration.apply_calibration(raw_df)
    result = qa.evaluate_log_qa(calibrated)

    pass_rate = result["qa_pass"].mean()
    assert pass_rate > 0.95


def test_out_of_range_flag_triggers_beyond_configured_limits():
    raw_df = synthetic.generate_raw_test_log(inject_faults=False)
    calibrated = calibration.apply_calibration(raw_df)
    calibrated.loc[0, "rpm"] = 90_000.0  # far beyond the overspeed limit
    result = qa.evaluate_log_qa(calibrated)
    assert bool(result.loc[0, "qa_rpm_out_of_range"]) is True
    assert bool(result.loc[0, "qa_pass"]) is False
