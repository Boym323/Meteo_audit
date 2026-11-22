#!/usr/bin/env python3
"""Validate aggregated protected-year 2021 diagnostic checkpoint artifacts."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports/2026-11-13-protected-year-2021-diagnostics.csv"
REPORT_PATH = ROOT / "reports/2026-11-13-protected-year-2021-diagnostics.md"


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = {r["metric"]: r["value"] for r in csv.DictReader(f)}
    expected = {
        "rows_total": "103464",
        "min_interval_min": "5",
        "max_interval_min": "5",
        "non5_interval_rows": "0",
        "adjacent_pairs": "103463",
        "delta_300s": "103368",
        "gaps_gt_300s": "95",
        "max_delta_s": "166500",
        "gaps_ge_1d": "1",
        "conditional_5m_missing_slots": "1655",
        "freezing_rows": "15962",
        "rows_below_minus10": "571",
        "freezing_low_wind_rows": "6643",
        "positive_wind_missing_dir": "44129",
        "null_radiation": "103464",
        "null_uv": "103464",
        "null_pm25_1": "103464",
    }
    for key, value in expected.items():
        assert rows.get(key) == value, (key, rows.get(key), value)
    assert int(rows["adjacent_pairs"]) == int(rows["rows_total"]) - 1
    assert int(rows["delta_300s"]) + int(rows["gaps_gt_300s"]) == int(rows["adjacent_pairs"])
    assert int(rows["expected_full_year_5m_rows"]) - int(rows["rows_total"]) == 1656
    assert int(rows["missing_slots_on_5m_grid"]) == int(rows["conditional_5m_missing_slots"])
    report = REPORT_PATH.read_text(encoding="utf-8")
    for phrase in ("diagnostický", "ER-01/ER-02", "ER-04", "nevznikají kandidáti oprav"):
        assert phrase in report, phrase
    print(f"protected-year 2021 diagnostics: OK ({len(rows)} metrics; 103,464 rows; no correction scope)")


if __name__ == "__main__":
    main()
