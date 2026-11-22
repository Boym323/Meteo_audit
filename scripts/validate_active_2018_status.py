#!/usr/bin/env python3
"""Validate the Q1 2018 active reconstruction status reconciliation."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports/2026-11-13-active-2018-reconstruction-status.csv"
REPORT_PATH = ROOT / "reports/ACTIVE_2018_RECONSTRUCTION_STATUS.md"


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    exp = {r["variable"] + ":" + r["batch_month_label"]: int(r["expected_count_from_goal"])
           for r in rows if r["record_type"] == "goal_expectation"}
    observed = {}
    for r in rows:
        if r["record_type"] == "recent_batch_observed":
            key = r["variable"] + ":" + r["batch_month_label"]
            observed[key] = observed.get(key, 0) + int(r["event_rows"])
            assert int(r["event_rows"]) == int(r["unique_targets"])
            assert int(r["event_rows"]) == int(r["current_matches"])
            assert int(r["missing_archive"]) == 0
    assert exp["outTemp:2018-02"] == 1745
    assert exp["outTemp:2018-03"] == 3932
    assert exp["outHumidity:2018-02"] == 487
    assert exp["outHumidity:2018-03"] == 1036
    assert sum(exp.values()) == 7200
    assert observed["outTemp:2018-02"] == 3372
    assert observed["outTemp:2018-03"] == 3932
    assert observed["outHumidity:2018-02"] == 487
    assert observed["outHumidity:2018-03"] == 1036
    latest = {r["variable"]: r for r in rows if r["record_type"] == "latest_q1_state"}
    assert latest["outTemp"]["unique_targets"] == "10118"
    assert latest["outHumidity"]["unique_targets"] == "5890"
    assert all(r["unique_targets"] == r["current_matches"] for r in latest.values())
    report = REPORT_PATH.read_text(encoding="utf-8")
    for phrase in ("INTERIM", "ER-23", "Nejde o důkaz neoprávněné změny"):
        assert phrase in report
    print(f"active 2018 status: OK ({len(rows)} aggregate rows; discrepancy retained for review)")


if __name__ == "__main__":
    main()
