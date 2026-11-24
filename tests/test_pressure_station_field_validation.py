import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_pressure_station_field as validation


class StationPressureValidationTests(unittest.TestCase):
    def test_hypsometric_transport_direction_and_round_trip(self):
        at_222 = validation.transport_station_pressure(950.0, 10.0, 222.25)
        self.assertGreater(at_222, 950.0)
        back = validation.transport_station_pressure(at_222, 10.0, 425.0, site_height_m=222.25)
        self.assertAlmostEqual(back, 950.0, places=10)

    def test_rejects_bad_pressure_and_temperature(self):
        with self.assertRaises(ValueError):
            validation.transport_station_pressure(float("nan"), 10.0, 222.25)
        with self.assertRaises(ValueError):
            validation.transport_station_pressure(950.0, 80.0, 222.25)

    def test_block_bootstrap_is_repeatable_and_needs_three_months(self):
        few = {"2020-01": [1.0], "2020-02": [2.0]}
        self.assertIsNone(validation.block_bootstrap_ci(few)["low_hpa"])
        many = {"2020-01": [1.0, 1.2], "2020-02": [2.0], "2020-03": [3.0]}
        self.assertEqual(validation.block_bootstrap_ci(many), validation.block_bootstrap_ci(many))


if __name__ == "__main__":
    unittest.main()
