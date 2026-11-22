import unittest

from meteo_audit.db import ReadOnlyQueryError
from meteo_audit.gap_screening import annual_gap_screening_sql, utc_year_bounds


class GapScreeningTests(unittest.TestCase):
    def test_utc_year_bounds_are_fixed_epoch_boundaries(self):
        self.assertEqual(utc_year_bounds(2024), (1704067200, 1735689600))

    def test_rejects_invalid_year(self):
        for year in (1969, 2200, "2024"):
            with self.subTest(year=year), self.assertRaises(ValueError):
                utc_year_bounds(year)

    def test_query_is_aggregate_only_and_uses_both_intervals(self):
        sql = annual_gap_screening_sql("loucka_reconstruction", 2016)
        self.assertTrue(sql.startswith("SELECT "))
        self.assertIn("LAG(dateTime)", sql)
        self.assertIn("LAG(current_interval)", sql)
        self.assertIn("LEAST(prev_interval,current_interval)", sql)
        self.assertIn("GROUP BY prev_interval,current_interval", sql)
        self.assertIn("dateTime < 1451606400 ORDER BY dateTime DESC LIMIT 1", sql)
        self.assertIn("UNION ALL", sql)
        self.assertIn("dateTime >= 1451606400 AND dateTime < 1483228800", sql)
        self.assertIn("dateTime < 1483228800", sql)

    def test_database_must_be_allowlisted(self):
        with self.assertRaises(ReadOnlyQueryError):
            annual_gap_screening_sql("untrusted_schema", 2016)


if __name__ == "__main__":
    unittest.main()
