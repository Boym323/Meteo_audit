"""Offline socket guard tests; never connects or changes a live server."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import stat
import unittest
from unittest.mock import patch

from meteo_audit.approval_dryrun import PreflightError

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "issue26_db_provision.py"
spec = importlib.util.spec_from_file_location("issue26_local_socket", SCRIPT)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class LocalRootSocketGuardTests(unittest.TestCase):
    def test_refuses_non_root_and_unexpected_path(self):
        with patch.object(cli.os, "geteuid", return_value=1000):
            with self.assertRaisesRegex(PreflightError, "root"):
                cli.check_local_root_socket("/run/mysqld/mysqld.sock")
        with patch.object(cli.os, "geteuid", return_value=0):
            with self.assertRaisesRegex(PreflightError, "exact"):
                cli.check_local_root_socket("/tmp/forwarded.sock")

    def test_requires_actual_unix_socket_not_regular_file(self):
        with patch.object(cli.os, "geteuid", return_value=0):
            with patch.object(cli.Path, "is_symlink", return_value=False):
                with patch.object(cli.Path, "stat",
                                  return_value=SimpleNamespace(st_mode=stat.S_IFREG | 0o600)):
                    with self.assertRaisesRegex(PreflightError, "not a socket"):
                        cli.check_local_root_socket("/run/mysqld/mysqld.sock")

    def test_accepts_existing_local_socket_and_denies_symlink(self):
        with patch.object(cli.os, "geteuid", return_value=0):
            with patch.object(cli.Path, "is_symlink", return_value=False):
                with patch.object(cli.Path, "stat",
                                  return_value=SimpleNamespace(st_mode=stat.S_IFSOCK | 0o660)):
                    self.assertEqual(
                        str(cli.check_local_root_socket("/run/mysqld/mysqld.sock")),
                        "/run/mysqld/mysqld.sock",
                    )
            with patch.object(cli.Path, "is_symlink", return_value=True):
                with self.assertRaisesRegex(PreflightError, "expected exact"):
                    cli.check_local_root_socket("/run/mysqld/mysqld.sock")


if __name__ == "__main__":
    unittest.main()
