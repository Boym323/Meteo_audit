import copy
import json
import unittest
from pathlib import Path

from meteo_audit.logger_lineage import (
    LineageEvidenceError, evaluate_logger_lineage,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/data/2026-11-22-cumulus-weewx-transition-evidence.json"


class LoggerLineageEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_original_2009_capture_anchors_cumulus_version(self):
        original = self.evidence["web_observations"][0]
        self.assertEqual(original["software_version"], "1.8.7")
        self.assertEqual(original["displayed_station"], "Watson W-8681 / Fine Offset")
        self.assertEqual(original["capture_utc"], 1251645949)
        self.assertIn("/web/20090830152549/", original["source_ref"])

    def test_reported_years_are_not_exact_wayback_captures(self):
        out = evaluate_logger_lineage(self.evidence)
        self.assertEqual(out["reported_cumulus_years"], [2013])
        self.assertEqual(out["reported_weewx_years"], [2017])
        self.assertEqual(out["last_direct_cumulus_utc"], 1251645949)
        self.assertIsNone(out["first_direct_weewx_utc"])
        self.assertEqual(out["website_generator_assessment"],
                         "NO_EXACT_WEB_GENERATOR_SWITCH_BOUND")
        self.assertIsNone(out["logger_switched_at_utc"])

    def test_even_two_exact_web_snapshots_only_bound_web_generator(self):
        data = copy.deepcopy(self.evidence)
        data["web_observations"].append({
            "generator": "WeeWX", "evidence_type": "DIRECT_ARCHIVE",
            "capture_utc": 1500000000, "year": 2017,
            "source_ref": "synthetic:archived-2017-page"
        })
        out = evaluate_logger_lineage(data)
        self.assertEqual(out["website_generator_assessment"],
                         "BOUNDED_WEB_GENERATOR_CHANGE_ONLY")
        self.assertIsNone(out["logger_switched_at_utc"])
        self.assertIsNone(out["hardware_switched_at_utc"])

    def test_direct_capture_mismatched_year_is_rejected(self):
        data = copy.deepcopy(self.evidence)
        data["web_observations"][0]["year"] = 2010
        with self.assertRaisesRegex(LineageEvidenceError, "year"):
            evaluate_logger_lineage(data)

    def test_user_year_only_evidence_cannot_inject_capture_time(self):
        data = copy.deepcopy(self.evidence)
        data["web_observations"][1]["capture_utc"] = 1380000000
        with self.assertRaisesRegex(LineageEvidenceError, "year-only"):
            evaluate_logger_lineage(data)

    def test_database_markers_must_not_claim_software(self):
        data = copy.deepcopy(self.evidence)
        data["archive_markers"][0]["logger"] = "WeeWX"
        with self.assertRaisesRegex(LineageEvidenceError, "unsupported"):
            evaluate_logger_lineage(data)

    def test_june_july_gap_and_new_markers_are_ordered(self):
        markers = self.evidence["archive_markers"]
        by = {(m["marker_type"], m["source"]): m["time_utc"] for m in markers}
        last = by[("archive_last_before_gap", "old_weewx.archive")]
        first = by[("archive_first_after_gap", "old_weewx.archive")]
        pressure = by[("first_field_present", "old_weewx.archive:pressure")]
        subminute = by[("first_subminute_timestamp", "old_weewx.archive")]
        self.assertEqual(last, 1403304540)
        self.assertEqual(first, 1404406800)
        self.assertEqual(first, pressure)
        self.assertEqual(subminute, 1404651601)
        self.assertLess(last, first)
        self.assertLess(first, subminute)
        self.assertGreater(first - last, 12 * 86400)

    def test_2013_numeric_change_is_not_software_switch(self):
        ratios = {r["window"]: r for r in self.evidence["wind_ratio_snapshots"]}
        self.assertEqual(ratios["2013-03 UTC"]["same_numeric_unit"], 4801)
        self.assertEqual(ratios["2013-03 UTC"]["x3_6"], 0)
        self.assertEqual(ratios["2013-05 through July UTC"]["x3_6"], 6259)
        out = evaluate_logger_lineage(self.evidence)
        self.assertIsNone(out["logger_switched_at_utc"])

    def test_2014_postgap_raw_times_differ_from_5min_target(self):
        snapshots = {r["window"]: r for r in self.evidence["wind_ratio_snapshots"]}
        after = snapshots["2014-Jul-03 through Jul-31 UTC"]
        self.assertLess(after["snapped_target_pairs"], after["source_rows"])
        self.assertEqual(after["source_rows"], 8406)
        self.assertEqual(after["x3_6"], 6815)

    def test_unverified_source_import_method(self):
        out = evaluate_logger_lineage(self.evidence)
        self.assertEqual(out["source_import_method"], "UNVERIFIED")
        self.assertEqual(out["disposition"], "FORENSIC_EVIDENCE_ONLY_NO_HISTORIC_DATA_WRITE")
        self.assertEqual(out["archive_pipeline_marker_count"], 9)
        self.assertEqual(self.evidence["interpretation"]["approved_historical_changes"], 0)

    def test_negative_or_boolean_marker_epoch_fails(self):
        for bad in (-1, True):
            with self.subTest(bad=bad):
                data = copy.deepcopy(self.evidence)
                data["archive_markers"][0]["time_utc"] = bad
                with self.assertRaises(LineageEvidenceError):
                    evaluate_logger_lineage(data)


if __name__ == "__main__":
    unittest.main()
