#!/usr/bin/env python3
"""Validate the aggregate source-row checkpoint without loading raw event data."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "reports/2026-11-13-reconstruction-change-source-row-validation.csv"
REPORT = ROOT / "reports/2026-11-13-reconstruction-change-source-row-validation.md"


def main() -> None:
    with CSV.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 10
    assert sum(int(r["events"]) for r in rows) == 61002
    assert sum(int(r["source_row_missing"]) for r in rows) == 0
    assert sum(int(r["source_value_matches_raw_field"]) for r in rows) == 61002
    assert sum(int(r["source_value_null"]) for r in rows) == 0
    assert sum(int(r["target_time_equals_source_time"]) for r in rows) == 60960
    assert sum(int(r["events"]) for r in rows if r["variable"] == "rain") == 1011
    assert sum(int(r["events"]) for r in rows if r["variable"] == "rainRate") == 59871
    report = REPORT.read_text(encoding="utf-8")
    for term in ("61 002 eventů", "551 událostí", "Nepotvrzuje", "ER-25"):
        assert term in report, term
    print("source-row provenance checkpoint: OK (10 groups; 61,002 events; 551 self-RH exception documented)")


if __name__ == "__main__":
    main()
