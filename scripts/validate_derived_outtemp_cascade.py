"""Validate derived-field availability at applied outTemp targets."""
from csv import DictReader
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with (root / "reports/2026-11-13-derived-outtemp-cascade.csv").open(newline="", encoding="utf-8") as f:
    rows = list(DictReader(f))
assert len(rows) == 1
row = rows[0]
assert row["change_type"] == "filled_from_null"
assert int(row["target_count"]) == int(row["current_matches_latest_new"]) == 10127
assert int(row["current_temp_rh_available"]) == 325
assert int(row["wind_available"]) == 46
for field in ("dewpoint", "heatindex", "humidex", "appTemp", "windchill", "cloudbase", "vpd", "wbgt", "outHumAbs", "outThetaE"):
    assert int(row[f"{field}_present"]) == 0, field
with (root / "reports/2026-11-13-derived-outtemp-cascade-by-year.csv").open(newline="", encoding="utf-8") as f:
    year_rows = list(DictReader(f))
assert {r["utc_year"]: int(r["targets"]) for r in year_rows} == {"2018": 10119, "2020": 2, "2022": 5, "2024": 1}
assert sum(int(r["targets"]) for r in year_rows) == 10127
print("outTemp derived-cascade checks: OK (10,127 targets)")
