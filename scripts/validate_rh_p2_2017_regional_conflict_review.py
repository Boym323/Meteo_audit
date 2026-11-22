#!/usr/bin/env python3
"""Deterministic validation for the 2017 source-vs-regional RH review."""
import json
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "data/rh_p2_2017_regional_conflict_review.json").read_text())
rows = data["rows"]
assert data["schema"] == "rh-p2-2017-regional-conflict-review-v1"
assert data["recorded_at_utc"] == "2026-11-13T20:37:25Z"
assert data["query_execution_utc"] is None
assert len(rows) == 24
assert len({r["dateTime"] for r in rows}) == 24
assert all(1483228800 <= r["dateTime"] < 1514764800 for r in rows)
assert all(r["source_rh"] is not None and r["luhamet_rh"] is not None for r in rows)
assert all(r["rh_difference_pp"] > 35 for r in rows)
assert all(r["source_temp"] == r["target_temp"] for r in rows)
assert all(r["rh_events"] == 0 for r in rows)
assert sum(r["all_events"] > 0 for r in rows) == 1
assert [r["dateTime"] for r in rows if r["all_events"] > 0] == [1509272700]
assert data["other_variable_events"] == [{
    "id": 19162, "target_time": 1509272700, "variable": "rainRate",
    "old_value": 0.0, "new_value": 0.07999999991838411, "state": "applied",
    "batch_key": "rainrate-restore-2009-2025-v1",
    "source_database": "pocasi-loucka.eu_GW1000", "source_time": 1509272700,
}]
assert all(all(r[k] for k in ("euold_row", "eu_row", "gw_row", "old_row", "wh_row")) for r in rows)
assert all(r["source_rain"] == r["wh_rain"] and r["source_rainRate"] == r["wh_rainRate"]
           and r["source_wind"] == r["wh_wind"] for r in rows)
within = sum(min(r["prev_rh"], r["next_rh"]) <= r["source_rh"] <= max(r["prev_rh"], r["next_rh"]) for r in rows)
assert within == 8
assert sum(r["source_rh"] == r["prev_rh"] == r["next_rh"] for r in rows) == 3
sql = (ROOT / "sql/readonly/rh_p2_2017_regional_conflict_review.sql").read_text()
for token in ("1483228800", "1514764800", ">35", "r.outTemp=o.outTemp", "variable='outHumidity'"):
    assert token in sql, token
prior = json.loads((ROOT / "data/rh_p2_2017_exact_bracket_review.json").read_text())
prior_times = {r["dateTime"] for r in prior["candidates"]}
new_times = {r["dateTime"] for r in rows} - prior_times
assert len(new_times) == 16
assert all(not (min(r["prev_rh"], r["next_rh"]) <= r["source_rh"] <= max(r["prev_rh"], r["next_rh"]))
           for r in rows if r["dateTime"] in new_times)
assert (ROOT / "reports/2026-11-13-rh-p2-2017-regional-conflict-review.md").is_file()
with (ROOT / "data/rh_p2_2017_regional_conflict_review.csv").open(newline="", encoding="utf-8") as f:
    csv_rows = list(csv.DictReader(f))
assert len(csv_rows) == 24
assert {int(r["dateTime"]) for r in csv_rows} == {r["dateTime"] for r in rows}
print("PASS: 24 exact source/target temperature rows; all RH differ from LuhaMet by >35 pp; 16 additional non-bracketed targets; zero RH events; one unrelated rainRate event reconciled; no proposal")
