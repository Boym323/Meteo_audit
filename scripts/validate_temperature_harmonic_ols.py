#!/usr/bin/env python3
"""Validate aggregated outputs from the LuhaMet harmonic OLS holdout."""
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
train_path = ROOT / "reports/2026-11-13-temperature-luhamet-harmonic-ols-training-sufficient-stats.csv"
hold_path = ROOT / "reports/2026-11-13-temperature-luhamet-harmonic-ols-holdout.csv"
with train_path.open(newline="") as f:
    train = {r["stat"]: float(r["value"]) for r in csv.DictReader(f)}
with hold_path.open(newline="") as f:
    rows = list(csv.DictReader(f))
assert int(train["pairs_base"]) == 235135
assert int(train["flagged_zero_hot_base"]) == 140
assert int(train["pairs_sensitivity"]) == 234995
assert len(rows) == 6
assert sum(int(r["n"]) for r in rows) == 192235
assert sum(int(r["n"]) for r in rows if r["sensitivity_group"] == "zero_hot_flag") == 959
sumstats = {}
for key in ("n", "m0_abs", "m0_sq", "m0_err", "reg_abs", "reg_sq", "reg_err"):
    sumstats[key] = sum(float(r[key]) for r in rows)
n = sumstats["n"]
metrics = {
    "m0_mae": sumstats["m0_abs"] / n,
    "m0_rmse": math.sqrt(sumstats["m0_sq"] / n),
    "reg_mae": sumstats["reg_abs"] / n,
    "reg_rmse": math.sqrt(sumstats["reg_sq"] / n),
}
assert abs(metrics["m0_mae"] - 1.4864610674) < 1e-8
assert abs(metrics["m0_rmse"] - 2.8520308236) < 1e-8
assert abs(metrics["reg_mae"] - 1.5890313782) < 1e-8
assert abs(metrics["reg_rmse"] - 2.7565263579) < 1e-8
print(f"PASS: train={int(train['pairs_base'])}, holdout={int(n)}, metrics={metrics}")
