"""Direct issue #26 CLI invocations must load the src package, not its helper."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    "issue26_operator.py",
    "issue26_db_readonly_review.py",
    "issue26_approval_review.py",
)


class Issue26CliImportTests(unittest.TestCase):
    def test_each_cli_help_runs_without_pythonpath(self):
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        for script in SCRIPTS:
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / script), "--help"],
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
