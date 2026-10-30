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


if __name__ == "__main__":
    unittest.main()
