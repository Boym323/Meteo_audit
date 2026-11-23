"""Fail-closed tests for a read-only sensor deep-dive; no MariaDB writes."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "reports/data/2026-11-23-sensor-deepdive-qc-cohorts.json"
SQL = ROOT / "sql/readonly/production_sensor_mapping_pm25_followup_20261123.sql"
REPORT = ROOT / "reports/2026-11-23-deep-sensor-pm25-soil-mapping-followup.md"


class SensorDeepdiveInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_pinned_snapshot_and_parent_inventory_exist(self):
        self.assertEqual(self.data["schema"], "loucka-production-sensor-deepdive-v1")
        self.assertEqual(self.data["snapshot_cutoff_unix"], 1795415700)
        self.assertTrue(self.data["no_new_approved_operations"])
        self.assertTrue(self.data["independent_source_not_proven"])
        self.assertTrue((ROOT / self.data["parent_inventory"]).is_file())
        self.assertEqual(self.data["sql"], str(SQL.relative_to(ROOT)))

    def test_every_cohort_remains_unapproved(self):
        seen = set()
        allowed = set("ABCDEFGHIJKL")
        for c in self.data["cohorts"]:
            with self.subTest(cohort=c["id"]):
                self.assertNotIn(c["id"], seen)
                seen.add(c["id"])
                self.assertFalse(c["approved"])
                self.assertFalse(c["auto_apply"])
                self.assertEqual(c["status"], "QC_REVIEW_REQUIRED")
                self.assertTrue(set(c["evidence_sections"]) <= allowed)
                self.assertTrue(c["fields"])
                self.assertTrue(c["decision"])
                self.assertTrue(c["notes"])
        self.assertEqual(len(seen), 11)
        self.assertEqual(seen, {"RA"+str(i) for i in range(27, 38)})

    def test_counts_do_not_invent_approved_changes(self):
        c = {v["id"]: v for v in self.data["cohorts"]}
        self.assertEqual(c["RA27"]["observed_count"], 2128)
        self.assertEqual(c["RA28"]["observed_count"], 1551)
        self.assertIsNone(c["RA29"]["observed_count"])
        self.assertEqual(c["RA30"]["observed_count"], 11)
        self.assertEqual(c["RA31"]["observed_count"], 31)
        self.assertEqual(c["RA32"]["observed_count"], 1765)
        self.assertEqual(c["RA33"]["observed_count"], 14)
        self.assertEqual(c["RA34"]["observed_count"], 10555)
        self.assertIsNone(c["RA35"]["observed_count"])

    def test_all_sql_are_executable_read_only_selects(self):
        raw = SQL.read_text(encoding="utf-8")
        self.assertNotIn(chr(92)+chr(96), raw)
        no_comments = re.sub(r"(?m)^--[^\n]*", "", raw)
        statements = [s.strip() for s in no_comments.split(";") if s.strip()]
        self.assertEqual(len(statements), 12)
        for statement in statements:
            with self.subTest(query=statement[:45]):
                self.assertRegex(statement, r"^(SELECT|WITH)\b")
                self.assertIsNone(re.search(
                    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|REPLACE|GRANT)\b",
                    statement, re.I,
                ))

    def test_report_states_correct_nonindependent_mapping(self):
        report = REPORT.read_text(encoding="utf-8")
        for needle in (
            "2 128", "1 401", "90 917", "446", "1 551", "76 312",
            "1 765", "10 555", "2026-03-08 12:15",
            "2026-10-29 10:10", "NIKDY", "HOLD",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, report)


if __name__ == "__main__":
    unittest.main()
