#!/usr/bin/env python3
"""Offline integrity checks for the 2026-11-13 exact auxiliary-table snapshot."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
snapshot = json.loads((ROOT / "data/reconstruction_auxiliary_exact_snapshot_20261113.json").read_text())
assert snapshot["query_count"] == 17
assert len(snapshot["tables"]) == 17
expected = {
    "rain_archive_original_202107": 8921,
    "rain_audit_202107": 1310,
    "rain_backup_202107_before_chmi_v1": 8921,
    "rain_daily_reset_backup_2009_2011_v1": 328,
    "rain_phase_a_201006_backup_20261030_v1": 30,
    "rain_phase_a_backup_20261030_v1": 2,
    "rain_qc_202107": 8921,
    "rain_qc_daily_202107": 31,
    "rain_reconstruction_202107_chmi_v1": 8928,
    "reconstruction_batches": 24,
    "reconstruction_candidates": 365,
    "reconstruction_changes": 112772,
    "reconstruction_humidity_202204": 3734,
    "reference_daily": 32,
    "reference_observations": 1652638,
    "reference_stations": 2,
    "wh1080_missing_5min_candidates_20261030": 49796,
}
seen = set()
for table in snapshot["tables"]:
    name = table["table"]
    assert name not in seen
    seen.add(name)
    assert table["sql"].lstrip().upper().startswith("SELECT ")
    rows = table["result"]
    assert len(rows) == 1
    row = rows[0]
    assert int(row["exact_rows"]) == expected[name], (name, row["exact_rows"])
    assert all(k.endswith("_null") for k in row if k.endswith("_null"))
assert seen == set(expected)
by = {x["table"]: x["result"][0] for x in snapshot["tables"]}
assert int(by["rain_audit_202107"]["proposed_replacement_mm_null"]) == 1310
assert int(by["rain_qc_202107"]["validated_rain_mm_null"]) == 8921
assert int(by["rain_qc_daily_202107"]["verified_daily_rain_mm_null"]) == 31
assert int(by["reconstruction_candidates"]["proposed_value_null"]) == 338
assert int(by["reference_observations"]["exact_rows"]) == 1652638
assert snapshot["source"].find("READ_ONLY") >= 0
for table in snapshot["tables"]:
    row = table["result"][0]
    declared_nulls = sum(1 for key in row if key.endswith("_null"))
    assert table["sql"].count(" IS NULL)") == declared_nulls, table["table"]
groups = json.loads((ROOT / "data/reconstruction_auxiliary_grouped_states_20261113.json").read_text())
assert groups["group_count"] == 10 and len(groups["groups"]) == 10
grouped = {x["name"]: x["result"] for x in groups["groups"]}
assert sum(int(x["batches"]) for x in grouped["reconstruction_batches"]) == 24
assert sum(int(x["events"]) for x in grouped["reconstruction_changes_by_state"]) == 112772
assert sum(int(x["rows_n"]) for x in grouped["humidity_by_decision"]) == 3734
assert sum(int(x["rows_n"]) for x in grouped["reference_obs_by_quality"]) == 1652638
assert sum(int(x["rows_n"]) for x in grouped["wh1080_candidates_by_status"]) == 49796
delta = json.loads((ROOT / "data/reconstruction_auxiliary_delta_review_20261113.json").read_text())
assert delta["writes"] == 0
assert len(delta["checks"]["rain_reconstruction_202107_chmi_v1_minus_rain_archive_original_202107"]["timestamps"]) == 7
assert delta["checks"]["rain_archive_original_202107_minus_rain_reconstruction_202107_chmi_v1"]["rows"] == 0
current = json.loads((ROOT / "data/reconstruction_auxiliary_2021_seven_target_archive_completeness.json").read_text())
assert int(current["result"]["exact_rows"]) == 7
assert int(current["exact_numeric_columns"]) == 79
nonnull = {k.removesuffix("_nonnull") for k,v in current["result"].items() if k.endswith("_nonnull") and int(v or 0)>0}
assert nonnull == {"usUnits", "interval", "rain"}
assert int(current["result"]["rain_nonnull"]) == 7
assert int(current["result"]["rainRate_nonnull"]) == 0
hist = delta["checks"]["rain_2021_change_history"]
assert hist["target_variable_pairs"] == 7 and hist["applied_events_per_target"] == 3
assert hist["applied_events_total"] == 21 and hist["rainRate_events"] == 0
assert (ROOT / "reports/2026-11-13-2021-seven-rain-snapshot-target-history-review.md").is_file()
print(json.dumps({"validation": "PASS", "tables": len(seen), "exact_scope_row_sum": sum(expected.values()), "seven_2021_targets": 7, "measured_fields_nonnull": sorted(nonnull - {"usUnits","interval"}), "historical_rain_events": 21, "read_only": True}, indent=2))
