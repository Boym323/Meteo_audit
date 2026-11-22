"""Check aggregate audit-chain reconciliation for legacy rain Phase A backups."""
from csv import DictReader
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "reports/2026-11-13-rain-phaseA-history-reconciliation.csv"
with p.open(newline="", encoding="utf-8") as f:
    rows = {r["backup_name"]: r for r in DictReader(f)}
expected = {
    "daily_reset_2009_2011": (328, 328, 328, 0, 328, 328),
    "june_2010_phase_a": (30, 30, 30, 18, 12, 30),
    "phase_a_other": (2, 2, 2, 1, 1, 2),
}
assert set(rows) == set(expected)
for name, values in expected.items():
    row = rows[name]
    actual = tuple(int(row[k]) for k in (
        "backup_rows", "exactly_one_initial_batch_event", "backup_matches_initial_old",
        "superseded_to_null_review", "current_zero", "current_matches_latest_event"))
    assert actual == values, (name, actual, values)
    assert int(row["missing_initial_event"]) == int(row["multiple_initial_events"]) == 0
    assert int(row["initial_event_applied"]) == int(row["backup_rows"])
    assert int(row["initial_event_zero"]) == int(row["backup_rows"])
    assert int(row["current_null"]) + int(row["current_zero"]) == int(row["backup_rows"])
assert sum(int(r["backup_rows"]) for r in rows.values()) == 360
assert sum(int(r["superseded_to_null_review"]) for r in rows.values()) == 19
print("rain Phase A backup/history reconciliation: OK (360 targets, 19 supersessions)")
