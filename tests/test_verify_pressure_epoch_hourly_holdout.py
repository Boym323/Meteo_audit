"""Synthetic tests only. Full hourly experiment requires existing LXC CHMI cache."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/verify_pressure_epoch_hourly_holdout.py"
spec = importlib.util.spec_from_file_location("epoch_hourly", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class HourlyCalibrationTest(unittest.TestCase):
    def test_robust_metrics(self):
        got = m.summary([-2.0, 0.0, 2.0])
        self.assertEqual(got["n"], 3)
        self.assertEqual(got["median_bias"], 0.0)
        self.assertEqual(got["mad"], 2.0)
        self.assertAlmostEqual(got["mae"], 4 / 3)
        self.assertEqual(m.summary([])["n"], 0)

    def test_utc_only_and_absolute_epoch_month(self):
        t = m.ts_epoch("2019-01-01T00:00:00Z")
        self.assertEqual(m.month(t), "2019-01")
        self.assertEqual(m.month_x(t), 19 * 12)
        with self.assertRaises(ValueError):
            m.ts_epoch("2019-01-01T01:00:00+01:00")
        with self.assertRaises(ValueError):
            m.ts_epoch("2019-01-01T00:00:00")

    def test_frozen_model_cannot_refit_from_holdout(self):
        t = m.ts_epoch("2019-01-01T00:00:00Z")
        d = {"schema": "loucka-pressure-monthly-calibration-backtest-v1",
             "epochs": [{"id": "X", "type": "hourly", "splits": {"holdout": ["2019-01", "2019-03"]},
                         "references": {"H": {"selected": "constant", "models": {"constant": {"parameters": {"intercept": -20.0, "slope": 0.0}}}},
                                        "M": {"selected": "raw", "models": {"raw": {"parameters": {"intercept": 0.0, "slope": 0.0}}}}}}]}
        reference = {(m.STATIONS["H"], t): 1020.0, (m.STATIONS["M"], t): 1019.0}
        score = m.hourly_backtest(d, reference, {t: 1000.0})
        self.assertEqual(len(score), 4)
        h = next(x for x in score if x["trained_on"] == "H" and x["tested_on"] == "H")
        self.assertEqual(h["raw"]["mae"], 20.0)
        self.assertEqual(h["corrected"]["mae"], 0.0)
        self.assertEqual(h["diagnostic_hourly_gate"], "FAIL_OR_INSUFFICIENT")  # one hour is not enough

    def test_manifest_fail_closed_on_missing_sha(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            (base / "raw").mkdir()
            (base / "manifest.json").write_text(json.dumps({"items": [{
                "kind": "hourly_csv", "element": "P_hm", "station_id": m.STATIONS["H"],
                "availability": "available", "path": "missing.csv", "sha256": "0" * 64
            }]}))
            with self.assertRaisesRegex(ValueError, "SHA256"):
                m.load_chmi_hourly(base)


if __name__ == "__main__":
    unittest.main()
