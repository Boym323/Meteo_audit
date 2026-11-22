#!/usr/bin/env python3
"""Summarize saved READ-ONLY archive availability for the 44 >=24h gaps."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/long_gap_ge24h_per_archive_availability.json"
CSV_OUT = ROOT / "reports/2026-11-13-long-gap-per-archive-availability.csv"
MD_OUT = ROOT / "reports/2026-11-13-long-gap-per-archive-availability.md"
REQUIRED = {"loucka_reconstruction", "pocasi-loucka.eu", "pocasi-loucka.eu_GW1000", "pocasi-loucka.eu_old", "old_weewx", "weewx_WH1080"}
FIELDS = [
    "gap_id", "year", "start", "end", "delta", "source_database",
    "source_rows", "first_source_time", "last_source_time", "outTemp_nonnull",
    "outTemp_zero", "outHumidity_nonnull", "rain_nonnull", "rainRate_nonnull",
    "windSpeed_nonnull", "windDir_nonnull", "windGust_nonnull", "barometer_nonnull", "usUnits_nonnull", "interval_nonnull",
]

def main():
    obj = json.loads(SOURCE.read_text())
    gaps = obj["gaps"]
    assert len(gaps) == 44 and len({g["gap_id"] for g in gaps}) == 44
    flat = []
    by_gap = {}
    for gap in gaps:
        avail = gap["source_availability"]
        assert {r["source_database"] for r in avail} == REQUIRED
        assert len(avail) == 6
        by_gap[gap["gap_id"]] = {r["source_database"]: r for r in avail}
        for r in avail:
            flat.append({**{k: gap[k] for k in ("gap_id", "year", "start", "end", "delta")}, **r})
    assert all(int(by_gap[i]["loucka_reconstruction"]["source_rows"]) == 0 for i in by_gap)
    assert all(int(by_gap[i]["pocasi-loucka.eu"]["source_rows"]) == 0 for i in by_gap)
    assert all(int(by_gap[i]["pocasi-loucka.eu_GW1000"]["source_rows"]) == 0 for i in by_gap)
    assert sum(int(by_gap[i]["pocasi-loucka.eu_old"]["source_rows"]) for i in by_gap) == 9
    assert sum(int(by_gap[i]["pocasi-loucka.eu_old"]["source_rows"]) > 0 for i in by_gap) == 9
    assert all(int(by_gap[i]["old_weewx"]["source_rows"]) == int(by_gap[i]["weewx_WH1080"]["source_rows"]) for i in by_gap)
    totals = {db: sum(int(by_gap[i][db]["source_rows"]) for i in by_gap) for db in REQUIRED}
    assert totals["old_weewx"] == totals["weewx_WH1080"] == 31632
    hits = sum(int(by_gap[i]["old_weewx"]["source_rows"]) > 0 for i in by_gap)
    assert hits == 35
    with CSV_OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(flat)
    year_counts = Counter()
    for gap in gaps:
        if int(by_gap[gap["gap_id"]]["old_weewx"]["source_rows"]):
            year_counts[gap["year"]] += 1
    lines = [
        "# Per-archive availability inside 44 long gaps",
        "",
        "**Scope:** 44 strict open intervals between adjacent reconstruction archive endpoints with delta >=24 h. READ-ONLY, exact timestamp ranges; all six archives queried by fully-qualified schema names from the permitted `loucka_reconstruction` MCP database context.",
        "",
        "## Results",
        "",
        "- Reconstruction interior rows: 0 in all 44 intervals.",
        "- `pocasi-loucka.eu` and `pocasi-loucka.eu_GW1000`: 0 interior rows in all 44 intervals.",
        "- `pocasi-loucka.eu_old`: 9 interior rows across 9 intervals; each is near a gap endpoint and reviewed separately in `reports/2026-11-13-long-gap-eu_old-boundary-rows.md`.",
        "- `old_weewx` and `weewx_WH1080`: 31,632 rows each across the same 35 intervals; exact timestamp sequences match all 35, but field values agree across all 10 compared fields in only 5 intervals.",
        "- Source-visible gap counts by the reconstruction endpoint year: " + ", ".join(f"{y}: {year_counts[y]}" for y in sorted(year_counts)) + ".",
        "",
        "Source row presence and copy agreement do not establish meteorological correctness, operational uptime, intentional deletion, or a historical cleaning rule. In particular, exact timestamp agreement does not imply field-value agreement. No RESTORED or ESTIMATED proposal follows from availability alone.",
        "",
        "## Query access note",
        "",
        "Direct MCP `database_name` selection rejects dotted names, but fully-qualified backtick-quoted schema references work from a READ-ONLY query context selected as `loucka_reconstruction`. All six per-gap archive counts are now included. The query does not access or change other schema state.",
        "",
        "Reproduction of the local summary: `python3 scripts/summarize_long_gap_archive_availability.py`. Source aggregates: `data/long_gap_ge24h_per_archive_availability.json`; exact SQL: `sql/readonly/long_gap_ge24h_source_availability_all_six.sql`; bounds: `reports/2026-11-12-long-gap-cases-ge-1d.csv`.",
        "",
    ]
    MD_OUT.write_text("\n".join(lines))
    print(f"PASS: gaps=44 output_rows={len(flat)} six-archive rows={totals} old/WH1080 source-visible gaps={hits}")

if __name__ == "__main__":
    main()
