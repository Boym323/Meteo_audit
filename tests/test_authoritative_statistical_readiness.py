import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_authoritative_statistical_readiness import TZ, expected_grid, numeric_equal


class AuthoritativeReadinessTests(unittest.TestCase):
    def test_dst_civil_days_use_real_elapsed_slots(self):
        self.assertEqual(expected_grid(dt.date(2026, 3, 29), 300, 0)[1], 276)
        self.assertEqual(expected_grid(dt.date(2026, 10, 25), 300, 0)[1], 300)

    def test_day_and_night_split_follows_local_clock(self):
        first, total, daytime, nighttime, _ = expected_grid(dt.date(2026, 1, 15), 300, 0)
        self.assertEqual(total, 288)
        self.assertEqual(daytime + nighttime, total)
        self.assertEqual(dt.datetime.fromtimestamp(first, TZ).date(), dt.date(2026, 1, 15))

    def test_field_epoch_lower_bound_advances_expected_grid_only_for_that_field(self):
        day = dt.date(2024, 1, 1)
        lower_bound = int(dt.datetime(2024, 1, 1, 1, 2, tzinfo=TZ).timestamp())
        first, total, _, _, _ = expected_grid(day, 300, 0, lower_bound)
        self.assertGreaterEqual(first, lower_bound)
        self.assertEqual(total, 275)
        # A different field with an earlier sensor epoch keeps its own complete grid.
        _, other_total, _, _, _ = expected_grid(day, 300, 0)
        self.assertEqual(other_total, 288)

    def test_numeric_comparison_preserves_decimal_equality(self):
        self.assertTrue(numeric_equal("1.2300", 1.23))
        self.assertFalse(numeric_equal("1.2301", 1.23))
        self.assertTrue(numeric_equal(None, None))
        self.assertFalse(numeric_equal(None, 0))


if __name__ == "__main__":
    unittest.main()
