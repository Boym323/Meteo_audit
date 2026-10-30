"""Boundary consistency between rainfall and rainRate audit modules."""
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from meteo_audit.time_bounds import archive_period_predicate, local_year_bounds, PRAGUE


class SharedArchiveBoundaryTests(unittest.TestCase):
    def test_utc_predicate_is_exclusive_at_start_and_inclusive_at_end(self):
        start, end = local_year_bounds(2021)
        self.assertEqual(
            archive_period_predicate(start, end),
            f"dateTime > {start} AND dateTime <= {end}",
        )
        self.assertEqual(start, int(datetime(2021, 1, 1, tzinfo=PRAGUE).timestamp()))
        self.assertEqual(end, int(datetime(2022, 1, 1, tzinfo=PRAGUE).timestamp()))
        self.assertFalse(start < start <= end)
        self.assertTrue(local_year_bounds(2020)[0] < start <= local_year_bounds(2020)[1])
        self.assertTrue(start < end <= end)
        self.assertFalse(local_year_bounds(2022)[0] < end <= local_year_bounds(2022)[1])

    def test_year_predicates_share_the_same_new_year_boundary(self):
        dec_start, jan_first = local_year_bounds(2020)
        jan_start, next_jan = local_year_bounds(2021)
        self.assertEqual(jan_first, jan_start)
        self.assertIn(f"dateTime <= {jan_first}", archive_period_predicate(dec_start, jan_first))
        self.assertIn(f"dateTime > {jan_first}", archive_period_predicate(jan_start, next_jan))

    def test_invalid_boundary_arguments_are_rejected(self):
        for start, stop in ((2, 2), (2, 1), ("2", 3), (True, 3)):
            with self.subTest(start=start, stop=stop), self.assertRaises(ValueError):
                archive_period_predicate(start, stop)

    def test_local_year_boundaries_validate_year(self):
        for year in (1969, 2200, -1):
            with self.subTest(year=year), self.assertRaises(ValueError):
                local_year_bounds(year)


if __name__ == "__main__":
    unittest.main()
