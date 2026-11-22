"""Tests for CHMI ten-minute rainfall quality and local-day boundaries."""

import unittest
from datetime import datetime
from decimal import Decimal

from meteo_audit.chmi_rainfall import summarize_chmi_10min
from meteo_audit.time_bounds import PRAGUE


class ChmiLocalDayTests(unittest.TestCase):
    def test_interval_ending_at_midnight_belongs_to_previous_day(self):
        start = int(datetime(2021, 7, 1, tzinfo=PRAGUE).timestamp())
        end = int(datetime(2021, 8, 1, tzinfo=PRAGUE).timestamp())
        rows = [
            {"STATION": "0-203-0-11777", "ELEMENT": "SRA10M", "DT": "2021-06-30T22:00Z", "VALUE": "9", "FLAG": "", "QUALITY": "0.0"},
            {"STATION": "0-203-0-11777", "ELEMENT": "SRA10M", "DT": "2021-06-30T22:10Z", "VALUE": "0.1", "FLAG": "", "QUALITY": "0.0"},
            {"STATION": "0-203-0-11777", "ELEMENT": "SRA10M", "DT": "2021-06-30T22:20Z", "VALUE": "5", "FLAG": "", "QUALITY": "3.0"},
            {"STATION": "0-203-0-11777", "ELEMENT": "SRA10M", "DT": "2021-07-01T22:00Z", "VALUE": "0.2", "FLAG": "", "QUALITY": "0.0"},
            {"STATION": "0-203-0-11777", "ELEMENT": "SRA10M", "DT": "2021-07-01T22:10Z", "VALUE": "0.4", "FLAG": "", "QUALITY": "0.0"},
            {"STATION": "0-203-0-11777", "ELEMENT": "SRA10M", "DT": "2021-07-31T22:00Z", "VALUE": "0.3", "FLAG": "", "QUALITY": "0.0"},
            {"STATION": "0-203-0-11777", "ELEMENT": "SRA10M", "DT": "2021-08-01T22:10Z", "VALUE": "9", "FLAG": "", "QUALITY": "0.0"},
        ]
        daily = summarize_chmi_10min(rows, start, end)
        first = daily[("0-203-0-11777", datetime(2021, 7, 1).date())]
        second = daily[("0-203-0-11777", datetime(2021, 7, 2).date())]
        last = daily[("0-203-0-11777", datetime(2021, 7, 31).date())]
        self.assertEqual(first["recorded_intervals"], 3)
        self.assertEqual(first["valid_intervals"], 2)
        self.assertEqual(first["rejected_intervals"], 1)
        self.assertEqual(first["valid_mm"], Decimal("0.3"))
        self.assertEqual(second["valid_mm"], Decimal("0.4"))
        self.assertEqual(last["valid_mm"], Decimal("0.3"))

    def test_duplicate_station_timestamp_fails_closed(self):
        start = int(datetime(2021, 7, 1, tzinfo=PRAGUE).timestamp())
        row = {"STATION": "0-203-0-11777", "ELEMENT": "SRA10M", "DT": "2021-07-01T00:10Z", "VALUE": "0", "FLAG": "", "QUALITY": "0.0"}
        with self.assertRaisesRegex(ValueError, "duplicate SRA10M"):
            summarize_chmi_10min([row, row], start, start + 30000)


if __name__ == "__main__":
    unittest.main()
