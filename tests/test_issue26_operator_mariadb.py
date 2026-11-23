"""Issue26 operator CLI: existing account only, real synthetic MariaDB tests."""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from meteo_audit.approval_dryrun import CandidateBatch, FieldCorrection, PreflightError
from meteo_audit.approval_gate import challenge_for, sign_exact_batch
from meteo_audit.issue26_readonly_export import export_current_review


class ExistingAccountOperatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ISSUE26_CI_MYSQL") != "1":
            raise unittest.SkipTest("requires ephemeral synthetic MariaDB")
        import importlib.util
        import pymysql
        cls.pymysql = pymysql
        script = Path(__file__).resolve().parents[1] / "scripts" / "issue26_operator.py"
        spec = importlib.util.spec_from_file_location("issue26_operator", script)
        cls.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runner)
        cls.conn = pymysql.connect(
            host="127.0.0.1", port=3306, user="root", password="ci",
            database="loucka_reconstruction", autocommit=True,
        )
        with cls.conn.cursor() as cur:
            cur.execute("SELECT @@hostname,@@server_id,CURRENT_USER()")
            cls.host, cls.sid, cls.account = cur.fetchone()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setUp(self):
        with self.conn.cursor() as c:
            c.execute("DELETE FROM issue26_field_events")
            c.execute("DELETE FROM issue26_batch_events")
            c.execute("DELETE FROM reconstruction_changes")
            c.execute("DELETE FROM archive")
            c.execute(
                "INSERT INTO archive(dateTime,rain,outTemp,outHumidity) VALUES "
                "(1625097900,4.2567,NULL,NULL),"
                "(1540000000,NULL,1.0,40.0),"
                "(1540000300,NULL,0.0,55.0)"
            )
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.batch = CandidateBatch("ci-owner-exact", (
            FieldCorrection(
                1540000000, "outTemp", 1.0, 2.5,
                "raw:synthetic", "unit:synthetic",
                "rule:v1", "HIGH", "MEDIUM",
            ),
        ))
        self.review = export_current_review(
            self.conn, self.batch,
            expected_hostname=self.host, expected_server_id=self.sid,
        )
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_text(json.dumps({
            "batch_id": self.batch.batch_id,
            "schema": self.batch.schema, "target": self.batch.target,
            "operations": [asdict(x) for x in self.batch.operations],
        }))
        self.review_path = self.root / "review.json"
        self.review_path.write_text(json.dumps(self.review))
        self.key = bytes(range(32))
        self.key_path = self.root / "owner.key"
        self.key_path.write_bytes(self.key)
        os.chmod(self.key_path, 0o600)
        self.saved_receipt = None

    def _operation(self, mode, *, execute=False, receipt=None, prompt=None):
        with patch.object(self.runner, "EXPECTED_HOST", self.host):
            with patch.object(self.runner, "EXPECTED_SERVER_ID", self.sid):
                with patch.object(self.runner, "EXISTING_ACCOUNT", self.account):
                    return self.runner.operation(
                        self.conn, mode=mode,
                        manifest_path=str(self.manifest_path),
                        review_path=str(self.review_path),
                        receipt_path=str(receipt) if receipt else None,
                        key_path=str(self.key_path),
                        execute=execute,
                        prompt=prompt if prompt is not None else lambda _: "",
                        expected_hostname=self.host,
                        expected_server_id=self.sid,
                        expected_account=self.account,
                        now=1795430020,
                    )

    def _sign(self, *, now):
        sig = sign_exact_batch(
            self.batch, self.review["snapshot"],
            approver="owner:ci-review",
            entered_challenge=challenge_for(self.batch, self.review["snapshot"]),
            secret_key=self.key, now=now,
        )
        path = self.root / ("receipt-" + str(now) + ".json")
        path.write_text(json.dumps(asdict(sig)))
        os.chmod(path, 0o600)
        return path

    def _phrase(self, mode):
        prefix = ("APLIKUJI-DAVKU:" if mode == "apply" else "VRATIT-DAVKU:")
        return prefix + self.batch.batch_id + ":" + self.batch.payload_sha256 + ":" + self.review["snapshot"]["before_image_sha256"]

    def _value(self):
        with self.conn.cursor() as c:
            c.execute("SELECT outTemp FROM archive WHERE dateTime=1540000000")
            return c.fetchone()[0]

    def _event_count(self):
        with self.conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM issue26_batch_events")
            return c.fetchone()[0]

    def test_status_select_only_and_account_pin(self):
        status = self.runner.live_status(
            self.conn, expected_hostname=self.host,
            expected_server_id=self.sid, expected_account=self.account,
        )
        self.assertEqual(status["db_writes"], 0)
        self.assertEqual(status["new_sql_users"], 0)
        self.assertEqual(status["audit"]["status"], "DDL_VERIFIED")
        self.assertEqual(status["batch_events"], 0)
        with self.assertRaisesRegex(PreflightError, "account"):
            self.runner.live_status(
                self.conn, expected_hostname=self.host,
                expected_server_id=self.sid, expected_account="wrong@%",
            )

    def test_inspect_no_execution_or_signature_required(self):
        result = self._operation("inspect")
        self.assertEqual(result["db_writes"], 0)
        self.assertEqual(self._value(), 1.0)
        self.assertEqual(self._event_count(), 0)
        with self.assertRaises(PreflightError):
            self._operation("inspect", execute=True)

    def test_apply_requires_exact_sign_and_explicit_manual_confirmation(self):
        signed = self._sign(now=1795430000)
        with self.assertRaisesRegex(PreflightError, "execute"):
            self._operation("apply", receipt=signed)
        with self.assertRaisesRegex(PreflightError, "confirmation"):
            self._operation(
                "apply", execute=True, receipt=signed,
                prompt=lambda _: "YES",
            )
        self.assertEqual(self._event_count(), 0)
        result = self._operation(
            "apply", execute=True, receipt=signed,
            prompt=lambda _: self._phrase("apply"),
        )
        self.assertEqual(result["status"], "COMMITTED_APPLY")
        self.assertEqual(self._value(), 2.5)
        self.assertEqual(self._event_count(), 1)
        with self.assertRaisesRegex(PreflightError, "already"):
            self._operation(
                "apply", execute=True, receipt=signed,
                prompt=lambda _: self._phrase("apply"),
            )

    def test_rollback_requires_different_signed_receipt_and_manual_phrase(self):
        first = self._sign(now=1795430000)
        self._operation("apply", execute=True, receipt=first,
                        prompt=lambda _: self._phrase("apply"))
        with self.assertRaisesRegex(PreflightError, "DIFFERENT"):
            self._operation("rollback", execute=True, receipt=first,
                            prompt=lambda _: self._phrase("rollback"))
        second = self._sign(now=1795430010)
        with self.assertRaisesRegex(PreflightError, "confirmation"):
            self._operation("rollback", execute=True, receipt=second,
                            prompt=lambda _: "NO")
        outcome = self._operation(
            "rollback", execute=True, receipt=second,
            prompt=lambda _: self._phrase("rollback"),
        )
        self.assertEqual(outcome["status"], "COMMITTED_ROLLBACK")
        self.assertEqual(self._value(), 1.0)
        self.assertEqual(self._event_count(), 2)

    def test_reject_modified_report_without_sql_writes(self):
        invalid = dict(self.review)
        invalid["identity"] = {**self.review["identity"], "hostname": "unexpected"}
        self.review_path.write_text(json.dumps(invalid))
        with self.assertRaisesRegex(PreflightError, "source review DB"):
            self._operation("inspect")
        self.assertEqual(self._event_count(), 0)

    def test_reject_expired_signature_without_writes(self):
        sig = self._sign(now=1795420000)
        with self.assertRaisesRegex(PreflightError, "expired"):
            self._operation("apply", execute=True, receipt=sig,
                            prompt=lambda _: self._phrase("apply"))
        self.assertEqual(self._value(), 1.0)
        self.assertEqual(self._event_count(), 0)


if __name__ == "__main__":
    unittest.main()
