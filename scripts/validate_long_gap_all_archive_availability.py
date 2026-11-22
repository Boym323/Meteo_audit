#!/usr/bin/env python3
"""Validate aggregate archive coverage for the 2011-2012 long gap."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "reports/2026-11-13-long-gap-all-archive-availability.csv"
REPORT = ROOT / "reports/2026-11-13-long-gap-all-archive-availability.md"


def main() -> None:
    with CSV.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 6
    by_name = {r["archive"]: r for r in rows}
    assert by_name["loucka_reconstruction"]["rows_inside_open_gap"] == "0"
    for name in ("old_weewx", "weewx_WH1080"):
        r = by_name[name]
        assert r["rows_inside_open_gap"] == "3560"
        assert r["outTemp_nonnull"] == "3560"
        assert r["outTemp_zero"] == "3264"
    assert by_name["pocasi-loucka.eu"]["rows_inside_open_gap"] == "0"
    assert by_name["pocasi-loucka.eu_GW1000"]["rows_inside_open_gap"] == "0"
    assert by_name["pocasi-loucka.eu_old"]["rows_inside_open_gap"] == "1"
    report = REPORT.read_text(encoding="utf-8")
    for term in ("185 d 12 h 8 min", "3 264", "296 non-NULL RH párů", "ER-01/ER-02"):
        assert term in report, term
    print("long-gap all-archive availability: OK (6 archives; 3,560 paired source rows)")


if __name__ == "__main__":
    main()
