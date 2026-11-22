#!/usr/bin/env python3
"""Validate the aggregate 2013 counter-delta checkpoint."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with (ROOT / "reports/2026-11-13-rain-2013-counter-epoch.csv").open(
    encoding="utf-8", newline=""
) as f:
    rows = list(csv.DictReader(f))

assert [int(r["utc_month"]) for r in rows] == list(range(1, 13))
number = lambda key: [int(r[key]) for r in rows]
assert sum(number("source_rows")) == 95_495
assert sum(number("positive_source_deltas")) == 1_400
assert sum(number("exact_positive_matches")) == 1_139
assert sum(number("source_positive_recon_zero")) == 0
assert sum(number("source_positive_recon_null")) == 2
assert sum(number("exact_positive_matches")[:3]) == 0
assert sum(number("exact_positive_matches")[4:9]) == 844
assert sum(number("exact_positive_matches")[9:]) == 292
assert sum(number("recon_positive_source_zero_or_unknown")[:3]) == 57
assert all(int(rows[m]["exact_positive_matches"]) == int(rows[m]["both_positive"])
           for m in range(4, 12))
print("PASS: UTC monthly coverage, counter-step totals, mismatch epochs, and positive matches")
