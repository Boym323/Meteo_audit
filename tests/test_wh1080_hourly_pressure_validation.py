import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_wh1080_hourly_pressure_source as validation


class WH1080PressureValidationTests(unittest.TestCase):
    def test_hourly_validation_separates_missing_and_control(self):
        ts = 1514764800
        refs = {
            ("0-20000-0-11774", ts): {"P": 980.0},
            ("0-20000-0-11782", ts): {"P": 977.0},
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "export.csv"
            fields = ["dateTime_utc", "target_pressure_hpa", "target_outTemp_c",
                      "source_usUnits", "source_interval_minutes", "source_pressure_hpa"]
            with path.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerow(dict(dateTime_utc=ts, target_pressure_hpa="", target_outTemp_c=10,
                                     source_usUnits=17, source_interval_minutes=5, source_pressure_hpa=950))
                writer.writerow(dict(dateTime_utc=ts, target_pressure_hpa=950, target_outTemp_c=10,
                                     source_usUnits=17, source_interval_minutes=5, source_pressure_hpa=950))
            counts, groups = validation.evaluate(path, refs)
        self.assertEqual(counts["target_pressure_missing"], 1)
        self.assertEqual(counts["target_pressure_present"], 1)
        self.assertEqual(groups["H_missing"]["n"], 1)
        self.assertEqual(groups["M_present"]["n"], 1)

    def test_metrics_include_tail_error(self):
        result = validation.summary([-1.0, 1.0, 10.0])
        self.assertAlmostEqual(result["mae_hpa"], 4.0)
        self.assertEqual(result["median_bias_hpa"], 1.0)
        self.assertEqual(result["mad_hpa"], 2.0)
        self.assertGreater(result["p95_abs_error_hpa"], 9.0)


if __name__ == "__main__":
    unittest.main()
