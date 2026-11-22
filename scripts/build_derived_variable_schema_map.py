#!/usr/bin/env python3
"""Build a deterministic schema-presence map for GOAL-derived variables."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/2026-11-13-archive-column-metadata.csv"
OUTPUT = ROOT / "reports/2026-11-13-derived-variable-schema-map.csv"
ARCHIVES = (
    "loucka_reconstruction",
    "pocasi-loucka.eu",
    "pocasi-loucka.eu_GW1000",
    "pocasi-loucka.eu_old",
    "old_weewx",
    "weewx_WH1080",
)
VARIABLES = (
    "dewpoint", "inDewpoint", "windchill", "heatindex", "appTemp", "humidex",
    "cloudbase", "altimeter", "windrun", "ET", "maxSolarRad", "vpd", "wbgt",
    "outHumAbs", "outThetaE", "GTS", "GTSdate", "dayET", "ET24", "yearGDD",
    "seasonGDD",
)

with SOURCE.open(newline="", encoding="utf-8") as stream:
    metadata = list(csv.DictReader(stream))

by_variable: dict[str, dict[str, str]] = {}
for variable in VARIABLES:
    schemas = {
        row["TABLE_SCHEMA"]: row
        for row in metadata
        if row["TABLE_NAME"] == "archive" and row["COLUMN_NAME"] == variable
    }
    present = [archive for archive in ARCHIVES if archive in schemas]
    types = sorted({schemas[archive]["COLUMN_TYPE"] for archive in present})
    by_variable[variable] = {
        "variable": variable,
        "archive_schema_count": str(len(present)),
        "archive_schemas": ";".join(present),
        "column_types": ";".join(types),
        "in_reconstruction": str("loucka_reconstruction" in schemas).lower(),
        "in_main_production": str("pocasi-loucka.eu" in schemas).lower(),
        "formula_and_producer": "not_established_by_schema_metadata",
        "metadata_source": "reports/2026-11-13-archive-column-metadata.csv",
    }

fields = (
    "variable", "archive_schema_count", "archive_schemas", "column_types",
    "in_reconstruction", "in_main_production", "formula_and_producer", "metadata_source",
)
with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(by_variable[variable] for variable in VARIABLES)
print(f"wrote {len(VARIABLES)} derived-variable rows to {OUTPUT.relative_to(ROOT)}")
