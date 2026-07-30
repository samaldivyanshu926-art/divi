"""Sensor calibration models for the four test-cell instrumentation channels.

Each sensor class holds its calibration coefficients as dataclass fields
and exposes a single ``raw_to_engineering_units`` method — the same shape
a real DAQ configuration file would have (slope/offset/range per channel),
so this module doubles as a template for a real calibration-sheet importer.

All four are **linear or near-linear, two-point calibration models**. Real
instrumentation (especially thermocouples) is not perfectly linear; the
simplification and its consequences are documented in
``docs/assumptions_and_limitations.md`` rather than silently assumed.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoadCellCalibration:
    """Strain-gauge load cell: 16-bit ADC counts -> force in newtons.

    Modelled as a two-point linear calibration,

        F = slope_n_per_count * (raw_counts - zero_offset_counts)

    ``zero_offset_counts`` is the ADC reading with no load applied (the
    "tare"), and ``slope_n_per_count`` is derived from a known calibration
    weight: ``slope = F_cal / (raw_at_F_cal - zero_offset_counts)``.
    """

    slope_n_per_count: float
    zero_offset_counts: float
    rated_capacity_n: float

    @classmethod
    def from_two_point(
        cls,
        zero_counts: float,
        cal_counts: float,
        cal_force_n: float,
        rated_capacity_n: float,
    ) -> "LoadCellCalibration":
        """Build a calibration from a tare reading and one known calibration load."""
        slope = cal_force_n / (cal_counts - zero_counts)
        return cls(slope_n_per_count=slope, zero_offset_counts=zero_counts, rated_capacity_n=rated_capacity_n)

    def raw_to_engineering_units(self, raw_counts: float) -> float:
        """Convert raw ADC counts to force in newtons."""
        return self.slope_n_per_count * (raw_counts - self.zero_offset_counts)


@dataclass(frozen=True)
class ThermocoupleCalibration:
    """Type-K thermocouple: millivolt EMF -> temperature in kelvin.

    Uses a **simplified linear** EMF-temperature relation,

        T [degC] = mv_reading / seebeck_coefficient_mv_per_c + cold_junction_temp_c

    A real Type-K thermocouple's EMF-temperature curve is described by an
    8th/9th-order polynomial per the NIST ITS-90 reference tables; the
    linear approximation here (using the nominal Type-K Seebeck
    coefficient of ~0.041 mV/degC around typical exhaust-gas
    temperatures) is accurate to within a few degrees over a few hundred
    degC span around the reference point, which is adequate for a
    portfolio-level demonstration but would need the full polynomial (or
    a lookup table) for certified test data.
    """

    seebeck_coefficient_mv_per_c: float = 0.041
    cold_junction_temp_c: float = 25.0

    def raw_to_engineering_units(self, raw_millivolts: float) -> float:
        """Convert thermocouple EMF in millivolts to temperature in kelvin."""
        temp_c = raw_millivolts / self.seebeck_coefficient_mv_per_c + self.cold_junction_temp_c
        return temp_c + 273.15


@dataclass(frozen=True)
class PressureTransducerCalibration:
    """4-20 mA current-loop pressure transducer -> pressure in pascal.

    Standard industrial current-loop scaling: 4 mA maps to
    ``range_min_pa``, 20 mA maps to ``range_max_pa``, linear in between.
    """

    range_min_pa: float
    range_max_pa: float
    loop_min_ma: float = 4.0
    loop_max_ma: float = 20.0

    def raw_to_engineering_units(self, raw_milliamps: float) -> float:
        """Convert a 4-20 mA loop current to pressure in pascal."""
        span_fraction = (raw_milliamps - self.loop_min_ma) / (self.loop_max_ma - self.loop_min_ma)
        return self.range_min_pa + span_fraction * (self.range_max_pa - self.range_min_pa)


@dataclass(frozen=True)
class RpmSensorCalibration:
    """Magnetic pickup / pulse counter -> shaft speed in RPM.

    Counts gear teeth (or a toothed phonic wheel) passing a fixed pickup
    over a sample window:

        RPM = (pulse_count / pulses_per_revolution) / sample_window_s * 60
    """

    pulses_per_revolution: int

    def raw_to_engineering_units(self, pulse_count: float, sample_window_s: float) -> float:
        """Convert a pulse count over a known sample window to RPM."""
        revolutions = pulse_count / self.pulses_per_revolution
        return revolutions / sample_window_s * 60.0


# --- Representative "as-fitted" calibrations used by the synthetic rig -----
# These are the calibration constants the synthetic DAQ generator (synthetic.py)
# uses to go from engineering units *back* to raw counts, and that the
# reduction pipeline (calibration.py) uses to reverse the process — exactly
# as a real calibration sheet would be used in both directions.

DEFAULT_LOAD_CELL = LoadCellCalibration.from_two_point(
    zero_counts=1000.0, cal_counts=48000.0, cal_force_n=5000.0, rated_capacity_n=10_000.0
)
DEFAULT_THERMOCOUPLE = ThermocoupleCalibration(seebeck_coefficient_mv_per_c=0.041, cold_junction_temp_c=25.0)
DEFAULT_PRESSURE_TRANSDUCER = PressureTransducerCalibration(range_min_pa=0.0, range_max_pa=1_000_000.0)
DEFAULT_RPM_SENSOR = RpmSensorCalibration(pulses_per_revolution=60)
