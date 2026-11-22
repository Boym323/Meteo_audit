#!/usr/bin/env python3
"""Validate and summarize aggregate hashes for source copies in long gaps."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/long_gap_source_copy_field_hashes.json"
CSV_OUT = ROOT / "reports/2026-11-13-long-gap-source-copy-field-concordance.csv"
MD_OUT = ROOT / "reports/2026-11-13-long-gap-source-copy-field-concordance.md"
FIELDS = ["usUnits", "interval", "outTemp", "outHumidity", "rain", "rainRate", "windSpeed", "windDir", "windGust", "barometer"]

def main():
    obj = json.loads(SOURCE.read_text())
    gaps = obj["gaps"]
    assert len(gaps) == 44 and len({g["gap_id"] for g in gaps}) == 44
    active = [g for g in gaps if int(next(r for r in g["source_availability"] if r["source_database"] == "old_weewx")["source_rows"]) > 0]
    assert len(active) == 35
    assert all(g["copy_comparison"]["exact_timestamp_sequence"] for g in active)
    assert all(not g["copy_comparison"]["hash_truncation_detected"] for g in active)
    counts = {f: Counter() for f in FIELDS}
    exact_full_rows = 0
    output = []
    for g in gaps:
        c = g["copy_comparison"]
        if c["rows"] and all(c["fields"][f]["exact_sequence_equal"] for f in FIELDS):
            exact_full_rows += 1
        for f in FIELDS:
            if not c["rows"]:
                state = "NO_SOURCE_ROWS_IN_EITHER_ARCHIVE"
                old_n = wh_n = ""
                equal_availability = equal_values = ""
            else:
                x = c["fields"][f]
                old_n, wh_n = x["nonnull_count_old"], x["nonnull_count_wh1080"]
                equal_availability = x["availability_equal"]
                equal_values = x["exact_sequence_equal"]
                if equal_values:
                    state = "MATCH"
                elif not equal_availability:
                    state = "NONNULL_AVAILABILITY_CONFLICT"
                else:
                    state = "VALUE_SEQUENCE_CONFLICT"
                counts[f][state] += 1
            output.append({
                "gap_id": g["gap_id"], "year": g["year"], "delta_seconds": g["delta"],
                "source_rows_each": c["rows"], "timestamp_sequence_equal": c["exact_timestamp_sequence"],
                "variable": f, "old_weewx_nonnull": old_n, "weewx_WH1080_nonnull": wh_n,
                "availability_equal": equal_availability, "ordered_timestamp_value_hash_equal": equal_values,
                "disposition": state,
            })
    assert exact_full_rows == 5
    assert len(output) == 440
    with CSV_OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(output[0]))
        w.writeheader(); w.writerows(output)
    lines = [
        "# Source-copy field concordance inside long archive gaps",
        "",
        "**Scope:** 44 reconstruction gaps >=24h. READ-ONLY database-side SHA-256 fingerprints compare ordered `(dateTime, value)` sequences in `old_weewx` and `weewx_WH1080`, independently for each listed field. Concatenated byte-length checks passed, so hashes were not truncated. No raw values are exported.",
        "",
        "## Results",
        "",
        "- Reconstruction has no interior rows in each catalogued gap by the gap definition.",
        "- 35 gaps have source rows in both historical archives; the other 9 have none in either.",
        "- In all 35 source-present gaps, the complete ordered timestamp sequence matches exactly. `usUnits` and `interval` sequences also match in all 35.",
        f"- All ten field sequences match in only {exact_full_rows}/35 source-present gaps. Equal row counts and timestamp keys therefore do not imply identical historical measurements.",
        "",
        "| Field | Exact sequence matches | Value or availability conflicts | Availability-count conflicts |",
        "|---|---:|---:|---:|",
    ]
    for f in FIELDS:
        c = counts[f]
        matches = c["MATCH"]
        avail = c["NONNULL_AVAILABILITY_CONFLICT"]
        val = c["VALUE_SEQUENCE_CONFLICT"]
        lines.append(f"| `{f}` | {matches} | {val + avail} | {avail} |")
    lines += [
        "",
        "For `outTemp`, `windSpeed`, `windDir`, `windGust`, and `barometer`, 29/35 ordered value sequences differ despite exact timestamp agreement. `rain` differs in 16/35. `rainRate`, `usUnits`, and `interval` match in 35/35. `outHumidity` has 34 matches and one sequence/availability conflict. These are exact-copy comparisons, not independent sensor votes.",
        "",
        "## Interpretation and limits",
        "",
        "This demonstrates field-specific historical divergence/transformations between the two archives within 30 source-present gaps. It does not identify which archive's values were retained, removed, scaled, or corrected, nor whether divergence reflects prior cleaning, unit conversion, NULL policy, or sensor QC. The hash establishes sequence equality/inequality for the selected fields, not meteorological correctness or historical intent. No automatic RESTORED proposal is permitted from this finding.",
        "",
        "Per-gap comparisons for the three dotted production database names could not be obtained: Weather MCP `execute_sql` returns `INVALID_ARGUMENT` although database listing exposes those names. The per-gap result is therefore limited to the reconstruction and two legacy archives; existing annual/band-level six-archive aggregates are not per-gap concordance.",
        "",
        "Reproduction: `python3 scripts/build_long_gap_source_copy_field_report.py`; database query template: `sql/readonly/long_gap_source_copy_field_fingerprints.sql`; compact machine evidence: `data/long_gap_source_copy_field_hashes.json`.",
        "",
    ]
    MD_OUT.write_text("\n".join(lines))
    print(f"PASS: 44 gaps; {len(active)} exact timestamp sequences; full-row equality {exact_full_rows}/35; output rows={len(output)}")

if __name__ == "__main__":
    main()
