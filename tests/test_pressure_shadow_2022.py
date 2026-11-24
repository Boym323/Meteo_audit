import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_pressure_shadow_2022 as m


class ShadowTest(unittest.TestCase):
    def setUp(self):
        self.model = m.load_model(ROOT / "models/pressure-shadow-2022-v1.json")

    def test_prediction_domain(self):
        self.assertTrue(950 < m.prediction(1013, 10, self.model) < 980)
        self.assertIsNone(m.prediction(1013, None, self.model))
        self.assertIsNone(m.prediction(1013, -20, self.model))
        self.assertIsNone(m.prediction(1080, 10, self.model))

    def test_common_hours_gate_and_missing_only(self):
        rows, refs = [], {}
        expected = m.prediction(1013, 10, self.model)
        for i in range(120):
            ts = m.START + i * 3600
            rows.append(dict(dateTime=ts, usUnits=16, pressure=None,
                             barometer=1013, outTemp=10))
            for sid, height in m.STATIONS.values():
                refs[(sid, ts)] = m.transport_station_pressure(expected, 10, height)
        rows.append(dict(dateTime=m.START + 300, usUnits=16, pressure=expected,
                         barometer=1013, outTemp=10))
        groups, candidates = m.evaluate(rows, refs, self.model)
        self.assertEqual(groups["2022-01"]["gate"], "PASS_DIAGNOSTIC_PREVIEW_ONLY")
        self.assertEqual(groups["2022-01"]["preview_rows"], 120)
        self.assertEqual(len(candidates), 120)
        self.assertEqual(groups["2022-01"]["local_control"]["n"], 1)
        # Fail on an independent reference disagreement.
        sid, height = m.STATIONS["M"]
        for i in range(120):
            refs[(sid, m.START + i * 3600)] += 10
        groups, _ = m.evaluate(rows, refs, self.model)
        self.assertEqual(groups["2022-01"]["preview_rows"], 0)

    def test_duplicate_fail_closed(self):
        row = dict(dateTime=m.START, usUnits=16, pressure=None, barometer=1013, outTemp=10)
        with self.assertRaises(ValueError):
            m.evaluate([row, row], {}, self.model)


if __name__ == "__main__":
    unittest.main()
