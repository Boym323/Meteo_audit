"""Unit tests for source consensus and WeeWX daily rainfall grouping."""

import unittest
from datetime import datetime
from decimal import Decimal

from meteo_audit.rain_reconstruction import agreed_local_rain, summarize_archive
from meteo_audit.time_bounds import PRAGUE


class LocalRainConsensusTests(unittest.TestCase):
    def test_exact_three_source_consensus_preserves_zero(self):
        self.assertEqual(
            agreed_local_rain(
                {"production_rain": "0", "gw1000_rain": 0.0, "legacy_rain": "0.000"}
            ),
            Decimal("0"),
        )

    def test_nonzero_consensus_is_returned_exactly(self):
        self.assertEqual(
            agreed_local_rain(
                {
                    "production_rain": "0.02794",
                    "gw1000_rain": "0.02794",
                    "legacy_rain": "0.02794",
                }
            ),
            Decimal("0.02794"),
        )

    def test_missing_or_disagreeing_source_is_not_imputed(self):
        self.assertIsNone(
            agreed_local_rain(
                {"production_rain": "0.1", "gw1000_rain": None, "legacy_rain": "0.1"}
            )
        )
        self.assertIsNone(
            agreed_local_rain(
                {
                    "production_rain": "0.1",
                    "gw1000_rain": "0",
                    "legacy_rain": "0.1",
                }
            )
        )


class WeeWxDailyRainTests(unittest.TestCase):
    def test_month_uses_start_exclusive_end_inclusive_and_interval_start_day(self):
        start = int(datetime(2021, 7, 1, tzinfo=PRAGUE).timestamp())
        end = int(datetime(2021, 8, 1, tzinfo=PRAGUE).timestamp())
        rows = [
            {"dateTime": start, "interval": 5, "rain": "9"},  # excluded
            {"dateTime": start + 300, "interval": 5, "rain": "0.1"},
            # This row ends at midnight July 2; its interval starts July 1.
            {"dateTime": start + 86400, "interval": 5, "rain": "0.2"},
            {"dateTime": start + 86400 + 300, "interval": 5, "rain": None},
            # This end boundary is included; its interval starts July 31.
            {"dateTime": end, "interval": 5, "rain": "0.3"},
            {"dateTime": end + 300, "interval": 5, "rain": "9"},  # excluded
        ]
        daily = summarize_archive(rows, start, end)
        self.assertEqual(daily[datetime(2021, 7, 1).date()]["intervals"], 2)
        self.assertEqual(daily[datetime(2021, 7, 1).date()]["known_mm"], Decimal("3.0"))
        self.assertEqual(daily[datetime(2021, 7, 2).date()]["unknown_intervals"], 1)
        self.assertEqual(daily[datetime(2021, 7, 31).date()]["known_mm"], Decimal("3.0"))
        self.assertEqual(sum(int(bucket["intervals"]) for bucket in daily.values()), 4)


if __name__ == "__main__":
    unittest.main()
