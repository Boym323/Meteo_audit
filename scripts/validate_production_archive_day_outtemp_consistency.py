#!/usr/bin/env python3
"""Reconcile the production outTemp daily-summary audit CSVs."""
import csv
from pathlib import Path

root = Path(__file__).resolve().parents[1]

def read(name):
    with (root / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

annual = read("reports/2026-11-13-production-outtemp-daily-summary-consistency-annual.csv")
monthly = read("reports/2026-11-13-production-outtemp-daily-summary-consistency-2026-monthly.csv")
control = read("reports/2026-11-13-production-outtemp-daily-summary-consistency-2025-control.csv")
assert len(annual) == 18 and [int(r["year"]) for r in annual] == list(range(2009, 2027))
assert len(monthly) == 11 and [r["local_month"] for r in monthly] == [f"2026-{m:02d}" for m in range(1, 12)]
assert all(int(r["no_raw_day"]) == 0 and int(r["count_mismatch_days"]) == 0 for r in annual)
assert all(int(r["sumtime_mismatch_days"]) == 0 for r in annual)
assert all(int(r["min_exact_mismatch_days"]) == 0 and int(r["max_exact_mismatch_days"]) == 0 for r in annual if int(r["year"]) <= 2025)
assert next(r for r in annual if int(r["year"]) == 2021)["scope"] == "diagnostic"
y26 = next(r for r in annual if int(r["year"]) == 2026)
assert (int(y26["summary_days"]), int(y26["min_exact_mismatch_days"]), int(y26["max_exact_mismatch_days"])) == (316, 151, 218)
assert (int(y26["min_diff_over_0_1"]), int(y26["max_diff_over_0_1"])) == (1, 86)
assert abs(float(y26["max_max_diff"]) - 0.38) < 1e-9
assert int(y26["wsum_exact_mismatch_days"]) == 23 and float(y26["max_wsum_diff"]) < 1e-8
assert len(control) == 1 and control[0]["local_year"] == "2025"
assert (int(control[0]["days"]), int(control[0]["min_exact_mismatch"]), int(control[0]["max_exact_mismatch"])) == (363, 0, 0)
assert int(control[0]["mintime_absent_in_archive"]) == int(control[0]["maxtime_absent_in_archive"]) == 0
assert sum(int(r["days"]) for r in monthly) == 316
assert sum(int(r["min_gt_0_1"]) for r in monthly) == 1
assert sum(int(r["max_gt_0_1"]) for r in monthly) == 86
assert all(int(r["max_gt_0_1"]) == 0 for r in monthly[:2])
assert any(int(r["max_gt_0_1"]) > 0 for r in monthly[2:])
assert sum(int(r["mintime_absent_in_archive"]) for r in monthly) == 189
assert sum(int(r["maxtime_absent_in_archive"]) for r in monthly) == 222
print("PASS: 18 years/6,103 complete days; 2025 control and 2026 anomaly reconcile")
