"""Boundary consistency between rainfall and rainRate audit modules."""
import unittest
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

from meteo_audit.time_bounds import archive_period_predicate, local_year_bounds, local_period_bounds, interval_overlap_seconds, interval_union_metrics, PRAGUE


class SharedArchiveBoundaryTests(unittest.TestCase):
    def test_local_month_bounds_include_dst_transitions(self):
        feb=local_period_bounds("2024-02")
        self.assertEqual(feb[1]-feb[0],29*86400)
        march=local_period_bounds("2024-03")
        self.assertEqual(march[1]-march[0],31*86400-3600)
        october=local_period_bounds("2024-10")
        self.assertEqual(october[1]-october[0],31*86400+3600)

    def test_archive_end_interval_clips_at_period_boundaries(self):
        start,end=local_period_bounds("2026-01")
        self.assertEqual(interval_overlap_seconds(start+120,300,start,end),120)
        self.assertEqual(interval_overlap_seconds(end+180,300,start,end),120)
        self.assertEqual(interval_overlap_seconds(start,300,start,end),0)
        self.assertEqual(interval_overlap_seconds(end+300,300,start,end),0)

    def test_first_and_last_archive_intervals_of_local_day_are_clipped(self):
        day_start = int(datetime.combine(date(2024, 5, 14), time(), PRAGUE).timestamp())
        next_day = int(datetime.combine(date(2024, 5, 15), time(), PRAGUE).timestamp())
        # Archive-end timestamps at both edges retain only support inside the day.
        self.assertEqual(interval_overlap_seconds(day_start + 120, 300, day_start, next_day), 120)
        self.assertEqual(interval_overlap_seconds(next_day + 180, 300, day_start, next_day), 120)
        self.assertEqual(next_day - day_start, 24 * 3600)

    def test_interval_crossing_month_boundary_is_split_by_actual_overlap(self):
        jan_start, jan_end = local_period_bounds("2024-01")
        feb_start, feb_end = local_period_bounds("2024-02")
        self.assertEqual(jan_end, feb_start)
        # A 5-minute interval ending three minutes into February overlaps
        # January for 2 minutes and February for 3 minutes.
        end = feb_start + 180
        self.assertEqual(interval_overlap_seconds(end, 300, jan_start, jan_end), 120)
        self.assertEqual(interval_overlap_seconds(end, 300, feb_start, feb_end), 180)

    def test_local_dst_transition_days_use_elapsed_utc_duration(self):
        spring_start = int(datetime.combine(date(2024, 3, 31), time(), PRAGUE).timestamp())
        spring_end = int(datetime.combine(date(2024, 4, 1), time(), PRAGUE).timestamp())
        autumn_start = int(datetime.combine(date(2024, 10, 27), time(), PRAGUE).timestamp())
        autumn_end = int(datetime.combine(date(2024, 10, 28), time(), PRAGUE).timestamp())
        self.assertEqual(spring_end - spring_start, 23 * 3600)
        self.assertEqual(autumn_end - autumn_start, 25 * 3600)
        # The two local 02:xx readings during the autumn fold are distinct UTC slots.
        first_two = datetime(2024, 10, 27, 2, 30, tzinfo=PRAGUE, fold=0)
        second_two = datetime(2024, 10, 27, 2, 30, tzinfo=PRAGUE, fold=1)
        self.assertEqual(int(second_two.timestamp()) - int(first_two.timestamp()), 3600)

    def test_irregular_and_long_intervals_are_clipped_by_actual_extent(self):
        start,end=local_period_bounds("2026-01")
        self.assertEqual(interval_overlap_seconds(start+901,901,start,end),901)
        self.assertEqual(interval_overlap_seconds(end+240,900,start,end),660)

    def test_off_grid_timestamp_uses_its_actual_interval_extent(self):
        self.assertEqual(interval_overlap_seconds(1_007, 37, 1_000, 1_100), 7)

    def test_interval_union_counts_boundaries_gaps_and_overlaps_without_overcoverage(self):
        period_start, period_end = 1_000, 2_000
        spans = [(1_000, 1_300), (1_300, 1_600), (1_600, 2_000)]
        result = interval_union_metrics(spans)
        self.assertEqual(result["covered_seconds"], period_end-period_start)
        self.assertEqual(result["internal_gap_seconds"], 0)
        self.assertEqual(result["overlap_seconds"], 0)
        self.assertLessEqual(result["covered_seconds"], period_end-period_start)

    def test_interval_union_reports_missing_and_overlapping_support(self):
        result = interval_union_metrics([(1_000, 1_300), (1_250, 1_500), (1_600, 2_000)])
        self.assertEqual(result["covered_seconds"], 900)
        self.assertEqual(result["overlap_seconds"], 50)
        self.assertEqual(result["overlap_rows"], 1)
        self.assertEqual(result["internal_gap_seconds"], 100)
        self.assertLessEqual(result["covered_seconds"], 1_000)

    def test_explicit_missing_archive_interval_remains_uncovered(self):
        start, stop = 0, 1_800
        # Six expected 5-minute slots with the middle slot absent.
        spans = [(0, 300), (300, 600), (900, 1_200), (1_200, 1_500), (1_500, 1_800)]
        result = interval_union_metrics(spans)
        self.assertEqual(result["covered_seconds"], 1_500)
        self.assertEqual(result["internal_gap_seconds"], 300)
        self.assertEqual(result["gap_spans"], [(600, 900)])
        self.assertLessEqual(result["covered_seconds"], stop - start)

    def test_interval_union_rejects_empty_or_noninteger_spans(self):
        for spans in [[(2, 2)], [(3, 2)], [(1, True)]]:
            with self.subTest(spans=spans), self.assertRaises(ValueError):
                interval_union_metrics(spans)

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
