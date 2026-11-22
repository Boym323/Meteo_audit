#!/usr/bin/env python3
"""Validate aggregate exact-time RH source availability checkpoint."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "reports/2026-11-13-rh-luhamet-exact-source-availability-2015-2017.csv"
REPORT = ROOT / "reports/2026-11-13-rh-luhamet-exact-source-availability-2015-2017.md"


def main() -> None:
    with CSV.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    expected = {
        "2015": (101261,3658,70961,69868,2978,1093),
        "2016": (87902,12810,87852,85802,12270,2050),
        "2017": (76831,24334,76779,75429,23334,1350),
    }
    cols = ("archive_rows","target_rh_null","exact_luhamet_timestamps",
            "valid_nonzero_luhamet_rh","null_target_valid_exact_reference_no_rh_history",
            "null_target_reference_rh_zero")
    for row in rows:
        assert tuple(int(row[c]) for c in cols) == expected[row["utc_year"]]
        assert row["reference_quality_status"] == "reference_only"
        assert row["source_resolution"] == "5min"
    assert sum(int(r["null_target_valid_exact_reference_no_rh_history"]) for r in rows) == 38582
    assert sum(int(r["target_rh_null"]) for r in rows) == 40802
    report = REPORT.read_text(encoding="utf-8")
    for term in ("38,582", "reference_only", "does not validate a transfer model", "ER-26"):
        assert term in report, term
    print("RH exact-source availability: OK (2015–2017; 38,582 exact-time availability cases)")


if __name__ == "__main__":
    main()
