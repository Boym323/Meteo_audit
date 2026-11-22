#!/usr/bin/env python3
"""Validate boundary bridge classification for yearly cadence segments."""
import csv
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with (root / "reports/2026-11-13-cadence-year-boundary-bridges.csv").open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 17
assert [int(r["utc_year"]) for r in rows] == list(range(2010, 2027))
assert all(int(r[k]) in (0, 1) for r in rows for k in (
    "prev_year_edge_regular", "cross_year_edge_regular", "next_edge_regular", "annual_runs_joined"))
assert all(int(r["annual_runs_joined"]) == (int(r["prev_year_edge_regular"]) and int(r["cross_year_edge_regular"])) for r in rows)
assert sum(int(r["annual_runs_joined"]) for r in rows) == 13
assert [int(r["utc_year"]) for r in rows if int(r["cross_year_edge_regular"]) == 0] == [2012, 2014, 2017, 2022]
annual_runs = sum(int(r["run_count"]) for r in csv.DictReader(
    (root / "reports/2026-11-12-candidate-cadence-runs-by-year.csv").open(newline="", encoding="utf-8")))
assert annual_runs == 7299
assert annual_runs - sum(int(r["annual_runs_joined"]) for r in rows) == 7286
print("PASS: 17 boundaries; 13 joins; 7,299 annual fragments -> 7,286 candidate continuous runs")
