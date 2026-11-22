#!/usr/bin/env python3
"""Check consistency of the locally generated long-gap triage artifacts."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read_csv(rel):
    with (ROOT / rel).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

catalog = read_csv("reports/2026-11-12-gap-event-catalog.csv")
long_rows = read_csv("reports/2026-11-12-long-gap-cases-ge-1d.csv")
overlap = read_csv("reports/2026-11-12-long-gap-source-overlap.csv")
availability = read_csv("reports/2026-11-12-long-gap-outtemp-source-availability.csv")
zero_runs = read_csv("reports/2026-11-12-long-gap-outtemp-zero-runs.csv")
history = read_csv("reports/2026-11-12-long-gap-outtemp-source-history.csv")
luhamet = read_csv("reports/2026-11-12-long-gap-luhamet-exact-context.csv")

assert len(catalog) == 24_523
assert len(long_rows) == 44
assert sum(int(r["delta_seconds"]) >= 604_800 for r in long_rows) == 5
assert sum(int(r["delta_seconds"]) >= 7_776_000 for r in long_rows) == 1
assert all((r["prev_interval"], r["current_interval"]) == ("5", "5") for r in long_rows)
assert any("2021 diagnostic only" in r["review_flags"] for r in long_rows)
assert any("2018 Q1 interim/live" in r["review_flags"] for r in long_rows)

assert len(overlap) == 5
assert [int(r["shared_exact_timestamps"]) for r in overlap] == [3561, 5344, 4812, 1, 2263]
assert len(availability) == 5
assert sum(int(r["shared_timestamps"]) for r in availability) == 15_981
expected_zero = {"1": 3264, "2": 5343, "3": 4810, "4": 0, "5": 2261}
assert {r["gap_id"]: int(r["WH1080_zero"]) for r in availability} == expected_zero
assert all(int(r["both_nonnull_equal"]) == int(r["shared_timestamps"]) - int(r["old_null_WH1080_value"]) for r in availability)

assert {r["gap_id"]: int(r["zero_rows"]) for r in zero_runs} == {k: v for k, v in expected_zero.items() if v}
assert sum(int(r["source_timestamps_with_outTemp"]) for r in history) == 15_981
assert sum(int(r["history_events"]) for r in history) == 0
assert sum(int(r["targets_with_history"]) for r in history) == 0
assert len(luhamet) == 3
assert {r["gap_id"]: int(r["exact_luhamet_pairs"]) for r in luhamet} == {"2": 0, "3": 4601, "5": 2254}
assert luhamet[1]["quality_status"] == "reference_only" and luhamet[1]["source_resolution"] == "5min"
assert luhamet[2]["quality_status"] == "reference_only" and int(luhamet[2]["reference_below0"]) == 1803
print("validated: gap catalog, source overlap, zero runs/history, and LuhaMet exact-time context")
