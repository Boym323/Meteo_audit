#!/usr/bin/env python3
"""Validate annual rain NULL exact-source reconciliation and 2018 Q1 cases."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def n(row: dict[str, str], key: str) -> int:
    return int(row[key] or 0)


def main() -> None:
    annual = rows("reports/2026-11-13-rain-null-exact-source-annual.csv")
    if [n(r, "utc_year") for r in annual] != list(range(2009, 2021)):
        raise SystemExit("Annual UTC year coverage is incomplete")
    totals = {key: sum(n(r, key) for r in annual) for key in (
        "candidates", "old_available", "wh_available", "both_equal", "both_differ",
        "latest_applied_null", "latest_applied_nonnull", "latest_reverted", "no_history",
        "old_zero", "old_positive", "wh_zero", "wh_positive")}
    expected = {"candidates":11780,"old_available":11776,"wh_available":11780,
                "both_equal":11776,"both_differ":0,"latest_applied_null":129,
                "latest_applied_nonnull":0,"latest_reverted":0,"no_history":11651,
                "old_zero":11500,"old_positive":276,"wh_zero":11504,"wh_positive":276}
    if totals != expected:
        raise SystemExit(f"Unexpected annual totals: {totals}")

    monthly = rows("reports/2026-11-13-rain-null-exact-source-2018-monthly.csv")
    if {r["utc_month"]:n(r,"source_null_targets") for r in monthly} != {
        "2018-01":2796,"2018-02":3363,"2018-03":3932,"2018-12":1}:
        raise SystemExit("Unexpected 2018 monthly target counts")
    if sum(n(r,"source_null_targets") for r in monthly if r["utc_month"]<"2018-04") != 10091:
        raise SystemExit("Unexpected interim Q1 target count")
    if any(n(r,"both_rain_equal") != n(r,"source_null_targets") or n(r,"both_rain_differ") for r in monthly):
        raise SystemExit("Legacy source rain copies disagree in 2018")

    cross = rows("reports/2026-11-13-rain-null-exact-source-2018-archive-crosscheck.csv")[0]
    if (n(cross,"recon_rain_null_rows"),n(cross,"prod_exact_rows"),n(cross,"prod_rain_available"),
        n(cross,"gw_exact_rows"),n(cross,"gw_rain_available"),n(cross,"oldprod_exact_rows"),
        n(cross,"oldprod_rain_available")) != (10091,11,0,11,0,11,0):
        raise SystemExit("Unexpected alternate-archive cross-check")

    cases = rows("reports/2026-11-13-rain-null-2018-positive-source-cases.csv")
    if len(cases) != 10:
        raise SystemExit("Expected ten positive Q1 source rain cases")
    for r in cases:
        if int(r["dateTime"])-int(r["prev_time"]) != 300 or int(r["next_time"])-int(r["dateTime"]) != 300:
            raise SystemExit("Positive source case lacks exact 300-second neighbors")
        if float(r["prev_rain"]) != 0 or float(r["next_rain"]) != 0:
            raise SystemExit("Positive source case is not bracketed by zeros")
        if float(r["rain"]) != float(r["wh_rain"]) or float(r["rainRate"]) != float(r["wh_rate"]):
            raise SystemExit("Legacy copies disagree on selected positive source case")
        if n(r,"rain_history_events") or n(r,"rate_history_events"):
            raise SystemExit("Selected Q1 case unexpectedly has target history")
        if r["recon_rain"] not in ("", "None"):
            raise SystemExit("Selected current reconstruction rain is not NULL")
    patterns = rows("reports/2026-11-13-rain-null-positive-source-patterns.csv")
    expected_patterns = {2009:2,2013:60,2016:14,2017:61}
    if {n(r,"utc_year"):n(r,"positive_nohistory_targets") for r in patterns} != expected_patterns:
        raise SystemExit("Unexpected positive source pattern counts")
    by_year = {n(r,"utc_year"):r for r in patterns}
    for year in (2016,2017):
        r=by_year[year]
        if n(r,"isolated_single_row_pulse") != expected_patterns[year] or n(r,"source_rate_positive") != expected_patterns[year]:
            raise SystemExit(f"Expected isolated positive/rate-positive pulses in {year}")
        if n(r,"recon_rate_zero") != expected_patterns[year]:
            raise SystemExit(f"Expected reconstruction rainRate=0 on the NULL rain targets in {year}")
    if n(by_year[2013],"prev_300s_positive") != 57 or n(by_year[2013],"next_300s_positive") != 57:
        raise SystemExit("Unexpected 2013 adjacent source-rain run pattern")
    if sum(expected_patterns.values()) + len(cases) != 147:
        raise SystemExit("Positive source no-history candidates do not reconcile to 147")
    print("PASS: annual 2009–2020 reconciliation, 2018 cross-archive/case evidence, and positive-source neighbor patterns")


if __name__ == "__main__":
    main()
