import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "reports/data/pressure-shadow-2022-v1"


class PressureShadowFollowupEvidenceTests(unittest.TestCase):
    def test_hash_manifest_and_candidate_row_count(self):
        expected = {}
        for line in (DATA / "SHA256SUMS.txt").read_text().splitlines():
            digest, name = line.split("  ", 1)
            expected[name] = digest
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((DATA / name).read_bytes()).hexdigest(), digest)
        with (DATA / "pressure-series-proposed-unapproved.csv").open(newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 15166)
        self.assertTrue(all(r["classification"] == "ESTIMATED" for r in rows))
        self.assertTrue(all(r["approval_status"] == "UNAPPROVED" for r in rows))
        self.assertTrue(all(float(r["empirical_uncertainty_hpa"]) > 0 for r in rows))
        self.assertEqual(len({r["dateTime_utc"] for r in rows}), len(rows))

    def test_original_preview_only_march_and_may(self):
        evidence = json.loads((DATA / "evidence.json").read_text())
        self.assertEqual(evidence["preview_rows"], 15166)
        self.assertEqual(evidence["approved_candidates"], 0)
        passed = [m for m, v in evidence["months"].items() if v["gate"] == "PASS_DIAGNOSTIC_PREVIEW_ONLY"]
        self.assertEqual(passed, ["2022-03", "2022-05"])

    def test_gate_unchanged_and_alternative_failures_remain(self):
        alt = json.loads((DATA / "alternative-models.json").read_text())
        self.assertEqual(alt["gate"], {
            "min_common_hours_per_month": 100,
            "min_common_coverage": 0.8,
            "max_mae_hpa": 2,
            "max_p95_absolute_hpa": 4,
            "max_abs_median_bias_hpa": 1.5,
        })
        for month in ("2022-02", "2022-04", "2022-06", "2022-07"):
            self.assertTrue(all(v["gate"] == "FAIL_OR_INSUFFICIENT"
                                for v in alt["months"][month]["models"].values()))

    def test_annual_status_inventory_preserves_unresolved_and_no_calibration(self):
        inv = json.loads((DATA / "annual-status-inventory.json").read_text())
        y22 = next(x for x in inv["annual_counts"] if x["year"] == 2022)
        self.assertEqual(y22["MEASURED"], 57890)
        self.assertEqual(y22["CALIBRATED"], 0)
        self.assertEqual(y22["ESTIMATED_UNAPPROVED"], 15166)
        self.assertEqual(y22["UNRESOLVED"], 31149)
        self.assertEqual(y22["pressure_null_total"], 46315)

    def test_quality_records_temporal_gaps_and_large_steps(self):
        q = json.loads((DATA / "preview-quality.json").read_text())
        mar = q["candidate_months"]["2022-03"]
        may = q["candidate_months"]["2022-05"]
        self.assertEqual(mar["n"], 6880)
        self.assertEqual(mar["max_gap_between_estimates_s"], 77400)
        self.assertAlmostEqual(mar["max_five_minute_estimate_step_hpa"], 5.2482, places=3)
        self.assertEqual(may["n"], 8286)
        self.assertEqual(may["max_gap_between_estimates_s"], 17400)


if __name__ == "__main__":
    unittest.main()
