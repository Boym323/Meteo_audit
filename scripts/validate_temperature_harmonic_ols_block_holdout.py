#!/usr/bin/env python3
"""Validate aggregate blocked-holdout and 0.1 C error histogram checkpoints."""
import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
block_file = ROOT / "reports/2026-11-13-temperature-luhamet-harmonic-ols-blocks.csv"
hist_file = ROOT / "reports/2026-11-13-temperature-luhamet-harmonic-ols-error-histogram.csv"
with block_file.open(newline="") as f:
    blocks = list(csv.DictReader(f))
with hist_file.open(newline="") as f:
    hist = list(csv.DictReader(f))
assert len(blocks) == 861
for kind, expected_blocks in (("1d", 729), ("7d", 106), ("30d", 26)):
    rows = [r for r in blocks if r["block_type"] == kind]
    assert len(rows) == expected_blocks
    assert sum(int(r["target_n"]) for r in rows) == 202723
    assert sum(int(r["eligible_reference_n"]) for r in rows) == 192235
    assert sum(int(r["zero_hot_n"]) for r in rows) == 959
    assert math.isclose(
        sum(float(r["eligible_reference_n"]) for r in rows)
        / sum(float(r["target_n"]) for r in rows),
        0.9482643804600366,
        abs_tol=1e-12,
    )
assert sum(int(r["eligible_reference_n"]) == 0 for r in blocks if r["block_type"] == "1d") == 30
assert sum(int(r["eligible_reference_n"]) == 0 for r in blocks if r["block_type"] == "7d") == 2
assert sum(int(r["eligible_reference_n"]) == 0 for r in blocks if r["block_type"] == "30d") == 0

totals = defaultdict(int)
bins = defaultdict(dict)
for r in hist:
    key = (r["year"], r["group"], r["method"])
    bucket = int(r["abs_error_decic_bucket"])
    count = int(r["count"])
    totals[key] += count
    bins[key][bucket] = count
expected_n = {
    "all": 192235,
    "nonflag": 191276,
    "freeze_nonflag": 22406,
    "flagged": 959,
}
expected_year_group_n = {
    ("2019", "all"): 94395,
    ("2020", "all"): 97840,
    ("2019", "nonflag"): 93780,
    ("2020", "nonflag"): 97496,
    ("2019", "freeze_nonflag"): 10372,
    ("2020", "freeze_nonflag"): 12034,
    ("2019", "flagged"): 615,
    ("2020", "flagged"): 344,
}
for year in ("2019", "2020"):
    for group, expected in expected_n.items():
        for method in ("direct", "ols"):
            assert totals[(year, group, method)] == expected_year_group_n[(year, group)]
            assert sum(bins[(year, group, "direct")].values()) == sum(
                bins[(year, group, "ols")].values()
            )
for group, expected in expected_n.items():
    for method in ("direct", "ols"):
        count = sum(totals[(y, group, method)] for y in ("2019", "2020"))
        assert count == expected


def quantile_bin(group, method, p):
    merged = defaultdict(int)
    for year in ("2019", "2020"):
        for bucket, count in bins[(year, group, method)].items():
            merged[bucket] += count
    rank = math.ceil(p * sum(merged.values()))
    seen = 0
    for bucket in sorted(merged):
        seen += merged[bucket]
        if seen >= rank:
            return bucket
    raise AssertionError("quantile rank not found")


assert quantile_bin("all", "direct", 0.90) == 23
assert quantile_bin("all", "ols", 0.90) == 27
assert quantile_bin("nonflag", "direct", 0.95) == 34
assert quantile_bin("nonflag", "ols", 0.95) == 35
print("PASS: 861 blocks; 202723 target slots; 192235 exact reference pairs; histogram counts and quantile bins reconcile")
