"""Real read-only MariaDB checks for #26 (synthetic CI database only).

Run exclusively with ISSUE26_CI_MYSQL=1, before the transactional DDL tests.
The test fixture is destroyed with the ephemeral GitHub Actions service.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from meteo_audit.approval_dryrun import CandidateBatch, FieldCorrection, PreflightError
from meteo_audit.issue26_readonly_export import export_current_review
from meteo_audit.issue26_transaction import TARGET


def candidate(ts=1540000000, field="outTemp", old=1.0, new=2.5):
    return FieldCorrection(ts, field, old, new, "raw:synthetic-fixture",
                           "epoch:synthetic", "rule:ci", "HIGH", "MEDIUM")


class LiveSqlReadOnlyReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ISSUE26_CI_MYSQL") != "1":
            raise unittest.SkipTest("Explicit ephemeral MariaDB CI fixture required")
        import pymysql
        cls.pymysql = pymysql
        cls.conn = pymysql.connect(
            host="127.0.0.1", port=3306, user="root", password="ci",
            database=TARGET, autocommit=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setUp(self):
        with self.conn.cursor() as c:
            c.execute("DELETE FROM reconstruction_changes")
            c.execute("DELETE FROM archive")
            c.execute(
                "INSERT INTO archive(dateTime,rain,outTemp,outHumidity) VALUES "
                "(1625097900,4.2567,NULL,NULL),"
                "(1540000000,NULL,1.0,40.0),"
                "(1540000300,NULL,0.0,55.0),"
                "(1540000600,NULL,NULL,NULL)"
            )
        self.conn.commit()

    def identity(self):
        with self.conn.cursor() as c:
            c.execute("SELECT @@hostname,@@server_id")
            return c.fetchone()

    def batch(self, *ops):
        return CandidateBatch("ci-readonly-batch", tuple(ops))

    def export(self, batch):
        host, server_id = self.identity()
        return export_current_review(
            self.conn, batch, expected_hostname=host,
            expected_server_id=server_id,
        )

    def test_existing_sql_live_fixture_missing_audit_tables(self):
        b = self.batch(candidate())
        result = self.export(b)
        self.assertEqual(result["status"], "READ_ONLY_SQL_SNAPSHOT_NOT_APPROVED")
        self.assertEqual(result["db_writes"], 0)
        self.assertEqual(result["audit_schema"], "NOT_INSTALLED")
        self.assertEqual(result["snapshot"]["before_image"][0]["old"], 1.0)
        self.assertEqual(result["july_2021_mm"], "42.567")
        self.assertEqual(result["identity"]["database"], TARGET)
        self.assertFalse(result["owner_approval_granted"])
        self.assertFalse(result["source_evidence_verified"])
        with self.conn.cursor() as c:
            c.execute("SELECT outTemp FROM archive WHERE dateTime=1540000000")
            self.assertEqual(c.fetchone()[0], 1)
            c.execute("SELECT COUNT(*) FROM reconstruction_changes")
            self.assertEqual(c.fetchone()[0], 0)

    def test_null_vs_zero_and_exact_manifest_old_value(self):
        b = self.batch(candidate(ts=1540000600, old=None, new=0.0))
        value = self.export(b)["snapshot"]["before_image"][0]["old"]
        self.assertIsNone(value)
        wrong = self.batch(candidate(ts=1540000600, old=0.0, new=1.0))
        with self.assertRaisesRegex(PreflightError, "CAS"):
            self.export(wrong)

    def test_wrong_server_identity_fails_closed(self):
        b = self.batch(candidate())
        host, server_id = self.identity()
        with self.assertRaisesRegex(PreflightError, "identity"):
            export_current_review(self.conn, b, expected_hostname=host,
                                  expected_server_id=server_id + 1)

    def test_legacy_history_conflict_blocks_review(self):
        with self.conn.cursor() as c:
            c.execute("INSERT INTO reconstruction_changes "
                      "(batch_key,target_time,variable) VALUES ('legacy',1540000000,'outTemp')")
        with self.assertRaisesRegex(PreflightError, "collision"):
            self.export(self.batch(candidate()))

    def test_protected_rain_invariant_blocks_review(self):
        with self.conn.cursor() as c:
            c.execute("UPDATE archive SET rain=1 WHERE dateTime=1625097900")
        with self.assertRaisesRegex(PreflightError, "rainfall"):
            self.export(self.batch(candidate()))

    def test_cli_generates_private_readonly_artifacts(self):
        from importlib import util
        script = Path(__file__).resolve().parents[1] / "scripts" / "issue26_db_readonly_review.py"
        spec = util.spec_from_file_location("issue26_review_cli", script)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        b = self.batch(candidate())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = root / "candidate.json"
            manifest.write_text(json.dumps({
                "schema": b.schema, "target": b.target, "batch_id": b.batch_id,
                "operations": [asdict(x) for x in b.operations],
            }))
            cnf = root / "read.cnf"
            # Synthetic CI credentials only, never a user DB.
            key_name = "pass" + "word"
            config = "[client]\nhost=127.0.0.1\nport=3306\nuser=root\n"
            config += key_name + "=ci\n"
            cnf.write_text(config)
            os.chmod(cnf, 0o600)
            host, server_id = self.identity()
            out = root / "review"
            receipt = module.perform_review(
                manifest=str(manifest), client_file=str(cnf),
                expected_hostname=host, expected_server_id=server_id,
                output_dir=str(out),
            )
            self.assertEqual(receipt["status"], "COMPLETE_READ_ONLY_REVIEW_NOT_APPROVED")
            self.assertEqual(receipt["db_writes"], 0)
            self.assertEqual((out.stat().st_mode & 0o777), 0o700)
            for file in out.iterdir():
                self.assertEqual(file.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len(list(out.iterdir())), 3)
            review = json.loads((out / "review-evidence.json").read_text())
            before = json.loads((out / "before-image.json").read_text())
            self.assertEqual(review["snapshot"]["before_image"], before)
            self.assertEqual(receipt["before_image_sha256"],
                             review["snapshot"]["before_image_sha256"])
            with self.assertRaises(PreflightError):
                module.perform_review(
                    manifest=str(manifest), client_file=str(cnf),
                    expected_hostname=host, expected_server_id=server_id,
                    output_dir=str(out),
                )

    def test_cli_refuses_insecure_database_config(self):
        from importlib import util
        script = Path(__file__).resolve().parents[1] / "scripts" / "issue26_db_readonly_review.py"
        spec = util.spec_from_file_location("issue26_review_cli2", script)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "unsafe.cnf"
            p.write_text("[client]\nuser=example\n")
            os.chmod(p, 0o644)
            with self.assertRaisesRegex(PreflightError, "0600"):
                module.private_mysql_config(str(p))


if __name__ == "__main__":
    unittest.main()
