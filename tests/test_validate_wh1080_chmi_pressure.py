"""Synthetic regression tests for the WH1080/ČHMÚ 2018 read-only audit."""
import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "scripts" / "validate_wh1080_chmi_pressure.py"
spec = importlib.util.spec_from_file_location("wh_audit", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TestWHPressure(unittest.TestCase):
    def test_height_transport(self):
        p = m.to_other_elevation(955.8, -1.1, 222.25)
        self.assertGreater(p, 955.8)
        self.assertLess(p, 990)

    def test_timestamps_and_quality(self):
        ts = int(datetime(2018, 1, 13, 17, 0, tzinfo=timezone.utc).timestamp())
        row = {"dateTime": ts, "usUnits": 16, "wh_usUnits": 17, "wh_pressure": 955.8,
               "pressure": None, "barometer": 1008.2, "outTemp": -1.1}
        refs = {("0-20000-0-11774", ts): {"P": 982.1, "P_hm": 1010.2}}
        obs, buckets = m.prepare_comparisons([row], refs)
        self.assertEqual(buckets["target_pressure_NULL"], 1)
        self.assertEqual(len(obs), 2)
        self.assertIn("WH_pressure_height_adjusted_minus_CHMI_P", [x["metric"] for x in obs])
        self.assertIn("target_barometer_minus_CHMI_P_hm", [x["metric"] for x in obs])
        with self.assertRaises(ValueError):
            m.prepare_comparisons([{**row, "usUnits": 17}], refs)
        with self.assertRaises(ValueError):
            m.prepare_comparisons([{**row, "dateTime": ts + 300}], refs)

    def test_baseline_and_groups(self):
        ts = int(datetime(2018, 1, 13, 17, 0, tzinfo=timezone.utc).timestamp())
        row = {"dateTime": ts, "usUnits": 16, "wh_usUnits": 17, "wh_pressure": 955.8,
               "pressure": 955.9, "barometer": 1008.2, "outTemp": -1.1}
        refs = {("0-20000-0-11774", ts): {"P": 982.1, "P_hm": 1010.2}}
        obs, buckets = m.prepare_comparisons([row], refs)
        self.assertEqual(buckets["target_pressure_present"], 1)
        self.assertEqual(len(obs), 4)
        groups = m.group_statistics(obs, monthly=False)
        self.assertEqual(len(groups), 4)
        self.assertTrue(all(g["n"] == 1 for g in groups))
        self.assertAlmostEqual(next(g["median_hpa"] for g in groups if g["metric"] == "WH_minus_target_pressure"), -0.1)

    def test_chmi_manifest_hash_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw"
            raw.mkdir()
            sid = "0-20000-0-11774"
            fake = b"STATION,ELEMENT,DT,VALUE,FLAG,QUALITY\n"
            path = raw / "a.csv"
            path.write_bytes(fake)
            manifest = root / "manifest.json"
            doc = {"items": [{"kind": "hourly_csv", "period": "2018-01", "station_id": sid, "element": "P",
                              "availability": "available", "path": "a.csv", "sha256": hashlib.sha256(fake).hexdigest()}]}
            manifest.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError, "coverage incomplete"):
                m.load_chmi_2018(manifest, raw)


if __name__ == "__main__":
    unittest.main()
