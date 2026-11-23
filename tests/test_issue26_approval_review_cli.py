"""Integration-level tests for the local review/sign/verify CLI (#26)."""
import contextlib
from dataclasses import asdict
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from meteo_audit.approval_dryrun import CandidateBatch, FieldCorrection, preflight
from meteo_audit.approval_gate import challenge_for

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "issue26_approval_review.py"
SPEC = importlib.util.spec_from_file_location("issue26_approval_cli", SCRIPT)
cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cli)


class ApprovalReviewCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.manifest = root / "batch.json"
        self.before = root / "before.json"
        self.key = root / "owner.key"
        self.receipt = root / "approved.json"
        self.batch = CandidateBatch("synthetic-ci-only", (
            FieldCorrection(1540000000, "outTemp", 1.0, 2.5,
                            "raw:fixture", "epoch:fixture", "rule:test",
                            "HIGH", "MEDIUM"),
        ))
        self.manifest.write_text(json.dumps({
            "schema": self.batch.schema, "target": self.batch.target,
            "batch_id": self.batch.batch_id,
            "operations": [asdict(x) for x in self.batch.operations],
        }))
        self.before.write_text(json.dumps([
            {"target_time_utc": 1540000000, "variable": "outTemp", "old": 1.0},
        ]))
        self.key.write_bytes(b"K" * 32)
        os.chmod(self.key, 0o600)

    def run_cli(self, *args, entered=None):
        cmd = [
            "issue26_approval_review.py", *args,
            "--manifest", str(self.manifest),
            "--before-image", str(self.before),
        ]
        output = io.StringIO()
        with patch.object(sys, "argv", cmd), patch("builtins.input", return_value=entered), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = cli.main()
        return result, output.getvalue()

    def test_full_challenge_sign_verify_no_database(self):
        rc, out = self.run_cli("challenge")
        self.assertEqual(rc, 0)
        challenge = json.loads(out)["exact_phrase"]
        args = ["--key-file", str(self.key), "--receipt-file", str(self.receipt)]
        rc, out = self.run_cli("sign", "--operator", "owner:synthetic", *args,
                               entered=challenge)
        self.assertEqual(rc, 0, out)
        self.assertTrue(self.receipt.exists())
        self.assertEqual(self.receipt.stat().st_mode & 0o777, 0o600)
        rc, out = self.run_cli("verify", *args)
        self.assertEqual(rc, 0, out)
        self.assertIn("NOT_APPLIED", out)

    def test_tampered_before_image_or_manifest_rejected(self):
        _, out = self.run_cli("challenge")
        phrase = json.loads(out)["exact_phrase"]
        args = ["--key-file", str(self.key), "--receipt-file", str(self.receipt)]
        self.assertEqual(self.run_cli("sign", "--operator", "owner:synthetic",
                                      *args, entered=phrase)[0], 0)
        self.before.write_text(json.dumps([
            {"target_time_utc":1540000000, "variable":"outTemp", "old": 7.0}
        ]))
        rc, out = self.run_cli("verify", *args)
        self.assertEqual(rc, 2)
        self.assertIn("CAS", out)

    def test_refuses_duplicate_review_rows(self):
        rows = json.loads(self.before.read_text())
        self.before.write_text(json.dumps(rows + rows))
        rc, out = self.run_cli("challenge")
        self.assertEqual(rc, 2)
        self.assertIn("duplicate", out)

    def test_insecure_secret_file_refused(self):
        os.chmod(self.key, 0o644)
        rc, out = self.run_cli("sign", "--operator", "owner:synthetic",
                               "--key-file", str(self.key),
                               "--receipt-file", str(self.receipt), entered="")
        self.assertEqual(rc, 2)
        self.assertIn("0600", out)

    def test_receipt_cannot_be_overwritten(self):
        _, out = self.run_cli("challenge")
        phrase = json.loads(out)["exact_phrase"]
        args = ["--operator", "owner:synthetic",
                "--key-file", str(self.key), "--receipt-file", str(self.receipt)]
        self.assertEqual(self.run_cli("sign", *args, entered=phrase)[0], 0)
        rc, _ = self.run_cli("sign", *args, entered=phrase)
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
