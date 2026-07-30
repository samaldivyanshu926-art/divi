"""Project 2 — Test-Bed Data Acquisition & Reduction.

Simulates a realistic engine test-cell DAQ chain end to end: synthetic raw
sensor signals -> calibration into engineering units -> noise filtering ->
corrected-speed normalisation -> automated QA flagging -> dashboard.

Modules
-------
sensors         : Sensor calibration models (load cell, thermocouple,
                  pressure transducer, RPM/speed pickup).
synthetic       : Synthetic raw-DAQ test-run generator.
calibration     : Raw-signal -> engineering-unit reduction pipeline.
filtering       : Noise filters (moving average, Butterworth low-pass).
corrected_speed : ISA-referenced corrected speed / corrected mass flow.
qa              : Automated QA flagging rules.
dashboard       : Interactive Plotly test-run dashboard.
plotting        : Static matplotlib summary plots.
"""
