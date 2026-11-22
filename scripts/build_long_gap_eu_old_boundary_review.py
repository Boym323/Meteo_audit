#!/usr/bin/env python3
"""Validate 9 eu_old source rows inside long gaps against nearest target endpoints."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/long_gap_eu_old_boundary_source_review.json"
CSV_OUT = ROOT / "reports/2026-11-13-long-gap-eu_old-boundary-rows.csv"
MD_OUT = ROOT / "reports/2026-11-13-long-gap-eu_old-boundary-rows.md"
FIELDS = ["usUnits", "interval", "outTemp", "outHumidity", "rain", "rainRate", "windSpeed", "windDir", "windGust", "barometer"]
ARCHIVES = ["loucka_reconstruction", "pocasi-loucka.eu", "pocasi-loucka.eu_GW1000", "pocasi-loucka.eu_old", "old_weewx", "weewx_WH1080"]

def main():
    obj = json.loads(SOURCE.read_text())
    cases = obj["cases"]
    assert len(cases) == 9 and len({x["gap_id"] for x in cases}) == 9
    assert all(abs(int(c["source_minus_endpoint_seconds"])) <= 120 for c in cases)
    assert all(int(c["offgrid_offset_seconds"]) != 0 for c in cases)
    assert all(c["source_time_presence_by_archive"] == {
        "loucka_reconstruction": False, "pocasi-loucka.eu": False,
        "pocasi-loucka.eu_GW1000": False, "pocasi-loucka.eu_old": True,
        "old_weewx": True, "weewx_WH1080": True} for c in cases)
    rows = []
    exact = 0
    conflict_cases = []
    for c in cases:
        matches = c["eu_old_endpoint_equal_fields"]
        n_equal = sum(bool(matches[f]) for f in FIELDS)
        if n_equal == len(FIELDS): exact += 1
        else: conflict_cases.append(c)
        row = {"gap_id": c["gap_id"], "source_time": c["source_time"], "nearest_reconstruction_endpoint": c["nearest_reconstruction_endpoint"],
               "source_minus_endpoint_seconds": c["source_minus_endpoint_seconds"], "offgrid_offset_seconds": c["offgrid_offset_seconds"],
               "source_key_archives": ";".join(a for a in ARCHIVES if c["source_time_presence_by_archive"][a]),
               "target_row_absent_archives": ";".join(a for a in ARCHIVES if not c["source_time_presence_by_archive"][a]),
               "source_usUnits": c["source_row_eu_old"]["usUnits"], "source_interval": c["source_row_eu_old"]["interval"],
               "fields_equal_to_nearest_reconstruction_endpoint": n_equal,
               "classification": c["classification"]}
        for f in FIELDS:
            row[f"eu_old_{f}"] = c["source_row_eu_old"].get(f)
            row[f"reconstruction_endpoint_{f}"] = c["reconstruction_nearest_endpoint"].get(f)
            row[f"equal_{f}"] = matches[f]
        rows.append(row)
    assert exact == 8 and len(conflict_cases) == 1
    assert [f for f,v in conflict_cases[0]["eu_old_endpoint_equal_fields"].items() if not v] == ["outTemp"]
    with CSV_OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    c = conflict_cases[0]
    lines = [
        "# Nine eu_old rows near long-gap endpoints",
        "",
        "All nine `pocasi-loucka.eu_old` rows found inside 44 >=24h reconstruction gaps have exact matching timestamp rows in both `old_weewx` and `weewx_WH1080`. No matching row exists at these exact timestamps in reconstruction, current EU, or GW1000. Each source time is off the 300-second grid and only 59–120 seconds from an existing reconstruction endpoint.",
        "",
        f"At the nearest existing reconstruction endpoint, 8/9 `eu_old` rows match all ten checked fields exactly (`usUnits`, `interval`, temperature, humidity, rain, rainRate, windSpeed, direction, gust and barometer). They are classified `TIMESTAMP_DUPLICATE_SUSPECTED`, not restoration candidates. Gap {c['gap_id']} is the sole conflict: its off-grid source temperature is {c['source_row_eu_old']['outTemp']} °C versus {c['reconstruction_nearest_endpoint']['outTemp']} °C at the nearest endpoint; the other nine fields match. Retain it as `TIMESTAMP_DUPLICATE_SUSPECTED_WITH_FIELD_CONFLICT_REVIEW`.",
        "",
        "The five rows from 2015–2017 use `usUnits=16` in eu_old and `usUnits=17` in old/WH1080. In four nonzero windSpeed/windGust cases the eu_old values are exactly 3.6× the old/WH values, matching the values at the `usUnits=16` reconstruction endpoint; one zero-wind case remains zero. This is bounded evidence of a field-specific unit transform for these timestamps only, not proof of a complete historical epoch rule. The four earlier rows carry the unit metadata difference but their wind values are numerically unchanged. Rain also has field-specific availability/value differences. No global conversion rule is inferred from nine edge rows.",
        "",
        "The rows are near existing gap boundaries, rather than a continuous source series through the gap. This pattern supports a timestamp-shift/duplicate hypothesis. It does not prove the historical merge deliberately removed them. No timestamp was shifted and no proposal was created.",
        "",
        "Reproduction: `python3 scripts/build_long_gap_eu_old_boundary_review.py`; all-six archive timestamp query: `sql/readonly/long_gap_eu_old_boundary_source_review.sql`; source/result JSON: `data/long_gap_eu_old_boundary_source_review.json`.",
        "",
    ]
    MD_OUT.write_text("\n".join(lines))
    print(f"PASS: {len(cases)} off-grid source rows within 120 s of endpoints; {exact} exact endpoint duplicates; 1 outTemp conflict")

if __name__ == "__main__":
    main()
