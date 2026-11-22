import math
import unittest

from meteo_audit.epoch_units import (
    UnitEpoch, UnresolvedUnitEpoch, rain_interval_cm, resolve_epoch, wind_speed_kmh,
)


class EpochUnitTests(unittest.TestCase):
    def setUp(self):
        self.early = UnitEpoch(
            "weewx_WH1080", 1293840000, 1357000000, 17, "km/h", "counter_mm",
            "synthetic:2011", True)
        self.late = UnitEpoch(
            "weewx_WH1080", 1514764800, 1577836800, 17, "m/s", "interval_mm",
            "synthetic:2019", True)

    def convert_wind(self, raw, ts=1540000000, epochs=None, units=17):
        return wind_speed_kmh(raw, source="weewx_WH1080",
                              end_time_utc=ts, us_units=units,
                              epochs=[self.early, self.late] if epochs is None else epochs)

    def test_2011_kmh_not_doubled(self):
        self.assertEqual(self.convert_wind(12, ts=1300000000), 12.0)

    def test_2019_ms_times_3_6(self):
        self.assertAlmostEqual(self.convert_wind(12), 43.2)

    def test_2013_boundary_without_evidence_fails(self):
        with self.assertRaisesRegex(UnresolvedUnitEpoch, "missing"):
            self.convert_wind(12, ts=1370000000)

    def test_counter_not_interval(self):
        with self.assertRaisesRegex(UnresolvedUnitEpoch, "counter"):
            rain_interval_cm(12, source="weewx_WH1080", end_time_utc=1300000000,
                             us_units=17, epochs=[self.early])

    def test_verified_mm_interval_to_cm(self):
        self.assertAlmostEqual(rain_interval_cm(
            1.5, source="weewx_WH1080", end_time_utc=1540000000,
            us_units=17, epochs=[self.late]), 0.15)

    def test_zero_and_null_remain_distinct(self):
        self.assertEqual(self.convert_wind(0), 0)
        self.assertIsNone(self.convert_wind(None))
        self.assertEqual(rain_interval_cm(
            0, source="weewx_WH1080", end_time_utc=1540000000,
            us_units=17, epochs=[self.late]), 0)
        self.assertIsNone(rain_interval_cm(
            None, source="weewx_WH1080", end_time_utc=1540000000,
            us_units=17, epochs=[self.late]))

    def test_unverified_epoch_fails(self):
        unknown = UnitEpoch("weewx_WH1080", 1360000000, 1400000000, 17,
                            "m/s", "UNRESOLVED")
        with self.assertRaisesRegex(UnresolvedUnitEpoch, "not verified"):
            self.convert_wind(12, ts=1370000000, epochs=[unknown])

    def test_overlapping_epoch_fails(self):
        overlap = UnitEpoch("weewx_WH1080", 1300000000, 1310000000, 17,
                            "m/s", "counter_mm", "synthetic:overlap", True)
        with self.assertRaisesRegex(UnresolvedUnitEpoch, "ambiguous"):
            self.convert_wind(10, ts=1305000000, epochs=[self.early, overlap])

    def test_mismatched_unit_system_fails(self):
        with self.assertRaisesRegex(UnresolvedUnitEpoch, "differs"):
            self.convert_wind(10, units=16)

    def test_invalid_placeholders_fail(self):
        for value in (True, -1, math.nan, math.inf, "0"):
            with self.subTest(value=value), self.assertRaises(UnresolvedUnitEpoch):
                self.convert_wind(value)

    def test_verified_needs_reference(self):
        with self.assertRaisesRegex(UnresolvedUnitEpoch, "evidence"):
            UnitEpoch("wh", 0, 10, 17, "m/s", "interval_mm", verified=True)

    def test_end_exclusive_and_bool_timestamp_fail(self):
        with self.assertRaises(UnresolvedUnitEpoch):
            resolve_epoch([self.early], source="weewx_WH1080",
                          end_time_utc=self.early.end_utc, us_units=17)
        with self.assertRaises(UnresolvedUnitEpoch):
            resolve_epoch([self.early], source="weewx_WH1080",
                          end_time_utc=True, us_units=17)


if __name__ == "__main__":
    unittest.main()
