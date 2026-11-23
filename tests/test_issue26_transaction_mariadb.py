"""MariaDB 11.8 synthetic integration for issue #26 transactional engine.

Enabled ONLY by ISSUE26_CI_MYSQL=1. No production network config is included.
No permanent DB instance or backup/restore is required.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import os
import threading
import unittest

from meteo_audit.approval_dryrun import CandidateBatch, FieldCorrection, PreflightError, preflight
from meteo_audit.approval_gate import challenge_for, sign_exact_batch
from meteo_audit.issue26_transaction import (
    APPROVE_ROLLBACK, TransactionRejected, sql_preflight,
    apply_approved_batch, rollback_approved_batch,
)

KEY_MATERIAL = bytes(range(32))
NOW = 1795430000
EPOCH = 1540000000


def op(timestamp=EPOCH, variable="outTemp", before=1.0, after=2.5):
    return FieldCorrection(timestamp, variable, before, after,
                           "raw:synthetic", "unit:synthetic",
                           "rule:synthetic-v1", "HIGH", "MEDIUM")


class RealMariaDbTransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ISSUE26_CI_MYSQL") != "1":
            raise unittest.SkipTest("Requires explicit synthetic MariaDB CI fixture")
        import pymysql
        cls.pymysql = pymysql
        cls.connection_args = {
            "host": "127.0.0.1", "port": 3306, "user": "root",
            "password": "ci", "database": "loucka_reconstruction",
            "autocommit": True, "connect_timeout": 5,
        }
        cls.conn = cls.connect()
        schema = Path(__file__).resolve().parents[1] / "sql" / "issue26_transactional_audit_schema.sql"
        with cls.conn.cursor() as c:
            for statement in schema.read_text(encoding="utf-8").split(";"):
                if statement.strip():
                    c.execute(statement)
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    @classmethod
    def connect(cls):
        return cls.pymysql.connect(**cls.connection_args)

    def setUp(self):
        with self.conn.cursor() as c:
            c.execute("DELETE FROM issue26_field_events")
            c.execute("DELETE FROM issue26_batch_events")
            c.execute("DELETE FROM reconstruction_changes")
            c.execute("DELETE FROM archive")
            c.execute(
                "INSERT INTO archive (dateTime,rain,outTemp,outHumidity) VALUES "
                "(1625097900,4.2567,NULL,NULL),"
                "(1540000000,NULL,1.0,40.0),"
                "(1540000300,NULL,0.0,55.0),"
                "(1540000600,NULL,NULL,NULL)"
            )
        self.conn.commit()

    @staticmethod
    def batch(*ops, name="synthetic-batch-a"):
        return CandidateBatch(name, ops)

    def approve(self, conn, batch):
        report = sql_preflight(conn, batch)
        signature = sign_exact_batch(
            batch, report, approver="owner:ci-synthetic-only",
            entered_challenge=challenge_for(batch, report),
            secret_key=KEY_MATERIAL, now=NOW,
        )
        return report, signature

    def count(self, table):
        with self.conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM " + table)
            return c.fetchone()[0]

    def value(self, timestamp=EPOCH, col="outTemp"):
        self.assertIn(col, ("outTemp", "outHumidity"))
        with self.conn.cursor() as c:
            c.execute("SELECT " + col + " FROM archive WHERE dateTime=%s", (timestamp,))
            return c.fetchone()[0]

    def test_sql_preflight_is_select_only(self):
        b = self.batch(op())
        report = sql_preflight(self.conn, b)
        self.assertEqual(report["db_writes"], 0)
        self.assertEqual(self.value(), 1)
        self.assertEqual(self.count("issue26_batch_events"), 0)

    def test_real_apply_and_rollback_both_append_only(self):
        b = self.batch(op())
        report, signature = self.approve(self.conn, b)
        applied = apply_approved_batch(self.conn, b, report, signature,
                                       approval_key=KEY_MATERIAL, now=NOW)
        self.assertTrue(applied.committed)
        self.assertEqual(self.value(), 2.5)
        self.assertEqual(self.count("issue26_batch_events"), 1)
        self.assertEqual(self.count("issue26_field_events"), 1)

        # Rollback requires a FRESH owner signature and a separate exact phrase.
        fresh_signature = sign_exact_batch(
            b, report, approver="owner:ci-synthetic-only",
            entered_challenge=challenge_for(b, report),
            secret_key=KEY_MATERIAL, now=NOW+10,
        )
        rollback_phrase = (
            APPROVE_ROLLBACK + b.batch_id + ":" + b.payload_sha256
            + ":" + report["before_image_sha256"]
        )
        reverted = rollback_approved_batch(
            self.conn, b, report, fresh_signature, approval_key=KEY_MATERIAL,
            entered_rollback_challenge=rollback_phrase, now=NOW+20,
        )
        self.assertEqual(reverted.action, "ROLLBACK")
        self.assertEqual(self.value(), 1)
        self.assertEqual(self.count("issue26_batch_events"), 2)
        self.assertEqual(self.count("issue26_field_events"), 2)
        with self.assertRaisesRegex(PreflightError, "already"):
            apply_approved_batch(self.conn, b, report, signature,
                                 approval_key=KEY_MATERIAL, now=NOW)

    def test_second_apply_and_stale_approval_refused(self):
        b = self.batch(op())
        report, sig = self.approve(self.conn, b)
        self.assertTrue(apply_approved_batch(self.conn, b, report, sig,
                                              approval_key=KEY_MATERIAL, now=NOW).committed)
        with self.assertRaisesRegex(PreflightError, "already"):
            apply_approved_batch(self.conn, b, report, sig,
                                 approval_key=KEY_MATERIAL, now=NOW)
        self.assertEqual(self.value(), 2.5)

    def test_change_after_approval_blocks_any_write(self):
        b = self.batch(op())
        report, sig = self.approve(self.conn, b)
        with self.conn.cursor() as c:
            c.execute("UPDATE archive SET outTemp=9 WHERE dateTime=%s", (EPOCH,))
        with self.assertRaisesRegex(PreflightError, "CAS"):
            apply_approved_batch(self.conn, b, report, sig,
                                 approval_key=KEY_MATERIAL, now=NOW)
        self.assertEqual(self.count("issue26_batch_events"), 0)
        self.assertEqual(self.value(), 9)

    def test_null_safe_distinguishes_zero_and_missing(self):
        b = self.batch(op(timestamp=1540000600, before=None, after=0.0))
        report, sig = self.approve(self.conn, b)
        apply_approved_batch(self.conn, b, report, sig, approval_key=KEY_MATERIAL, now=NOW)
        self.assertEqual(self.value(1540000600), 0.0)
        with self.assertRaisesRegex(PreflightError, "already"):
            apply_approved_batch(self.conn, b, report, sig,
                                 approval_key=KEY_MATERIAL, now=NOW)

    def test_external_intervening_edit_blocks_rollback(self):
        b = self.batch(op())
        report, sig = self.approve(self.conn, b)
        apply_approved_batch(self.conn, b, report, sig, approval_key=KEY_MATERIAL, now=NOW)
        with self.conn.cursor() as c:
            c.execute("UPDATE archive SET outTemp=5 WHERE dateTime=%s", (EPOCH,))
        phrase = APPROVE_ROLLBACK + b.batch_id + ":" + b.payload_sha256 + ":" + report["before_image_sha256"]
        new_signature = sign_exact_batch(
            b, report, approver="owner:ci-synthetic-only",
            entered_challenge=challenge_for(b, report),
            secret_key=KEY_MATERIAL, now=NOW + 5,
        )
        with self.assertRaisesRegex(PreflightError, "post-image"):
            rollback_approved_batch(
                self.conn, b, report, new_signature, approval_key=KEY_MATERIAL,
                entered_rollback_challenge=phrase, now=NOW + 6,
            )
        self.assertEqual(self.count("issue26_batch_events"), 1)
        self.assertEqual(self.value(), 5)

    def test_rollback_rejects_original_apply_receipt_even_if_still_valid(self):
        b = self.batch(op())
        report, sig = self.approve(self.conn, b)
        apply_approved_batch(self.conn, b, report, sig,
                             approval_key=KEY_MATERIAL, now=NOW)
        phrase = APPROVE_ROLLBACK + b.batch_id + ":" + b.payload_sha256 + ":" + report["before_image_sha256"]
        with self.assertRaisesRegex(PreflightError, "DIFFERENT"):
            rollback_approved_batch(
                self.conn, b, report, sig, approval_key=KEY_MATERIAL,
                entered_rollback_challenge=phrase, now=NOW + 1,
            )
        self.assertEqual(self.value(), 2.5)
        self.assertEqual(self.count("issue26_batch_events"), 1)

    def test_foreign_change_history_blocks_apply(self):
        with self.conn.cursor() as c:
            c.execute("INSERT INTO reconstruction_changes "
                      "(batch_key,target_time,variable) VALUES (%s,%s,%s)",
                      ("older-change", EPOCH, "outTemp"))
        b = self.batch(op())
        with self.assertRaisesRegex(PreflightError, "legacy"):
            sql_preflight(self.conn, b)

    def test_multi_field_atomic_rollback_on_sql_failure(self):
        b = self.batch(
            op(), op(timestamp=1540000300, variable="outHumidity",
                     before=55.0, after=70.0)
        )
        report, sig = self.approve(self.conn, b)
        with self.conn.cursor() as c:
            c.execute(
                "CREATE TRIGGER issue26_synthetic_block BEFORE UPDATE ON archive "
                "FOR EACH ROW BEGIN IF NEW.outHumidity = 70.0 "
                "THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='synthetic abort'; "
                "END IF; END"
            )
        try:
            with self.assertRaises(self.pymysql.MySQLError):
                apply_approved_batch(
                    self.conn, b, report, sig, approval_key=KEY_MATERIAL, now=NOW
                )
            self.assertEqual(self.value(), 1)
            self.assertEqual(self.value(1540000300, "outHumidity"), 55)
            self.assertEqual(self.count("issue26_batch_events"), 0)
            self.assertEqual(self.count("issue26_field_events"), 0)
        finally:
            with self.conn.cursor() as c:
                c.execute("DROP TRIGGER IF EXISTS issue26_synthetic_block")

    def test_concurrent_competing_batches_one_wins(self):
        a = self.batch(op(after=2.5), name="concurrent-a")
        b = self.batch(op(after=3.5), name="concurrent-b")
        report_a, signature_a = self.approve(self.conn, a)
        report_b, signature_b = self.approve(self.conn, b)
        start = threading.Barrier(2)
        def work(batch, report, sig):
            connection = self.connect()
            try:
                start.wait(timeout=10)
                try:
                    apply_approved_batch(connection, batch, report, sig,
                                         approval_key=KEY_MATERIAL, now=NOW)
                    return "applied"
                except (PreflightError, self.pymysql.MySQLError):
                    return "refused"
            finally:
                connection.close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(work, a, report_a, signature_a),
                       pool.submit(work, b, report_b, signature_b)]
            results = [x.result(timeout=30) for x in futures]
        self.assertEqual(sorted(results), ["applied", "refused"])
        self.assertEqual(self.count("issue26_batch_events"), 1)
        self.assertIn(self.value(), [2.5, 3.5])

    def test_protected_2021_and_q1_2018_rejected_at_manifest(self):
        for timestamp, variable in [(1625100000, "rain"), (1517000000, "outTemp")]:
            with self.assertRaisesRegex(PreflightError, "protected"):
                op(timestamp=timestamp, variable=variable)

    def test_rollback_requires_explicit_phrase(self):
        b = self.batch(op())
        report, sig = self.approve(self.conn, b)
        apply_approved_batch(self.conn, b, report, sig, approval_key=KEY_MATERIAL, now=NOW)
        with self.assertRaisesRegex(PreflightError, "confirmation"):
            rollback_approved_batch(self.conn, b, report, sig,
                                    approval_key=KEY_MATERIAL,
                                    entered_rollback_challenge="", now=NOW)
        self.assertEqual(self.value(), 2.5)


if __name__ == "__main__":
    unittest.main()
