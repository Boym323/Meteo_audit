"""Regression gates for READ-ONLY production archive anomaly cohort inventory.

These tests validate evidence structure, not the meteorological correctness
of an unapproved source replacement. They never connect to MariaDB.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "reports/data/2026-11-23-production-anomaly-cohorts.json"
SQL = ROOT / "sql/readonly/production_anomaly_inventory_20261123.sql"
REPORT = ROOT / "reports/2026-11-23-production-anomaly-reconstruction-inventory.md"


class ProductionAnomalyInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_snapshot_is_explicit_and_never_a_manifest(self):
        data = self.inventory
        self.assertEqual(data["schema"], "loucka-production-anomaly-cohort-registry-v1")
        self.assertEqual(data["source_rows"], 1686896)
        self.assertEqual(data["source_columns"], 80)
        self.assertEqual(data["source_max_dateTime"], 1795415700)
        self.assertTrue(data["read_only"])
        self.assertIn("NOT_APPROVED", data["status"])
        self.assertIn("Entries overlap", data["warning"])

    def test_every_cohort_is_review_only_without_auto_apply(self):
        seen = set()
        data = self.inventory
        for row in data["cohorts"]:
            with self.subTest(row=row["id"]):
                self.assertNotIn(row["id"], seen)
                seen.add(row["id"])
                self.assertFalse(row["approved"])
                self.assertFalse(row["auto_apply"])
                self.assertEqual(row["stage"], "FORENSIC_REVIEW_ONLY")
                self.assertEqual(row["source"], "pocasi-loucka.eu.archive")
                self.assertIn(row["sql_block"], "ABCDEFGHIJKLMNOPQR")
                self.assertTrue(row["fields"])
                self.assertTrue(row["decision"])
                self.assertTrue(row["note"])
                self.assertTrue(row["window"])
        self.assertEqual(len(seen), 26)

    def test_critical_source_and_phantom_counts_are_pinned_not_reinterpreted(self):
        entries = {r["id"]: r for r in self.inventory["cohorts"]}
        self.assertEqual(entries["RA01"]["observed_count"], 1592925)
        self.assertEqual(entries["RA03"]["observed_count"], 5659)
        self.assertEqual(entries["RA06"]["observed_count"], 44516)
        self.assertEqual(entries["RA22"]["observed_count"], 3264+5343+2261+4810)
        self.assertEqual(entries["RA24"]["observed_count"], 1077)
        self.assertEqual(entries["RA26"]["observed_count"], 0)
        self.assertIsNone(entries["RA23"]["observed_count"])

    def test_all_sql_statements_are_select_only_and_executable_quoted(self):
        raw = SQL.read_text(encoding="utf-8")
        self.assertNotIn("\\`", raw, "escaped backticks make SQL invalid")
        no_comments = re.sub(r"(?m)^--[^\n]*", "", raw)
        statements = [v.strip() for v in no_comments.split(";") if v.strip()]
        self.assertEqual(len(statements), 18)
        for sql in statements:
            with self.subTest(sql=sql[:60]):
                self.assertRegex(sql, r"^(SELECT|WITH)\b")
                self.assertIsNone(
                    re.search(r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|REPLACE|GRANT)\b", sql, re.I)
                )

    def test_full_report_is_present_and_distinguishes_source_from_certification(self):
        text = REPORT.read_text(encoding="utf-8")
        for term in ("1 686 896", "37 611", "5 659", "44 516",
                     "54 154", "92 664", "HOLD", "SOURCE_REVIEW",
                     "NULL", "2011", "2026", "NO_GO"):
            with self.subTest(term=term):
                self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
