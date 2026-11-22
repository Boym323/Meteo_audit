#!/usr/bin/env python3
"""Validate saved aggregate and five-row rain upper-tail source/history screen."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANNUAL = ROOT / "reports/2026-11-13-rain-physical-range-screen.csv"
CASES = ROOT / "reports/2026-11-13-rain-extreme-source-history.csv"
EXPECTED_YEARS = list(range(2009, 2021)) + list(range(2022, 2027))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    annual = read_csv(ANNUAL)
    years = [int(r["utc_year"]) for r in annual]
    if years != EXPECTED_YEARS or any(int(r["usUnits"]) != 16 for r in annual):
        raise SystemExit("Unexpected UTC year coverage or usUnits")
    if any(int(r["rain_negative"]) or int(r["rainRate_negative"]) for r in annual):
        raise SystemExit("Negative rain/rainRate found in saved screening result")
    if sum(int(r["rain_gt_1_cm"]) for r in annual) != 3:
        raise SystemExit("Expected three archive rows with rain > 1 cm")
    if sum(int(r["rainRate_ge_10_cm_h"]) for r in annual) != 4:
        raise SystemExit("Expected four archive rows with rainRate >= 10 cm/h")
    cases = read_csv(CASES)
    if len(cases) != 5:
        raise SystemExit(f"Expected five exact-time case rows, got {len(cases)}")
    if any(r["rain_latest_state"] not in ("", "None") for r in cases):
        raise SystemExit("Unexpected rain history on selected targets")
    if any(r["rate_latest_state"] != "applied" for r in cases):
        raise SystemExit("Expected latest applied rainRate history on all selected targets")
    for r in cases:
        if float(r["rate_latest_new"]) != float(r["rate_history_source_value"]):
            raise SystemExit("rainRate latest new_value differs from logged source_value")
    old_cases = [r for r in cases if r["iso_utc"].startswith("2013-")]
    if len(old_cases) != 2:
        raise SystemExit("Expected two 2013 source-counter cases")
    for r in old_cases:
        if int(r["old_counter_step_seconds"]) != 300 or r["old_delta_matches_current_rain"] != "True":
            raise SystemExit("2013 source counter delta did not reproduce rain")
        if r["old_rate_conversion_matches_current"] != "True":
            raise SystemExit("2013 standard rainRate unit conversion did not match")
    modern = [r for r in cases if r["iso_utc"].startswith("2023-")]
    if len(modern) != 3 or any(float(r["rain"]) != float(r["gw_rain"]) or float(r["rainRate"]) != float(r["gw_rate"]) for r in modern):
        raise SystemExit("2023 selected values do not exactly match GW1000 source rows")
    print("PASS: 17 UTC years, protected 2021 excluded, nonnegative ranges, threshold counts, 5 source/history cases")


if __name__ == "__main__":
    main()
