#!/usr/bin/env python3
"""Validate schema-map rows against the captured archive column metadata."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "reports/2026-11-13-derived-variable-schema-map.csv"
SOURCE = ROOT / "reports/2026-11-13-archive-column-metadata.csv"
EXPECTED = {
    "dewpoint": 6, "inDewpoint": 5, "windchill": 6, "heatindex": 6,
    "appTemp": 5, "humidex": 5, "cloudbase": 5, "altimeter": 6,
    "windrun": 5, "ET": 6, "maxSolarRad": 5, "vpd": 2, "wbgt": 2,
    "outHumAbs": 2, "outThetaE": 2, "GTS": 2, "GTSdate": 2,
    "dayET": 2, "ET24": 2, "yearGDD": 2, "seasonGDD": 2,
}

with SOURCE.open(newline="", encoding="utf-8") as stream:
    metadata = list(csv.DictReader(stream))
with MAP.open(newline="", encoding="utf-8") as stream:
    mapped = list(csv.DictReader(stream))

assert len(mapped) == len(EXPECTED) == 21
by_name = {row["variable"]: row for row in mapped}
assert len(by_name) == 21
for variable, expected_count in EXPECTED.items():
    row = by_name[variable]
    source_schemas = {
        source["TABLE_SCHEMA"]
        for source in metadata
        if source["TABLE_NAME"] == "archive" and source["COLUMN_NAME"] == variable
    }
    mapped_schemas = set(filter(None, row["archive_schemas"].split(";")))
    assert mapped_schemas == source_schemas, (variable, mapped_schemas, source_schemas)
    assert int(row["archive_schema_count"]) == expected_count == len(source_schemas), variable
    assert row["formula_and_producer"] == "not_established_by_schema_metadata"

report = (ROOT / "reports/DERIVED_VARIABLE_AUDIT.md").read_text(encoding="utf-8")
for required in ("algoritmů", "433 955", "20 712", "není doložen", "ET24"):
    assert required in report, required

rh_cascade_path = ROOT / "reports/2026-11-13-derived-rh-cascade-all-history.csv"
with rh_cascade_path.open(newline="", encoding="utf-8") as stream:
    rh_cascade = {row["change_type"]: row for row in csv.DictReader(stream)}
assert sum(int(row["target_count"]) for row in rh_cascade.values()) == 20_712
assert sum(int(row["current_matches_latest_new"]) for row in rh_cascade.values()) == 20_712
assert int(rh_cascade["changed_nonnull"]["dewpoint_present"]) == 7_503
assert int(rh_cascade["cleared_to_null"]["dewpoint_present"]) == 288
assert int(rh_cascade["filled_from_null"]["dewpoint_present"]) == 11
assert all(int(row["vpd_present"]) == 0 and int(row["wbgt_present"]) == 0 for row in rh_cascade.values())

outtemp_path = ROOT / "reports/2026-11-13-derived-outtemp-cascade.csv"
with outtemp_path.open(newline="", encoding="utf-8") as stream:
    outtemp_cascade = list(csv.DictReader(stream))
assert len(outtemp_cascade) == 1
assert int(outtemp_cascade[0]["target_count"]) == 10_127
assert int(outtemp_cascade[0]["current_matches_latest_new"]) == 10_127
for field in ("dewpoint_present", "heatindex_present", "humidex_present", "appTemp_present",
              "windchill_present", "cloudbase_present", "vpd_present", "wbgt_present",
              "outHumAbs_present", "outThetaE_present"):
    assert int(outtemp_cascade[0][field]) == 0, field

indewpoint_path = ROOT / "reports/2026-11-13-indewpoint-current-input-consistency.csv"
with indewpoint_path.open(newline="", encoding="utf-8") as stream:
    indewpoint = list(csv.DictReader(stream))
assert len(indewpoint) == 1
assert int(indewpoint[0]["compared"]) == int(indewpoint[0]["within_0_1c"]) == 433_955
assert float(indewpoint[0]["max_abs_delta_c"]) < 0.1

print("PASS: 21 derived-field schema mappings reconcile against all 6 archive metadata snapshots")
