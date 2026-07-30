#!/usr/bin/env python3
"""Project 2 entry point: synthetic DAQ -> calibration -> filtering ->
corrected speed -> QA -> dashboard, end to end.

Generates:
    data/project2/raw_test_log.csv
    data/project2/reduced_test_log.csv
    figures/project2/test_run_summary.png
    figures/project2/dashboard.html

Usage:
    python scripts/run_project2_data_reduction.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from jetx.common.logging_config import get_logger  # noqa: E402
from jetx.daq import calibration, corrected_speed, dashboard, filtering, plotting, qa, synthetic  # noqa: E402

logger = get_logger(__name__)

DATA_DIR = REPO_ROOT / "data" / "project2"
FIGURES_DIR = REPO_ROOT / "figures" / "project2"
SAMPLE_RATE_HZ = 10.0


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Generating synthetic raw test log...")
    raw_df = synthetic.generate_raw_test_log()
    raw_df.to_csv(DATA_DIR / "raw_test_log.csv", index=False)
    logger.info("Wrote %d raw samples to %s", len(raw_df), DATA_DIR / "raw_test_log.csv")

    logger.info("Applying calibration...")
    calibrated_df = calibration.apply_calibration(raw_df)

    logger.info("Filtering channels (Butterworth low-pass, fc=1.0 Hz)...")
    for column in ("thrust_n", "egt_k", "inlet_pressure_pa"):
        calibrated_df[f"{column}_filtered"] = filtering.filter_channel(
            calibrated_df, column, sample_rate_hz=SAMPLE_RATE_HZ, cutoff_hz=1.0
        )

    logger.info("Computing corrected speed / corrected fuel flow...")
    reduced_df = corrected_speed.add_corrected_parameters(calibrated_df)

    logger.info("Running QA flagging...")
    reduced_df = qa.evaluate_log_qa(reduced_df)

    reduced_df.to_csv(DATA_DIR / "reduced_test_log.csv", index=False)
    logger.info("Wrote %d reduced samples to %s", len(reduced_df), DATA_DIR / "reduced_test_log.csv")

    plotting.plot_test_run_summary(reduced_df, FIGURES_DIR / "test_run_summary.png")
    dashboard.build_dashboard(reduced_df, FIGURES_DIR / "dashboard.html")

    n_failed = int((~reduced_df["qa_pass"]).sum())
    logger.info(
        "QA summary: %d/%d samples flagged (%.1f%%) — peak thrust %.1f N at %.1f%% corrected speed",
        n_failed,
        len(reduced_df),
        100.0 * n_failed / len(reduced_df),
        reduced_df["thrust_n"].max(),
        reduced_df["rpm_percent_corrected"].max(),
    )


if __name__ == "__main__":
    main()
