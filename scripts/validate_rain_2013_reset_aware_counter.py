#!/usr/bin/env python3
"""Validate aggregate 2013 UTC-reset counter diagnostic."""
import csv
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "reports/2026-11-13-rain-2013-reset-aware-counter.csv"
with path.open(encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
assert [int(r["utc_month"]) for r in rows] == list(range(1, 13))
n = lambda key: [int(r[key]) for r in rows]
assert sum(n("negative_300s_steps")) == 177
assert sum(n("exact_utc_midnight_resets")) == 137
assert sum(n("positive_increments")) == 1_430
assert sum(n("exact_positive_matches")) == 1_139
assert sum(n("positive_increment_recon_zero")) == 30
assert sum(n("positive_increment_recon_null")) == 2
assert sum(n("exact_positive_matches")[:3]) == 0
assert sum(n("exact_positive_matches")[4:]) == 1_136
assert sum(n("exact_utc_midnight_resets")[4:]) == 104
print("PASS: reset cadence, UTC monthly totals, reset-aware positive cases and match epochs")
