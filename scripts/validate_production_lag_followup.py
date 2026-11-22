#!/usr/bin/env python3
"""Validate aggregated live production/reconstruction lag checkpoint."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports/2026-11-13-production-reconstruction-lag-followup.csv"
REPORT_PATH = ROOT / "reports/2026-11-13-production-reconstruction-lag-followup.md"


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = {r["metric"]: r["value"] for r in csv.DictReader(f)}
    expected = {
        "snapshot_utc": "2026-11-13T00:00:00Z",
        "production_last_epoch": "1794528000",
        "rows_after_reconstruction_anchor": "4135",
        "interval_not_5": "0",
        "non16_rows": "0",
        "delta_300s": "4132",
        "delta_not_300s": "3",
        "conditional_missing_5m_slots": "3",
        "null_outTemp": "0",
        "null_outHumidity": "0",
        "null_rain": "0",
        "null_rainRate": "0",
        "null_radiation": "183",
        "null_UV": "183",
        "max_radiation": "312.35866666666675",
        "max_UV": "3",
    }
    for key, value in expected.items():
        assert rows.get(key) == value, (key, rows.get(key), value)
    assert int(rows["delta_300s"]) + int(rows["delta_not_300s"]) == int(rows["rows_after_reconstruction_anchor"])
    assert int(rows["elapsed_seconds_between_maxima"]) == int(rows["production_last_epoch"]) - int(rows["reconstruction_anchor_epoch"])
    for i in (1, 2, 3):
        assert rows[f"gap{i}_delta_seconds"] == "600"
    report = REPORT_PATH.read_text(encoding="utf-8")
    for phrase in ("2026-11-13 00:00 UTC", "tři kroky po 600 s", "Nebyla kopírována data"):
        assert phrase in report, phrase
    print(f"production lag follow-up: OK ({len(rows)} metrics; 4,135 tail rows; 3 gaps)")


if __name__ == "__main__":
    main()
