"""Smoke tests for the local run wrapper; no database connection is used."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "run_audit_checkpoint.py"


class AuditRunCheckpointTests(unittest.TestCase):
    def test_records_successful_run_and_file_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            config = base / "config.json"
            output = base / "result.txt"
            run_root = base / "runs"
            config.write_text(json.dumps({"scope": {"audit": "unit-test"}}), encoding="utf-8")
            command = [
                sys.executable, str(WRAPPER), "--config", str(config),
                "--source", str(WRAPPER), "--output", str(output),
                "--run-root", str(run_root), "--", sys.executable, "-c",
                "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ok')",
                str(output),
            ]
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
            manifest_path = next(run_root.glob("*/manifest.json"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertEqual(manifest["status"], "succeeded")
            self.assertEqual(manifest["exit_code"], 0)
            self.assertEqual(manifest["scope"]["audit"], "unit-test")
            self.assertEqual(len(manifest["sources"]), 1)
            self.assertEqual(len(manifest["outputs"]), 1)
            self.assertTrue(manifest["log"]["sha256"])
            self.assertTrue(manifest["analysis_code"]["sha256"])

    def test_failed_command_is_checkpointed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            config = base / "config.json"
            config.write_text("{}", encoding="utf-8")
            command = [
                sys.executable, str(WRAPPER), "--config", str(config),
                "--run-root", str(base / "runs"), "--", sys.executable, "-c",
                "raise SystemExit(7)",
            ]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 7)
            manifest = json.loads(next((base / "runs").glob("*/manifest.json")).read_text())
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["exit_code"], 7)


if __name__ == "__main__":
    unittest.main()
