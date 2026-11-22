#!/usr/bin/env python3
"""Run only the local synthetic correction simulator tests and save a summary."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

suite = unittest.defaultTestLoader.discover(
    str(ROOT / "tests"), pattern="test_correction_simulation.py"
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
summary = {
    "scope": "synthetic_local_simulation_only_no_database_or_weather_mcp_access",
    "tests_run": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "status": "passed" if result.wasSuccessful() else "failed",
}
output = ROOT / "reports/2026-11-13-local-correction-simulation-tests.json"
output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"summary={output.relative_to(ROOT)} status={summary['status']} tests={result.testsRun}")
raise SystemExit(0 if result.wasSuccessful() else 1)
