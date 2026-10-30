import csv
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from meteo_audit import monthly
from meteo_audit.db import ReadOnlyQueryError

PRAGUE = ZoneInfo("Europe/Prague")


def epoch(text: str) -> int:
    return int(datetime.fromisoformat(text).timestamp())


def row(when: str, rain: str = "0", rate: str = "0", interval: int = 5, units: int = 16) -> str:
    return f"{epoch(when)}\t{interval}\t{units}\t{rain}\t{rate}"


class PeriodBoundaryTests(unittest.TestCase):
    def summarize(self, rows, start, stop):
        return monthly.summarize_rows(
            rows, start, stop, int(start.timestamp()) - 3600,
            int(stop.timestamp()) + 3600, 5,
        )

    def test_local_midnight_archival_record_belongs_to_previous_civic_day(self):
        start = datetime(2021, 7, 1, tzinfo=PRAGUE)
        stop = datetime(2021, 7, 2, tzinfo=PRAGUE)
        result = self.summarize([row("2021-07-02T00:00:00+02:00", "0.2")], start, stop)
        self.assertEqual(result["rain_sum_stored"], 0.2)
        self.assertEqual(result["max_local_civic_day_sum_stored"], 0.2)

    def test_month_and_year_boundaries_use_right_inclusive_interval(self):
        start = datetime(2020, 12, 1, tzinfo=PRAGUE)
        stop = datetime(2021, 1, 1, tzinfo=PRAGUE)
        result = self.summarize([row("2021-01-01T00:00:00+01:00", "0.4")], start, stop)
        self.assertEqual(result["rain_sum_stored"], 0.4)
        self.assertEqual(monthly._period_key(epoch("2021-01-01T00:00:00+01:00"), "day"), "2020-12-31")

    def test_adjacent_periods_count_a_boundary_record_once(self):
        boundary = epoch("2021-08-01T00:00:00+02:00")
        previous = datetime(2021, 7, 1, tzinfo=PRAGUE)
        next_period = datetime(2021, 8, 1, tzinfo=PRAGUE)
        after = datetime(2021, 9, 1, tzinfo=PRAGUE)
        all_rows = [f"{boundary}\t5\t16\t0.3\t0"]
        left_rows = [value for value in all_rows if int(value.split("\t")[0]) > int(previous.timestamp())
                     and int(value.split("\t")[0]) <= int(next_period.timestamp())]
        right_rows = [value for value in all_rows if int(value.split("\t")[0]) > int(next_period.timestamp())
                      and int(value.split("\t")[0]) <= int(after.timestamp())]
        left = self.summarize(left_rows, previous, next_period)
        right = self.summarize(right_rows, next_period, after)
        self.assertEqual(left["rows"] + right["rows"], 1)
        self.assertAlmostEqual(float(left["rain_sum_stored"] or 0) + float(right["rain_sum_stored"] or 0), 0.3)

    def test_spring_dst_month_has_23_hour_day_and_no_synthetic_local_hour(self):
        start = datetime(2021, 3, 28, tzinfo=PRAGUE)
        stop = datetime(2021, 3, 29, tzinfo=PRAGUE)
        self.assertEqual(int(stop.timestamp() - start.timestamp()), 23 * 3600)
        hour_keys = {
            monthly._period_key(epoch("2021-03-28T01:00:00+00:00"), "hour"),
            monthly._period_key(epoch("2021-03-28T02:00:00+00:00"), "hour"),
        }
        self.assertEqual(hour_keys, {"2021-03-28T01+0100", "2021-03-28T03+0200"})

    def test_autumn_dst_repeated_local_hour_has_distinct_offsets(self):
        first = epoch("2021-10-31T02:30:00+02:00")
        second = epoch("2021-10-31T02:30:00+01:00")
        self.assertNotEqual(first, second)
        self.assertNotEqual(monthly._period_key(first, "hour"), monthly._period_key(second, "hour"))

    def test_null_zero_and_positive_rain_are_separate(self):
        start = datetime(2022, 1, 1, tzinfo=PRAGUE)
        stop = datetime(2022, 1, 2, tzinfo=PRAGUE)
        result = self.summarize([
            row("2022-01-01T00:05:00+01:00", r"\N"),
            row("2022-01-01T00:10:00+01:00", "0"),
            row("2022-01-01T00:15:00+01:00", "0.1"),
        ], start, stop)
        self.assertEqual(result["rain_null_rows"], 1)
        self.assertEqual(result["rain_zero_rows"], 1)
        self.assertEqual(result["rain_positive_rows"], 1)
        self.assertEqual(result["rows"], 3)

    def test_missing_timestamps_are_estimated_without_inventing_rows(self):
        start = datetime(2022, 1, 1, tzinfo=PRAGUE)
        stop = datetime(2022, 1, 1, 0, 20, tzinfo=PRAGUE)
        result = self.summarize([
            row("2022-01-01T00:05:00+01:00"),
            row("2022-01-01T00:15:00+01:00"),
        ], start, stop)
        self.assertEqual(result["missing_intervals_between_rows_estimated"], 1)
        self.assertEqual(result["rows"], 2)

    def test_last_archive_month_coverage_clips_to_last_record(self):
        start = datetime(2025, 2, 1, tzinfo=PRAGUE)
        stop = datetime(2025, 3, 1, tzinfo=PRAGUE)
        first = epoch("2025-02-27T21:00:00+01:00")
        last = epoch("2025-02-27T21:10:00+01:00")
        rows = [
            row("2025-02-27T21:00:00+01:00"),
            row("2025-02-27T21:05:00+01:00"),
            row("2025-02-27T21:10:00+01:00"),
        ]
        result = monthly.summarize_rows(rows, start, stop, first, last, 5)
        self.assertEqual(result["expected_grid_rows_estimated"], 3)
        self.assertEqual(result["row_coverage_pct_estimated"], 100.0)
        self.assertEqual(result["missing_rows_estimated"], 0)
        self.assertTrue(result["first_archive_month_partial"])
        self.assertTrue(result["last_archive_month_partial"])

    def test_first_archive_row_counts_as_observed_grid_opportunity(self):
        start = datetime(2009, 3, 1, tzinfo=PRAGUE)
        stop = datetime(2009, 4, 1, tzinfo=PRAGUE)
        first = epoch("2009-03-29T18:45:00+02:00")
        last = epoch("2009-03-29T18:55:00+02:00")
        rows = [
            row("2009-03-29T18:45:00+02:00"),
            row("2009-03-29T18:50:00+02:00"),
            row("2009-03-29T18:55:00+02:00"),
        ]
        result = monthly.summarize_rows(rows, start, stop, first, last, 5)
        self.assertEqual(result["expected_grid_rows_estimated"], 3)
        self.assertEqual(result["missing_rows_estimated"], 0)

    def test_first_and_last_archive_months_are_marked_partial(self):
        start = datetime(2009, 3, 1, tzinfo=PRAGUE)
        stop = datetime(2009, 4, 1, tzinfo=PRAGUE)
        begin, end = int(start.timestamp()), int(stop.timestamp())
        result = monthly.summarize_rows([], start, stop, begin + 3600, end - 300, 5)
        self.assertTrue(result["calendar_month_complete"])
        self.assertTrue(result["first_archive_month_partial"])
        self.assertTrue(result["last_archive_month_partial"])
        self.assertEqual(result["range_status"], "no_rows_within_archive_range")

    def test_irregular_interval_is_reported_separately(self):
        start = datetime(2022, 1, 1, tzinfo=PRAGUE)
        stop = datetime(2022, 1, 1, 0, 20, tzinfo=PRAGUE)
        result = self.summarize([
            row("2022-01-01T00:05:00+01:00", interval=5),
            row("2022-01-01T00:17:00+01:00", interval=6),
        ], start, stop)
        self.assertEqual(result["irregular_timestamp_steps"], 1)
        self.assertEqual(result["off_5min_utc_grid_rows"], 1)

    def test_us_customary_rain_conversion_is_cm_to_mm(self):
        start = datetime(2022, 1, 1, tzinfo=PRAGUE)
        stop = datetime(2022, 1, 1, 0, 5, tzinfo=PRAGUE)
        result = self.summarize([row("2022-01-01T00:05:00+01:00", "0.25")], start, stop)
        self.assertEqual(result["rain_sum_mm_if_usUnits16"], 2.5)

    def test_yearly_aggregation_matches_monthly_totals_and_withholds_mixed_unit_conversion(self):
        jan_start = datetime(2021, 1, 1, tzinfo=PRAGUE)
        feb_start = datetime(2021, 2, 1, tzinfo=PRAGUE)
        mar_start = datetime(2021, 3, 1, tzinfo=PRAGUE)
        jan = monthly.summarize_rows([row("2021-01-31T23:55:00+01:00", "0.1")],
                                     jan_start, feb_start, int(jan_start.timestamp()) - 60,
                                     int(mar_start.timestamp()), 5)
        feb = monthly.summarize_rows([row("2021-02-28T23:55:00+01:00", "0.2")],
                                     feb_start, mar_start, int(jan_start.timestamp()) - 60,
                                     int(mar_start.timestamp()), 5)
        year = monthly.aggregate_yearly([jan, feb])[0]
        self.assertAlmostEqual(year["rain_sum_stored"], 0.3)
        self.assertAlmostEqual(year["rain_sum_mm_if_usUnits16"], 3.0)
        self.assertEqual(year["max_local_civic_day_sum_stored"], 0.2)
        self.assertEqual(year["max_5min_rain_stored"], 0.2)

        mixed = monthly.summarize_rows(
            [row("2021-01-31T23:55:00+01:00", "0.1"), row("2021-02-28T23:55:00+01:00", "0.2", units=17)],
            jan_start, mar_start, int(jan_start.timestamp()) - 60, int(mar_start.timestamp()), 5,
        )
        self.assertIsNone(monthly.aggregate_yearly([mixed])[0]["rain_sum_mm_if_usUnits16"])

    def test_rain_rate_is_reported_without_assuming_rain_times_twelve(self):
        start = datetime(2022, 1, 1, tzinfo=PRAGUE)
        stop = datetime(2022, 1, 1, 0, 10, tzinfo=PRAGUE)
        result = self.summarize([
            row("2022-01-01T00:05:00+01:00", "0.1", "0"),
            row("2022-01-01T00:10:00+01:00", "0", "7.5"),
        ], start, stop)
        self.assertEqual(result["rain_positive_rate_zero_rows"], 1)
        self.assertEqual(result["rate_positive_rain_zero_rows"], 1)
        self.assertEqual(result["max_rainRate_stored"], 7.5)

    def test_month_collection_is_local_calendar_and_stops_at_current_month(self):
        now = datetime(2021, 4, 12, tzinfo=PRAGUE)
        values = list(monthly.months(2021, 2022, now=now))
        self.assertEqual([start.strftime("%Y-%m") for start, _ in values], ["2021-01", "2021-02", "2021-03", "2021-04"])
        self.assertEqual(values[-1][1], now)

    def test_month_query_uses_allowlisted_schema_and_interval_end_comparison(self):
        start = datetime(2021, 7, 1, tzinfo=PRAGUE)
        stop = datetime(2021, 8, 1, tzinfo=PRAGUE)
        with patch.object(monthly, "query", return_value=[]) as mocked:
            monthly.audit_month(start, stop, 1, 2, 5, "loucka_reconstruction")
        sql = mocked.call_args.args[0]
        quoted_archive = chr(96) + "loucka_reconstruction" + chr(96) + "." + chr(96) + "archive" + chr(96)
        self.assertIn(quoted_archive, sql)
        self.assertIn("dateTime >", sql)
        self.assertIn("dateTime <=", sql)
        self.assertNotIn("dateTime >=", sql)

    def test_database_cli_choice_rejects_arbitrary_schema(self):
        with self.assertRaises(ReadOnlyQueryError):
            monthly.quote_database("anything")

    def test_cli_requires_explicit_database_choice(self):
        with patch.object(sys, "argv", ["monthly"]), self.assertRaises(SystemExit):
            monthly.main()


