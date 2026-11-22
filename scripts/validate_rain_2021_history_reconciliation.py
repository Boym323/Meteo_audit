#!/usr/bin/env python3
"""Validate aggregate evidence for protected-year 2021 rain history mismatch."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "reports/2026-11-13-rain-2021-null-history-reconciliation.csv"
REPORT_PATH = ROOT / "reports/PROTECTED_YEAR_2021_DIAGNOSTICS.md"


def main() -> None:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        metrics = {r["metric"]: r["value"] for r in csv.DictReader(f)}
    expected = {
        "targets": "146",
        "applied_old_matches_original": "146",
        "current_null": "0",
        "current_zero": "146",
        "current_matches_applied_old": "0",
        "current_matches_applied_new": "0",
        "current_matches_reconstruction": "146",
        "reconstruction_zero": "146",
        "latest_overall_applied": "146",
        "latest_overall_reverted": "0",
        "method": "chmi10m_idw2",
        "audit_class": "strong_suspicion_both_dry",
        "evidence_level": "humidity_screen_only",
        "qc_status": "suspect_excluded_from_screened",
    }
    for k, v in expected.items():
        assert metrics.get(k) == v, (k, metrics.get(k), v)
    report = REPORT_PATH.read_text(encoding="utf-8")
    for phrase in ("pouze diagnostický", "ER-24", "nic se nevrací"):
        assert phrase in report, phrase
    print("protected-year rain history reconciliation: OK (146 targets; no correction scope)")


if __name__ == "__main__":
    main()
