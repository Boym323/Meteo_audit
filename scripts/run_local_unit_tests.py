#!/usr/bin/env python3
"""Run all offline unit tests and write a compact machine-readable summary."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
summary = {
    "scope": "local unit tests; no production/archive writes",
    "tests_run": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "status": "passed" if result.wasSuccessful() else "failed",
}
output = ROOT / "reports/2026-11-13-local-unit-test-suite.json"
output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"summary={output.relative_to(ROOT)} status={summary['status']} tests={result.testsRun}")
raise SystemExit(0 if result.wasSuccessful() else 1)
