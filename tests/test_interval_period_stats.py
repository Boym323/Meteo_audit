import unittest

from meteo_audit.interval_period_stats import summarize_clipped_nonoverlapping


class IntervalPeriodStatsTests(unittest.TestCase):
    def test_clips_month_boundary_and_weights_by_actual_overlap(self):
        result = summarize_clipped_nonoverlapping(
            [(0, 60, "2"), (60, 120, "4"), (120, 180, "8")], 30, 150
        )
        self.assertEqual(result["covered_seconds"], 120)
        self.assertEqual(result["clipped_intervals"], 2)
        self.assertEqual(result["time_coverage"], 1)
        self.assertEqual(result["weighted_mean"], "4.5")

    def test_excludes_overlapping_aggregate_interval_without_double_counting(self):
        result = summarize_clipped_nonoverlapping(
            [(0, 60, "2"), (30, 90, "100"), (90, 120, "4")], 0, 120
        )
        self.assertEqual(result["covered_seconds"], 90)
        self.assertEqual(result["overlap_excluded_intervals"], 1)
        self.assertEqual(result["weighted_mean"], "2.666666666666666666666666667")
        self.assertEqual(result["longest_gap_seconds"], 30)

    def test_gap_and_empty_period_coverage_are_explicit(self):
        result = summarize_clipped_nonoverlapping([(10, 20, "1")], 0, 30)
        self.assertEqual(result["time_coverage"], 1 / 3)
        self.assertEqual(result["gap_count"], 2)
        self.assertEqual(result["longest_gap_seconds"], 10)


if __name__ == "__main__":
    unittest.main()
