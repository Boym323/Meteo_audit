"""Regressions for candidate humidity recovery, no MariaDB connection."""
import unittest

from meteo_audit.humidity_reconstruction import (
    reference_humidity_candidate, saturation_factor, short_gap_candidate
)


class ShortHumidityGapTests(unittest.TestCase):
    def test_july_2022_real_gap(self):
        self.assertAlmostEqual(
            short_gap_candidate(1657029000, 1657028700, 88.219205, 1657029300, 88.03324375),
            88.126224375, places=7
        )

    def test_august_2019_missing_three(self):
        for epoch, expected in (
            (1564776300, 62.64), (1564776600, 62.76), (1564776900, 62.88)
        ):
            self.assertAlmostEqual(
                short_gap_candidate(epoch, 1564775700, 62.4, 1564777200, 63.0),
                expected, places=8
            )

    def test_no_synthetic_long_gap(self):
        self.assertIsNone(short_gap_candidate(1000200, 1000000, 75, 1003600, 76))

    def test_reject_bad_anchors_and_clock(self):
        self.assertIsNone(short_gap_candidate(1200, 900, 10, 1500, 92))
        self.assertIsNone(short_gap_candidate(1200, 900, 0, 1500, 60))
        self.assertIsNone(short_gap_candidate(1200, 901, 75, 1500, 76))
        self.assertIsNone(short_gap_candidate(1500, 900, 75, 1500, 76))


class PhysicalModelTests(unittest.TestCase):
    def test_same_temperature(self):
        self.assertAlmostEqual(reference_humidity_candidate(14, 14, 81), 81)

    def test_higher_local_temperature_reduces_rh(self):
        self.assertLess(reference_humidity_candidate(20, 15, 80), 80)

    def test_invalid_sensor_values(self):
        for bad_rh in (0, 101, float("nan")):
            with self.assertRaises(ValueError):
                reference_humidity_candidate(20, 15, bad_rh)
        with self.assertRaises(ValueError):
            saturation_factor(float("inf"))




class DualReferenceJulyTests(unittest.TestCase):
    def test_candidate_written_to_db(self):
        from meteo_audit.humidity_reconstruction import july2022_dual_station_candidate
        self.assertEqual(july2022_dual_station_candidate(23.75, 23.0, 69.3, 72.0), 66.3)
        self.assertEqual(july2022_dual_station_candidate(24.125, 24.0, 70.3, 70.0), 66.7)

    def test_exclude_unreliable_references(self):
        from meteo_audit.humidity_reconstruction import july2022_dual_station_candidate
        self.assertIsNone(july2022_dual_station_candidate(24, 24, 15, 72))
        self.assertIsNone(july2022_dual_station_candidate(24, 28, 75, 76))
        self.assertIsNone(july2022_dual_station_candidate(24, 24, 0, 76))
        self.assertIsNone(july2022_dual_station_candidate(24, 24, float("nan"), 76))

    def test_moderate_quality_gate(self):
        from meteo_audit.humidity_reconstruction import july2022_dual_station_candidate
        self.assertIsNone(july2022_dual_station_candidate(23.3, 24.4, 70.0, 76.0))
        self.assertEqual(
            july2022_dual_station_candidate(23.3, 24.4, 70.0, 76.0,
                max_reference_gap_pp=6, max_temperature_gap_c=3),
            67.7
        )
        with self.assertRaises(ValueError):
            july2022_dual_station_candidate(20, 21, 70, 75, max_reference_gap_pp=15)



class LuhaMetMarch2022Tests(unittest.TestCase):
    def test_march_archive_correction(self):
        from meteo_audit.humidity_reconstruction import march2022_luhamet_candidate
        self.assertEqual(
            march2022_luhamet_candidate(0.95, 2.2, 50, 0.3, 47.3),
            52.7
        )
        self.assertEqual(
            march2022_luhamet_candidate(0.85, 1.6, 52, -0.2, 49.3),
            52.9
        )

    def test_reject_faulty_or_noncomparable_reference(self):
        from meteo_audit.humidity_reconstruction import march2022_luhamet_candidate
        self.assertIsNone(march2022_luhamet_candidate(0, 0, 0, 0, 50))
        self.assertIsNone(march2022_luhamet_candidate(0, 0, 55, 0, 80))
        self.assertIsNone(march2022_luhamet_candidate(0, 4, 55, 0, 54))
        self.assertIsNone(march2022_luhamet_candidate(0, 0, 55, float("nan"), 54))


class HistoricalLuhaMetTests(unittest.TestCase):
    def test_real_archive_examples(self):
        from meteo_audit.humidity_reconstruction import historical_luhamet_candidate
        cases = (
            (10.9166666666667, 11.3, 43, 44.1),
            (-6.6, -6.1, 82, 85.2),
            (-0.3, 0.7, 86, 92.5),
            (-1.03333333333333, -0.1, 83, 88.8),
            (0.7, 1.7, 79, 84.9),
        )
        for local_t, ref_t, rh, expected in cases:
            self.assertEqual(
                historical_luhamet_candidate(local_t, ref_t, rh, rh, rh),
                expected,
            )

    def test_reject_invalid_and_unstable_reference(self):
        from meteo_audit.humidity_reconstruction import historical_luhamet_candidate
        self.assertIsNone(historical_luhamet_candidate(12, 12, 0, 0, 0))
        self.assertIsNone(historical_luhamet_candidate(12, 12, 75, 0, 75))
        self.assertIsNone(historical_luhamet_candidate(12, 12, 75, 75, 95))
        self.assertIsNone(historical_luhamet_candidate(12, 15, 75, 75, 75))
        self.assertIsNone(historical_luhamet_candidate(12, float("nan"), 75, 75, 75))

if __name__ == "__main__":
    unittest.main()
