#!/usr/bin/env python3
"""Reconcile the consolidated rain audit against its aggregate source CSVs."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


physical = rows("reports/2026-11-13-rain-physical-range-screen.csv")
assert len(physical) == 17, len(physical)
for field in ("rain_negative", "rainRate_negative"):
    assert sum(int(row[field]) for row in physical) == 0, field
assert sum(int(row["n_rows"]) for row in physical) == 1_586_426
assert sum(int(row["rain_gt_0_5_cm"]) for row in physical) == 74
assert sum(int(row["rain_gt_1_cm"]) for row in physical) == 3
assert sum(int(row["rainRate_ge_5_cm_h"]) for row in physical) == 35
assert sum(int(row["rainRate_ge_10_cm_h"]) for row in physical) == 4

source = rows("reports/2026-11-13-rain-null-exact-source-annual.csv")
assert len(source) == 12, len(source)  # 2009–2020; 2021 excluded
assert sum(int(row["candidates"]) for row in source) == 11_780
assert sum(int(row["both_equal"]) for row in source) == 11_776
assert sum(int(row["both_differ"]) for row in source) == 0
assert sum(int(row["latest_applied_null"]) for row in source) == 129
assert sum(int(row["no_history"]) for row in source) == 11_651

phase_a = rows("reports/2026-11-13-rain-phaseA-history-reconciliation.csv")
assert sum(int(row["backup_rows"]) for row in phase_a) == 360
assert sum(int(row["initial_event_zero"]) for row in phase_a) == 360
assert sum(int(row["superseded_to_null_review"]) for row in phase_a) == 19
assert sum(int(row["current_matches_latest_event"]) for row in phase_a) == 360

protected = rows("reports/2026-11-13-rain-2021-history-artifact-reconciliation.csv")
assert sum(int(row["targets"]) for row in protected) == 1_497
assert sum(int(row["current_matches_reconstruction"]) for row in protected) == 1_497
assert sum(int(row["audit_rows"]) for row in protected) == 1_239

counter = rows("reports/2026-11-13-rain-2013-reset-aware-counter.csv")
assert len(counter) == 12
assert sum(int(row["negative_300s_steps"]) for row in counter) == 177
assert sum(int(row["exact_utc_midnight_resets"]) for row in counter) == 137
assert sum(int(row["positive_increments"]) for row in counter) == 1_430
assert sum(int(row["exact_positive_matches"]) for row in counter) == 1_139
q1 = [row for row in counter if int(row["utc_month"]) <= 3]
assert sum(int(row["positive_increments"]) for row in q1) == 255
assert sum(int(row["positive_increment_recon_zero"]) for row in q1) == 26
assert sum(int(row["positive_increment_recon_null"]) for row in q1) == 1
assert sum(int(row["both_positive"]) for row in q1) == 228
assert sum(int(row["exact_positive_matches"]) for row in q1) == 0
midyear = [row for row in counter if 5 <= int(row["utc_month"]) <= 9]
assert sum(int(row["positive_increments"]) for row in midyear) == 845
assert sum(int(row["exact_positive_matches"]) for row in midyear) == 844
lateyear = [row for row in counter if int(row["utc_month"]) >= 10]
assert sum(int(row["positive_increments"]) for row in lateyear) == 292
assert sum(int(row["exact_positive_matches"]) for row in lateyear) == 292

report = (ROOT / "reports/RAIN_AUDIT.md").read_text(encoding="utf-8")
for required in ("Stav etapy E: částečná", "11 780", "1 497", "844/845", "Žádný nový", "SELECT-only"):
    assert required in report, required

print("PASS: rain audit bundle reconciles 17-year range, source availability, history, and protected-year diagnostics")