class OutputIsolationTests(unittest.TestCase):
    def run_main(self, database: str, out: Path):
        start = datetime(2021, 7, 1, tzinfo=PRAGUE)
        stop = datetime(2021, 8, 1, tzinfo=PRAGUE)

        def fake_query(sql, **kwargs):
            if "MIN(dateTime)" in sql:
                return ["1620000000\t1630000000"]
            if "GROUP BY" in sql:
                return ["5\t100"]
            if "SELECT dateTime" in sql:
                return [row("2021-07-01T00:05:00+02:00", "0.1")]
            return []

        with patch.object(monthly, "query", side_effect=fake_query), \
             patch.object(monthly, "months", return_value=iter([(start, stop)])), \
             patch.object(monthly, "_code_version", return_value="test123"), \
             patch.object(sys, "argv", ["monthly", "--database", database, "--output-dir", str(out)]), \
             redirect_stdout(io.StringIO()):
            monthly.main()

    def test_databases_write_to_distinct_csv_and_metadata_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            self.run_main("pocasi-loucka.eu", out)
            self.run_main("loucka_reconstruction", out)
            prod = out / "pocasi-loucka.eu" / "monthly_rain_coverage.csv"
            recon = out / "loucka_reconstruction" / "monthly_rain_coverage.csv"
            self.assertTrue(prod.exists())
            self.assertTrue(recon.exists())
            prod_meta = json.loads(prod.with_name("monthly_rain_coverage.metadata.json").read_text())
            recon_meta = json.loads(recon.with_name("monthly_rain_coverage.metadata.json").read_text())
            self.assertEqual(prod_meta["database"], "pocasi-loucka.eu")
            self.assertEqual(recon_meta["database"], "loucka_reconstruction")
            self.assertEqual(prod_meta["processed_rows"], 1)
            self.assertEqual(recon_meta["processed_rows"], 1)
            with (prod.parent / "yearly_rain_coverage.csv").open() as stream:
                year = next(csv.DictReader(stream))
            self.assertEqual(float(year["rain_sum_stored"]), 0.1)
            self.assertEqual(float(year["rain_sum_mm_if_usUnits16"]), 1.0)


if __name__ == "__main__":
    unittest.main()
