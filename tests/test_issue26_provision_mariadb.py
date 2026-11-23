"""Ephemeral SQL tests of one-server issue26 provisioning and restricted grants."""
from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
import importlib.util
import os
import tempfile
import unittest
from unittest.mock import patch

from meteo_audit.approval_dryrun import PreflightError
from meteo_audit.issue26_audit_ddl_guard import verify_audit_ddl

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "issue26_db_provision.py"
spec = importlib.util.spec_from_file_location("issue26_db_provision", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DbProvisioningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ISSUE26_CI_MYSQL") != "1":
            raise unittest.SkipTest("Requires ephemeral CI MariaDB only")
        import pymysql
        cls.pymysql = pymysql
        cls.conn = pymysql.connect(host="127.0.0.1",port=3306,user="root",
                                   password="ci",database="loucka_reconstruction",
                                   autocommit=True)
        with cls.conn.cursor() as cur:
            cur.execute("SELECT @@hostname, @@server_id")
            cls.actual_host, cls.actual_sid = cur.fetchone()
            cur.execute(
                "SELECT SUBSTRING_INDEX(HOST,':',1) "
                "FROM information_schema.PROCESSLIST WHERE ID=CONNECTION_ID()"
            )
            cls.remote_seen_host = cur.fetchone()[0]

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setup_db(self):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM reconstruction_changes")
            cur.execute("DELETE FROM archive")
            cur.execute(
                "INSERT INTO archive (dateTime,rain,outTemp,outHumidity) "
                "VALUES (1625097900,4.2567,NULL,NULL),"
                "(1540000000,NULL,1.0,40.0)"
            )
            self.conn.commit()

    def patched_source(self):
        contexts = ExitStack()
        contexts.enter_context(patch.object(module, "FIXED_SERVER", self.actual_host))
        contexts.enter_context(patch.object(module, "FIXED_SERVER_ID", self.actual_sid))
        contexts.enter_context(patch.object(module, "ARCHIVE_FIELDS",
                                            frozenset({"dateTime","rain","outTemp","outHumidity"})))
        contexts.enter_context(patch.object(module, "EXPECTED_ARCHIVE_COLUMNS", 4))
        contexts.enter_context(patch.object(module, "VALUE_FIELDS",
                                            frozenset({"rain","outTemp","outHumidity"})))
        return contexts

    def test_provision_exact_schema_and_restricted_account(self):
        self.setup_db()
        with self.patched_source(), tempfile.TemporaryDirectory() as temp:
            private = Path(temp) / "new-owner-only"
            before = module.install_on_existing(
                self.conn, client_ipv4=self.remote_seen_host,
                client_address="127.0.0.1", output_dir=private,
                execute=False, confirmation=None,
            )
            self.assertEqual(before["status"], "DRY_RUN_NOT_INSTALLED_NO_DB_WRITES")
            self.assertFalse(private.exists())
            self.assertEqual(before["audit"]["status"], "NOT_INSTALLED")
            with self.assertRaisesRegex(PreflightError, "confirmation"):
                module.install_on_existing(
                    self.conn, client_ipv4=self.remote_seen_host,
                    client_address="127.0.0.1", output_dir=private,
                    execute=True, confirmation="WRONG",
                )
            self.assertFalse(private.exists())
            applied = module.install_on_existing(
                self.conn, client_ipv4=self.remote_seen_host,
                client_address="127.0.0.1", output_dir=private,
                execute=True, confirmation=module.EXACT_CONFIRM,
            )
            self.assertEqual(applied["status"], "DDL_AND_ROLE_CREATED_NO_ARCHIVE_CHANGES")
            self.assertEqual(applied["audit"]["status"], "DDL_VERIFIED")
            self.assertEqual(private.stat().st_mode & 0o777, 0o700)
            file = private / "writer.cnf"
            self.assertEqual(file.stat().st_mode & 0o777, 0o600)
            with self.conn.cursor() as cur:
                self.assertEqual(verify_audit_ddl(cur)["status"], "DDL_VERIFIED")
                cur.execute("SELECT outTemp FROM archive WHERE dateTime=1540000000")
                self.assertEqual(cur.fetchone()[0], 1.0)
                cur.execute("SELECT COUNT(*) FROM issue26_batch_events")
                self.assertEqual(cur.fetchone()[0], 0)
            # Prove that permissions are narrow on a real CI MariaDB account.
            limited = self.pymysql.connect(
                read_default_file=str(file), read_default_group="client",
                autocommit=True,
            )
            try:
                with limited.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM loucka_reconstruction.archive")
                    self.assertEqual(cur.fetchone()[0], 2)
                    with self.assertRaises(self.pymysql.MySQLError):
                        cur.execute("DELETE FROM loucka_reconstruction.issue26_batch_events")
                    with self.assertRaises(self.pymysql.MySQLError):
                        cur.execute("UPDATE loucka_reconstruction.issue26_batch_events "
                                    "SET approver='bad'")
                    with self.assertRaises(self.pymysql.MySQLError):
                        cur.execute("UPDATE loucka_reconstruction.archive "
                                    "SET dateTime=999 WHERE dateTime=1540000000")
                    with self.assertRaises(self.pymysql.MySQLError):
                        cur.execute("DROP TABLE loucka_reconstruction.issue26_field_events")
                # Assert the actual signed CAS writer can run using only
                # these narrowly scoped grants, not a privileged root user.
                from meteo_audit.approval_dryrun import CandidateBatch, FieldCorrection
                from meteo_audit.approval_gate import challenge_for, sign_exact_batch
                from meteo_audit.issue26_transaction import sql_preflight, apply_approved_batch
                correction = FieldCorrection(
                    1540000000, "outTemp", 1.0, 2.5,
                    "raw:fixture", "unit:fixture", "rule:ci", "HIGH", "MEDIUM",
                )
                batch = CandidateBatch("ci-restricted-user", (correction,))
                review = sql_preflight(limited, batch)
                signed = sign_exact_batch(
                    batch, review, approver="owner:ci-only",
                    entered_challenge=challenge_for(batch, review),
                    secret_key=bytes(range(32)), now=1795430000,
                )
                result = apply_approved_batch(
                    limited, batch, review, signed,
                    approval_key=bytes(range(32)), now=1795430001,
                )
                self.assertTrue(result.committed)
                with limited.cursor() as cur:
                    cur.execute(
                        "SELECT outTemp FROM loucka_reconstruction.archive "
                        "WHERE dateTime=1540000000"
                    )
                    self.assertEqual(cur.fetchone()[0], 2.5)
            finally:
                limited.close()
            with self.assertRaisesRegex(PreflightError, "already installed"):
                module.install_on_existing(
                    self.conn, client_ipv4=self.remote_seen_host,
                    client_address="127.0.0.1", output_dir=private,
                    execute=True, confirmation=module.EXACT_CONFIRM,
                )


if __name__ == "__main__":
    unittest.main()
