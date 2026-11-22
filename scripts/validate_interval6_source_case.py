#!/usr/bin/env python3
"""Validate the bounded three-row archive concordance case for interval=6."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "reports/2026-11-13-interval6-case-2019.csv"
with path.open(newline="") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 3
left, middle, right = rows
assert [int(r["dateTime_utc_epoch"]) for r in rows] == [1551328500, 1551328800, 1551329100]
assert [int(r["target_interval_min"]) for r in rows] == [5, 6, 5]
assert float(middle["target_outTemp"]) == -2.0
assert middle["production_interval_min"] == middle["gw1000_interval_min"] == "6"
assert middle["production_outTemp"] == middle["gw1000_outTemp"] == "-2"
assert not middle["old_interval_min"] and not middle["wh_interval_min"] and not middle["old_production_interval_min"]
assert all(int(r["outTemp_history_events"]) == 0 for r in rows)
assert left["target_outTemp"] == left["old_outTemp"] == left["wh_outTemp"] == left["production_outTemp"] == left["gw1000_outTemp"] == left["old_production_outTemp"]
assert right["target_outTemp"] == right["old_outTemp"] == right["wh_outTemp"] == right["production_outTemp"] == right["gw1000_outTemp"] == right["old_production_outTemp"]
print("PASS: exact source row at interval=6; adjacent 5-minute rows reconcile across archives")
