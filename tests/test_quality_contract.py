import unittest
from datetime import date, datetime, timezone

from meteo_audit.quality_contract import (
    FieldObservation, QualityContractError, belongs_to_civil_day,
    civil_day_bounds, serialize_field,
)


def field(state="MEASURED", **kw):
    args = dict(timestamp_utc=1790000000, variable="outTemp", state=state,
                measurement_value=0, display_value=0, unit="°C",
                source_ref="raw:sample", epoch_ref="sensor:era",
                independent_validation=True)
    args.update(kw)
    return FieldObservation(**args)


class FieldQualityTests(unittest.TestCase):
    def test_same_timestamp_can_have_distinct_qc_states_per_variable(self):
        measured = serialize_field(field(variable="outTemp"))
        missing = serialize_field(field(
            "MISSING", variable="outHumidity", measurement_value=None,
            display_value=None, qc_flags=("NO_SIGNAL",)))
        self.assertEqual(measured["timestamp_utc"], missing["timestamp_utc"])
        self.assertEqual(measured["state"], "MEASURED")
        self.assertEqual(missing["state"], "MISSING")
        self.assertTrue(measured["extrema_eligible"])
        self.assertFalse(missing["extrema_eligible"])

    def test_measured_zero_is_not_null(self):
        record = serialize_field(field(measurement_value=0, display_value=0))
        self.assertEqual(record["display_value"], 0)
        self.assertTrue(record["join_chart_line"])

    def test_missing_and_sensor_error_are_not_displayed_or_connected(self):
        for state in ("MISSING", "SENSOR_ERROR"):
            with self.subTest(state=state):
                obs = field(state, display_value=None,
                            qc_flags=("NO_SIGNAL",))
                self.assertFalse(obs.join_chart_line)
                self.assertFalse(obs.extrema_eligible)

    def test_never_assume_not_installed_without_epoch_evidence(self):
        with self.assertRaisesRegex(QualityContractError, "installation"):
            field("NOT_INSTALLED", measurement_value=None, display_value=None,
                  epoch_ref=None)
        present = field("NOT_INSTALLED", measurement_value=None,
                        display_value=None, epoch_ref="install:verified")
        self.assertFalse(present.extrema_eligible)

    def test_correction_requires_explicit_approval(self):
        with self.assertRaisesRegex(QualityContractError, "approved"):
            field("CORRECTED", change_ref="batch:1")
        corrected = field("CORRECTED", change_ref="batch:1", approved=True)
        self.assertFalse(corrected.extrema_eligible)

    def test_estimates_never_connect_chart_lines_or_define_extrema(self):
        estimate = field("ESTIMATED", change_ref="batch:2",
                         approved=True, replacement_confidence="LOW")
        self.assertFalse(estimate.join_chart_line)
        self.assertFalse(estimate.extrema_eligible)

    def test_sensor_flag_rejects_statistical_extrema(self):
        suspicious = field(qc_flags=("SATURATED",))
        self.assertFalse(suspicious.extrema_eligible)

    def test_unverified_measurement_rejects_extrema(self):
        self.assertFalse(field(independent_validation=False).extrema_eligible)

    def test_numeric_without_source_provenance_rejected(self):
        with self.assertRaisesRegex(QualityContractError, "provenance"):
            field(source_ref=None)

    def test_reject_placeholder_nan_infinity_bool(self):
        for bad in ("0", float("nan"), float("inf"), True):
            with self.subTest(bad=bad), self.assertRaises(QualityContractError):
                field(display_value=bad)

    def test_reject_duplicate_qc_flags(self):
        with self.assertRaisesRegex(QualityContractError, "duplicate"):
            field(qc_flags=("NO_SIGNAL", "NO_SIGNAL"))

    def test_spring_dst_day_has_23_hours(self):
        lower, upper = civil_day_bounds(date(2026, 3, 29))
        self.assertEqual(upper - lower, 23 * 3600)

    def test_autumn_dst_day_has_25_hours(self):
        lower, upper = civil_day_bounds(date(2026, 10, 25))
        self.assertEqual(upper - lower, 25 * 3600)

    def test_midnight_exclusive_start_inclusive_end(self):
        day = date(2026, 10, 25)
        lower, upper = civil_day_bounds(day)
        self.assertFalse(belongs_to_civil_day(lower, day))
        self.assertTrue(belongs_to_civil_day(upper, day))
        self.assertTrue(belongs_to_civil_day(lower + 300, day))
        self.assertFalse(belongs_to_civil_day(upper + 1, day))

    def test_fall_repeated_hour_has_offset_and_fold(self):
        # 2026-10-25 00:30Z = 02:30 CEST, 01:30Z = 02:30 CET.
        early = serialize_field(field(timestamp_utc=1792888200))
        late = serialize_field(field(timestamp_utc=1792891800))
        self.assertNotEqual(early["local_end_iso"], late["local_end_iso"])
        self.assertEqual({early["local_fold"], late["local_fold"]}, {0, 1})

    def test_no_automatic_approval_of_sensor_error(self):
        with self.assertRaises(QualityContractError):
            field("SENSOR_ERROR", display_value=None,
                  qc_flags=("FROZEN",), approved=True)


if __name__ == "__main__":
    unittest.main()
