"""Safety regression tests for scripts/isolated_restore_drill.py (#26)."""
import importlib.util
from pathlib import Path
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "isolated_restore_drill.py"
SPEC = importlib.util.spec_from_file_location("restore_drill_26", SCRIPT)
drill = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(drill)


class RestoreDrillTests(unittest.TestCase):
    def test_distinct_hosts_and_server_ids_required(self):
        with patch.object(drill, "instance", side_effect=[
            ("live", "1", "3306", "/var/lib/mysql"),
            ("live", "1", "3306", "/var/lib/mysql"),
        ]):
            with self.assertRaisesRegex(drill.DrillError, "separate instances"):
                drill.separate_instances("a", "b")

    def test_different_hosts_with_same_datadir_string_allowed(self):
        with patch.object(drill, "instance", side_effect=[
            ("source-host", "1", "3306", "/var/lib/mysql"),
            ("restore-host", "102", "3306", "/var/lib/mysql"),
        ]):
            result = drill.separate_instances("a", "b")
            self.assertEqual(result[1][1], "102")

    def test_destination_must_be_clean(self):
        with patch.object(drill, "select", return_value=[["pocasi-loucka.eu"]]):
            with self.assertRaisesRegex(drill.DrillError, "destination already contains"):
                drill.empty_destination("test")

    def test_invariants_lock_protected_rain_and_qc_receipt(self):
        with patch.object(drill, "select", return_value=[["1697334", "113154", "42.568", "60"]]):
            with self.assertRaisesRegex(drill.DrillError, "July 2021"):
                drill.invariants("src")
        with patch.object(drill, "select", return_value=[["1697334", "113154", "42.567", "59"]]):
            with self.assertRaisesRegex(drill.DrillError, "sensor"):
                drill.invariants("src")

    def test_null_checksum_is_not_accepted(self):
        with patch.object(drill, "select", side_effect=[[["1"]], [["x", "NULL"]]]):
            with self.assertRaisesRegex(drill.DrillError, "checksum unsupported"):
                drill.fingerprint("source", ["archive"])

    def test_private_cnf_mode_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "source.cnf"
            p.write_text("[client]\nuser=example\n")
            os.chmod(p, 0o600)
            self.assertEqual(drill.private_file(str(p)), p)
            os.chmod(p, 0o644)
            with self.assertRaisesRegex(drill.DrillError, "private"):
                drill.private_file(str(p))
            os.chmod(p, 0o600)
            link = Path(tmp) / "link.cnf"
            link.symlink_to(p)
            with self.assertRaisesRegex(drill.DrillError, "symlink"):
                drill.private_file(str(link))

    def setup_operator_mocks(self):
        return (patch.object(drill, "private_file", side_effect=lambda x: Path(x)),
                patch.object(drill.shutil, "which", return_value="/usr/bin/true"),
                patch.object(drill, "separate_instances",
                             return_value=(("src", "1", "3306", "/var/lib/mysql"),
                                           ("dst", "2", "3306", "/var/lib/mysql"))),
                patch.object(drill, "empty_destination"),
                patch.object(drill, "inventory", return_value=["archive", "reconstruction_changes"]),
                patch.object(drill, "invariants",
                             return_value={"archive_rows": "1697334", "change_events": "113154",
                                           "july_2021_mm": "42.567", "sensor_null_events": "60"}))

    def test_default_is_readonly_dryrun(self):
        patches = self.setup_operator_mocks()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], \
             patch.object(drill, "dump") as backup, patch.object(drill, "restore") as restore:
            result = drill.drill(SimpleNamespace(source_cnf="/a", destination_cnf="/b",
                                                 execute=False, confirm="", receipt_dir=None))
            self.assertEqual(result["status"], "DRY_RUN_NO_WRITES")
            self.assertEqual(result["db_writes"], 0)
            backup.assert_not_called()
            restore.assert_not_called()

    def test_no_explicit_confirmation_means_no_restore(self):
        patches = self.setup_operator_mocks()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], \
             patch.object(drill, "dump") as backup, patch.object(drill, "restore") as restore:
            with self.assertRaisesRegex(drill.DrillError, "confirmation"):
                drill.drill(SimpleNamespace(source_cnf="/a", destination_cnf="/b",
                                            execute=True, confirm="", receipt_dir="/tmp/not-created"))
            backup.assert_not_called()
            restore.assert_not_called()

    def test_restore_receipt_requires_matching_postimage(self):
        patches = self.setup_operator_mocks()
        fingerprints = [{"archive": {"rows": "3", "extended_checksum": "111"}},
                        {"archive": {"rows": "3", "extended_checksum": "111"}},
                        {"archive": {"rows": "3", "extended_checksum": "222"}}]
        with tempfile.TemporaryDirectory() as tmp, \
             patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], \
             patch.object(drill, "fingerprint", side_effect=fingerprints), \
             patch.object(drill, "dump", side_effect=lambda a, b: b.write_bytes(b"synthetic-fixture")), \
             patch.object(drill, "restore") as restored:
            with self.assertRaisesRegex(drill.DrillError, "checksum mismatch"):
                drill.drill(SimpleNamespace(
                    source_cnf="/a", destination_cnf="/b",
                    execute=True, confirm=drill.CONFIRMATION, receipt_dir=str(Path(tmp) / "drill")
                ))
            restored.assert_called_once()
            self.assertFalse((Path(tmp) / "drill" / "restore-receipt.json").exists())

    def test_successful_mock_receipt_never_grants_cutover(self):
        patches = self.setup_operator_mocks()
        with tempfile.TemporaryDirectory() as tmp, \
             patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], \
             patch.object(drill, "fingerprint", return_value={
                 "archive": {"rows": "3", "extended_checksum": "111"}}), \
             patch.object(drill, "dump", side_effect=lambda a, b: b.write_bytes(b"synthetic-fixture")), \
             patch.object(drill, "restore"):
            result = drill.drill(SimpleNamespace(
                source_cnf="/a", destination_cnf="/b",
                execute=True, confirm=drill.CONFIRMATION, receipt_dir=str(Path(tmp) / "drill")
            ))
            self.assertEqual(result["status"], "PASS_ISOLATED_RESTORE_DRILL_ONLY")
            self.assertFalse(result["production_cutover_authorized"])
            self.assertFalse(result["correction_batch_approved"])
            self.assertTrue((Path(tmp) / "drill" / "restore-receipt.json").exists())


if __name__ == "__main__":
    unittest.main()
