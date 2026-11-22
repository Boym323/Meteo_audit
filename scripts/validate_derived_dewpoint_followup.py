"""Validate aggregate reconciliation for dewpoint after applied RH changes."""
from csv import DictReader
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "reports/2026-11-13-derived-dewpoint-rh-change-followup.csv"
rows = {r["scope"]: r for r in DictReader(p.open(newline="", encoding="utf-8"))}
expected = {
    "2018_Q1_INTERIM": (4224, 4224, 4224, 4224, 0),
    "2019": (1096, 1085, 1096, 1085, 0),
    "2022_04_TARGET": (2194, 2194, 1077, 2194, 0),
}
assert set(rows) == set(expected)
for year, values in expected.items():
    row = rows[year]
    actual = tuple(int(row[k]) for k in (
        "compared_rows", "old_rh_present", "current_rh_delta_gt2c",
        "stored_dp_matches_old_rh_within_0_1c", "with_dewpoint_history"))
    assert actual == values, (year, actual, values)
    assert int(row["current_rh_matches_latest_new"]) == int(row["compared_rows"]), year
    assert float(row["old_rh_max_abs_delta_c"]) < 0.1, year
print("dewpoint/RH-change aggregate checks: OK (3 scopes)")
