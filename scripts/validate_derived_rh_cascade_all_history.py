"""Validate aggregate counts and dependency exposure in the RH cascade report."""
from csv import DictReader
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "reports/2026-11-13-derived-rh-cascade-all-history.csv"
rows = {r["change_type"]: r for r in DictReader(p.open(newline="", encoding="utf-8"))}
expected = {
    "changed_nonnull": (7586, 7586, 7503, 7472, 6839),
    "cleared_to_null": (288, 288, 288, 282, 271),
    "filled_from_null": (12838, 12838, 11, 11, 11),
}
assert set(rows) == set(expected)
for label, values in expected.items():
    row = rows[label]
    actual = tuple(int(row[k]) for k in (
        "target_count", "current_matches_latest_new", "dewpoint_present",
        "appTemp_present", "outThetaE_present"))
    assert actual == values, (label, actual, values)
    for channel in ("dewpoint_present", "heatindex_present", "humidex_present", "cloudbase_present", "outHumAbs_present"):
        assert row[channel] == row["dewpoint_present"], (label, channel)
assert sum(int(r["target_count"]) for r in rows.values()) == 20712
assert sum(int(rows[k]["current_matches_latest_new"]) for k in rows) == 20712
print("all-history RH cascade aggregate checks: OK (20,712 targets)")
