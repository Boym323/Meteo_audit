#!/usr/bin/env python3
"""Validate CHMI SRA/SRA10M comparison outputs and source-file hashes."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "reports/2026-11-13-chmi-sra-window-empirical.summary.csv"
DETAIL = ROOT / "reports/2026-11-13-chmi-sra-window-empirical.csv"
MANIFEST = ROOT / "data/chmi-rain-window/manifest.json"
EXPECTED = {
    ("0-203-0-11777", "end_at_dt"): (330, 129),
    ("0-203-0-11777", "end_at_dt_plus_24h"): (328, 305),
    ("0-203-0-11778", "end_at_dt"): (331, 172),
    ("0-203-0-11778", "end_at_dt_plus_24h"): (334, 316),
}


def main() -> None:
    with SUMMARY.open(encoding="utf-8", newline="") as f:
        summary = list(csv.DictReader(f))
    actual = {}
    for row in summary:
        key = (row["station"], row["window_candidate"])
        actual[key] = (int(row["complete_qc_windows_with_daily_value"]), int(row["exact_matches_0_1mm"]))
    if actual != EXPECTED:
        raise SystemExit(f"Unexpected aggregate summary: {actual}")
    if len(list(csv.DictReader(DETAIL.open(encoding="utf-8", newline="")))) != 730:
        raise SystemExit("Expected 730 station-day detail rows")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in manifest["daily_sources"]:
        path = ROOT / entry["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise SystemExit(f"SHA-256 mismatch: {entry['path']}")
    if len(manifest["subdaily_sources_reused"]) != 24:
        raise SystemExit("Expected 24 reused monthly CHMI subdaily files")
    for entry in manifest["subdaily_sources_reused"]:
        path = ROOT / entry["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise SystemExit(f"SHA-256 mismatch: {entry['path']}")
    for station in ("0-203-0-11777", "0-203-0-11778"):
        if actual[(station, "end_at_dt_plus_24h")][1] <= actual[(station, "end_at_dt")][1]:
            raise SystemExit(f"Expected DT+24h candidate to have more exact matches: {station}")
    print("PASS: 4 aggregate rows, 730 detail rows, 26 source hashes, and candidate-window comparison validated")


if __name__ == "__main__":
    main()
