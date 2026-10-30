import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from meteo_audit.db import ReadOnlyQueryError, _validate_select, query, quote_database


class QueryGuardTests(unittest.TestCase):
    def test_writes_and_side_effecting_selects_are_rejected(self):
        statements = (
            "UPDATE archive SET rain=0", "DELETE FROM archive",
            "INSERT INTO t VALUES (1)", "DROP TABLE archive",
            "SELECT * FROM t INTO OUTFILE '/tmp/x'", "SELECT * FROM t FOR UPDATE",
            "SELECT SLEEP(1)", "SELECT GET_LOCK('x', 2)", "SELECT @x",
            "SELECT 1 INTO @x", "SELECT 1 /* comment */",
        )
        for statement in statements:
            with self.subTest(statement=statement), self.assertRaises(ReadOnlyQueryError):
                _validate_select(statement)

    def test_multiple_statements_and_terminators_are_rejected(self):
        for statement in ("SELECT 1; SELECT 2", "SELECT 1;", "SELECT 1 -- comment"):
            with self.subTest(statement=statement), self.assertRaises(ReadOnlyQueryError):
                _validate_select(statement)

    def test_schema_names_are_allowlisted_and_quoted(self):
        tick = chr(96)
        self.assertEqual(quote_database("loucka_reconstruction"), tick + "loucka_reconstruction" + tick)
        self.assertEqual(quote_database("pocasi-loucka.eu"), tick + "pocasi-loucka.eu" + tick)
        for schema in ("arbitrary", "loucka_reconstruction; DROP TABLE archive", ""):
            with self.subTest(schema=schema), self.assertRaises(ReadOnlyQueryError):
                quote_database(schema)

    def test_sql_rejects_unallowlisted_qualified_schema(self):
        tick = chr(96)
        _validate_select("SELECT * FROM " + tick + "loucka_reconstruction" + tick + "." + tick + "archive" + tick)
        with self.assertRaises(ReadOnlyQueryError):
            _validate_select("SELECT * FROM " + tick + "arbitrary_schema" + tick + "." + tick + "archive" + tick)

    def test_query_requires_configured_credentials(self):
        with self.assertRaises(RuntimeError):
            query("SELECT 1", env_file="/does/not/exist")

    def test_existing_account_is_accepted_without_renaming_it(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials"
            path.write_text(
                "DB_HOST=localhost\nDB_PORT=3306\n"
                "DB_USER=loucka_audit\nDB_PASSWORD=dummy\n"
            )
            path.chmod(0o600)
            with patch("meteo_audit.db.subprocess.run") as run:
                run.return_value.stdout = "1\n"
                run.return_value.stderr = ""
                run.return_value.returncode = 0
                self.assertEqual(query("SELECT 1", env_file=path), ["1"])
            self.assertTrue(run.called)

    def test_timeout_has_safe_bounds(self):
        for timeout in (0, -1, 601, 1.5):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                query("SELECT 1", timeout=timeout, env_file="/does/not/exist")

    def test_config_permissions_are_checked_without_revealing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials"
            path.write_text("DB_PASSWORD=dummy\n")
            path.chmod(0o644)
            with self.assertRaises(PermissionError):
                query("SELECT 1", env_file=path)

    def test_client_config_is_private_and_removed_after_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "readonly.env"
            path.write_text(
                "DB_HOST=localhost\nDB_PORT=3306\n"
                "DB_USER=loucka_audit\nDB_PASSWORD=dummy\n"
            )
            path.chmod(0o600)
            observed = {}

            def fake_run(args, **kwargs):
                config_arg = next(arg for arg in args if arg.startswith("--defaults-extra-file="))
                config = Path(config_arg.split("=", 1)[1])
                observed["config"] = config
                observed["mode"] = stat.S_IMODE(config.stat().st_mode)
                observed["sql"] = args[-1]
                observed["config_text"] = config.read_text(encoding="utf-8")
                return type("Result", (), {"stdout": "1\n", "stderr": "", "returncode": 0})()

            with patch("meteo_audit.db.subprocess.run", side_effect=fake_run):
                self.assertEqual(query("SELECT 1", env_file=path), ["1"])
            self.assertEqual(observed["mode"], 0o600)
            self.assertIn('user="loucka_audit"', observed["config_text"])
            self.assertIn("SET SESSION TRANSACTION READ ONLY", observed["sql"])
            self.assertIn("START TRANSACTION READ ONLY", observed["sql"])
            self.assertIn("ROLLBACK", observed["sql"])
            self.assertNotIn("secret-value", observed["sql"])
            self.assertFalse(observed["config"].exists())

    def _write_readonly_env(self, directory: str) -> Path:
        path = Path(directory) / "readonly.env"
        path.write_text(
            "DB_HOST=localhost\nDB_PORT=3306\n"
            "DB_USER=loucka_audit\nDB_PASSWORD=dummy\n"
        )
        path.chmod(0o600)
        return path

    def test_client_timeout_is_reported_and_temporary_config_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            env = self._write_readonly_env(directory)
            config_path = {}

            def fake_run(args, **kwargs):
                arg = next(item for item in args if item.startswith("--defaults-extra-file="))
                config_path["path"] = Path(arg.split("=", 1)[1])
                raise subprocess.TimeoutExpired("mariadb", 2)

            with patch("meteo_audit.db.subprocess.run", side_effect=fake_run):
                with self.assertRaisesRegex(TimeoutError, "exceeded 2 seconds"):
                    query("SELECT 1", env_file=env, timeout=2)
            self.assertFalse(config_path["path"].exists())

    def test_database_errors_do_not_echo_the_query_and_remove_config(self):
        with tempfile.TemporaryDirectory() as directory:
            env = self._write_readonly_env(directory)
            config_path = {}

            def fake_run(args, **kwargs):
                arg = next(item for item in args if item.startswith("--defaults-extra-file="))
                config_path["path"] = Path(arg.split("=", 1)[1])
                return type("Result", (), {
                    "stdout": "", "stderr": "ERROR 1142: SELECT denied", "returncode": 1,
                })()

            with patch("meteo_audit.db.subprocess.run", side_effect=fake_run):
                with self.assertRaises(RuntimeError) as raised:
                    query("SELECT 1", env_file=env)
            self.assertNotIn("SELECT 1", str(raised.exception))
            self.assertFalse(config_path["path"].exists())


if __name__ == "__main__":
    unittest.main()
