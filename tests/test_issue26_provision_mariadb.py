"""Synthetic MariaDB regression: #26 must NEVER create another account.

The retired installer remains strictly read-only even with --execute/--confirm.
The CI fixture may simulate already-installed audit tables, but no user/GRANT
changes are performed by the installer. No production connections.
"""
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


class ExistingAccountsOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ISSUE26_CI_MYSQL") != "1":
            raise unittest.SkipTest("Ephemeral CI MariaDB only")
        import pymysql
        cls.conn = pymysql.connect(
            host="127.0.0.1", port=3306, user="root",
            password="ci", database="loucka_reconstruction", autocommit=True
        )
        with cls.conn.cursor() as c:
            c.execute("SELECT @@hostname, @@server_id")
            cls.host, cls.sid = c.fetchone()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def patched_host(self):
        e = ExitStack()
        e.enter_context(patch.object(module, "FIXED_SERVER", self.host))
        e.enter_context(patch.object(module, "FIXED_SERVER_ID", self.sid))
        e.enter_context(patch.object(
            module, "ARCHIVE_FIELDS",
            frozenset({"dateTime","rain","outTemp","outHumidity"}),
        ))
        e.enter_context(patch.object(module, "EXPECTED_ARCHIVE_COLUMNS", 4))
        return e

    def reset(self):
        with self.conn.cursor() as c:
            c.execute("DELETE FROM reconstruction_changes")
            c.execute("DELETE FROM archive")
            c.execute(
                "INSERT INTO archive(dateTime,rain,outTemp,outHumidity) VALUES "
                "(1625097900,4.2567,NULL,NULL),(1540000000,NULL,1.0,40.0)"
            )

    def count_new_accounts(self):
        with self.conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM mysql.user WHERE User='meteo_issue26_writer'")
            return c.fetchone()[0]

    def test_inspection_only_and_execute_never_creates_account_or_ddl(self):
        self.reset()
        with self.patched_host(), tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/"forbidden"
            status = module.install_on_existing(
                self.conn, client_ipv4="192.168.0.131",
                client_address="192.168.1.52", output_dir=output,
                execute=False, confirmation=None,
            )
            self.assertEqual(status["status"], "AUDIT_DDL_MISSING_READ_ONLY")
            self.assertEqual(status["new_db_accounts"], 0)
            self.assertEqual(status["db_writes"], 0)
            self.assertTrue(status["existing_accounts_only"])
            self.assertFalse(output.exists())
            for phrase in (None, "WRONG", module.EXACT_CONFIRM):
                with self.assertRaisesRegex(PreflightError, "NO NEW SQL ACCOUNTS"):
                    module.install_on_existing(
                        self.conn, client_ipv4="192.168.0.131",
                        client_address="192.168.1.52", output_dir=output,
                        execute=True, confirmation=phrase,
                    )
            self.assertEqual(self.count_new_accounts(), 0)
            self.assertFalse(output.exists())
            with self.conn.cursor() as c:
                c.execute(
                    "SELECT COUNT(*) FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA='loucka_reconstruction' "
                    "AND TABLE_NAME IN ('issue26_batch_events','issue26_field_events')"
                )
                self.assertEqual(c.fetchone()[0], 0)

    def test_can_inspect_existing_synthetic_ddl_without_creating_accounts(self):
        self.reset()
        schema_file = Path(__file__).resolve().parents[1] / "sql" / "issue26_transactional_audit_schema.sql"
        with self.conn.cursor() as c:
            for statement in schema_file.read_text(encoding="utf-8").split(";"):
                if statement.strip():
                    c.execute(statement)
            self.assertEqual(verify_audit_ddl(c)["status"], "DDL_VERIFIED")
        with self.patched_host():
            result = module.install_on_existing(
                self.conn, client_ipv4="192.168.0.131",
                client_address="192.168.1.52",
                output_dir=Path("/does-not-matter"), execute=False,
                confirmation=None,
            )
        self.assertEqual(result["status"], "EXISTING_AUDIT_DDL_VERIFIED_NO_DB_WRITES")
        self.assertEqual(result["new_db_accounts"], 0)
        self.assertEqual(self.count_new_accounts(), 0)
        with self.conn.cursor() as c:
            c.execute("SELECT COUNT(*) FROM issue26_batch_events")
            self.assertEqual(c.fetchone()[0], 0)
            c.execute("SELECT COUNT(*) FROM issue26_field_events")
            self.assertEqual(c.fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
