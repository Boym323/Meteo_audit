import csv
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from meteo_audit import rainrate


class RainRateAuditTests(unittest.TestCase):
    def test_local_year_bounds_use_prague_standard_time_midnights(self):
        start, stop = rainrate.year_bounds(2021)
        tz = ZoneInfo("Europe/Prague")
        self.assertEqual(datetime.fromtimestamp(start, tz), datetime(2021, 1, 1, tzinfo=tz))
        self.assertEqual(datetime.fromtimestamp(stop, tz), datetime(2022, 1, 1, tzinfo=tz))
        self.assertEqual(stop - start, 365 * 86400)

    def test_yearly_query_uses_allowlisted_schema_and_stored_categories(self):
        with patch.object(rainrate, "query", return_value=["3\t1\t1\t1\t0\t1\t2\t1\t1"]) as mocked:
            result = rainrate.audit_year("loucka_reconstruction", 2021)
        query = mocked.call_args.args[0]
        quoted = chr(96) + "loucka_reconstruction" + chr(96) + ".archive"
        self.assertIn(quoted, query)
        self.assertIn("dateTime >=", query)
        self.assertIn("dateTime <", query)
        self.assertEqual(result["archive_rows"], 3)
        self.assertEqual(result["rain_null_rows"], 1)
        self.assertEqual(result["rain_zero_rows"], 1)
        self.assertEqual(result["rain_positive_rows"], 1)
        self.assertEqual(result["rain_positive_rate_zero_rows"], 1)
        self.assertEqual(result["rate_positive_rain_zero_rows"], 1)

    def test_reports_and_metadata_are_separate_by_database(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            fake_rows = ["2\t0\t1\t1\t0\t1\t1\t1\t0"]
            with patch.object(rainrate, "ALLOWED_DATABASES", frozenset({"pocasi-loucka.eu", "loucka_reconstruction"})), \
                 patch.object(rainrate, "query", return_value=fake_rows), \
                 patch.object(rainrate, "_code_version", return_value="test123"), \
                 patch.object(sys, "argv", ["rainrate", "--start-year", "2021", "--end-year", "2021", "--output-dir", str(output)]):
                rainrate.main()
            paths = [
                output / database / "annual_rainrate_divergence.csv"
                for database in ("pocasi-loucka.eu", "loucka_reconstruction")
            ]
            self.assertTrue(all(path.exists() for path in paths))
            self.assertNotEqual(paths[0].parent, paths[1].parent)
            with paths[1].open(encoding="utf-8") as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(row["database"], "loucka_reconstruction")
            metadata = json.loads(paths[1].with_name("annual_rainrate_divergence.metadata.json").read_text())
            self.assertEqual(metadata["processed_rows"], 2)
            self.assertEqual(metadata["analysis_code_version"], "test123")


if __name__ == "__main__":
    unittest.main()
