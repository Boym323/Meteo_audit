#!/usr/bin/env python3
"""Validate the 2026-11-13 02:15Z production-tail snapshot artifacts."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "reports/2026-11-13-production-reconstruction-lag-0215.csv"
with path.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream))
summary = [row for row in rows if row["record_type"] == "summary"]
gaps = [row for row in rows if row["record_type"] == "gap"]
assert len(summary) == 1 and len(gaps) == 3
s = summary[0]
assert (int(s["rows"]), int(s["first_epoch"]), int(s["last_epoch"])) == (4162, 1793286900, 1794536100)
assert (int(s["interval_minutes"]), int(s["usUnits"])) == (5, 16)
assert all(int(s[name]) == 0 for name in ("outTemp_null", "outHumidity_null", "rain_null", "rainRate_null"))
assert (int(s["exact_interval_steps"]), int(s["long_steps"]), int(s["short_steps"])) == (4159, 3, 0)
assert all(int(row["delta_seconds"]) == 600 and int(row["conditional_missing_5m_slots"]) == 1 for row in gaps)
assert [int(row["current_epoch"]) for row in gaps] == [1793289900, 1793718000, 1794141300]
print("PASS: production tail counts, interval/unit, core NULLs, and three 10-minute gaps reconcile")
