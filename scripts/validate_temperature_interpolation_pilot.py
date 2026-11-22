#!/usr/bin/env python3
"""Validate the aggregate one-week synthetic temperature gap experiment."""
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "reports/2026-11-13-temperature-short-gap-interpolation-holdout-2019-07.csv"
with path.open(newline="") as f:
    rows = {int(r["block_hours"]): r for r in csv.DictReader(f)}
assert set(rows) == {1, 6, 24}
expected = {1: 168, 6: 28, 24: 7}
for hours, count in expected.items():
    row = rows[hours]
    assert int(row["complete_blocks"]) == count
    assert int(row["scored_points"]) == 2016
    assert int(row["matched_reference_points"]) == 2016
    assert math.isclose(float(row["direct_reference_MAE"]), 1.03501984127, abs_tol=1e-7)
    assert math.isclose(float(row["harmonic_OLS_MAE"]), 1.49000496561, abs_tol=1e-7)
assert float(rows[1]["interpolation_MAE"]) < float(rows[6]["interpolation_MAE"])
assert float(rows[6]["interpolation_MAE"]) < float(rows[24]["interpolation_MAE"])
assert float(rows[24]["interpolation_RMSE"]) > 5
print("PASS: 168/28/7 complete blocks; 2016 points each; interpolation error increases with mask length")
