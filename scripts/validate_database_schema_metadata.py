#!/usr/bin/env python3
"""Validate full six-schema COLUMNS and STATISTICS metadata exports."""
import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name: str) -> list[dict[str, str]]:
    with (ROOT / "reports" / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


columns = read("2026-11-13-database-columns.csv")
indexes = read("2026-11-13-database-index-columns.csv")
catalog = read("2026-11-13-database-table-catalog.csv")
archive_columns = read("2026-11-13-archive-column-metadata.csv")
assert len(columns) == 1410
assert len(indexes) == 120
assert len(catalog) == 102
schemas = {row["TABLE_SCHEMA"] for row in columns}
assert len(schemas) == 6
column_tables = {(row["TABLE_SCHEMA"], row["TABLE_NAME"]) for row in columns}
catalog_tables = {(row["TABLE_SCHEMA"], row["TABLE_NAME"]) for row in catalog}
assert column_tables == catalog_tables
assert len({(row["TABLE_SCHEMA"], row["TABLE_NAME"], row["ORDINAL_POSITION"]) for row in columns}) == len(columns)
assert all(row["TABLE_TYPE"] == "BASE TABLE" for row in catalog)

field_names = ("TABLE_SCHEMA", "TABLE_NAME", "ORDINAL_POSITION", "COLUMN_NAME", "COLUMN_TYPE",
               "IS_NULLABLE", "COLUMN_DEFAULT", "EXTRA", "COLUMN_KEY")
archive_subset = [row for row in columns if row["TABLE_NAME"] == "archive"]
assert len(archive_subset) == len(archive_columns) == 515
assert {tuple(row[name] for name in field_names) for row in archive_subset} == {
    tuple(row[name] for name in field_names) for row in archive_columns
}

indexed_tables = {(row["TABLE_SCHEMA"], row["TABLE_NAME"]) for row in indexes}
assert indexed_tables == column_tables
index_ids = {(row["TABLE_SCHEMA"], row["TABLE_NAME"], row["INDEX_NAME"]) for row in indexes}
assert len(index_ids) == 113
assert sum(row["INDEX_NAME"] == "PRIMARY" for row in indexes) == 105
assert sum(row["INDEX_NAME"] != "PRIMARY" for row in indexes) == 15
by_schema_columns = Counter(row["TABLE_SCHEMA"] for row in columns)
assert by_schema_columns == Counter({
    "loucka_reconstruction": 265,
    "old_weewx": 61,
    "pocasi-loucka.eu": 790,
    "pocasi-loucka.eu_GW1000": 66,
    "pocasi-loucka.eu_old": 114,
    "weewx_WH1080": 114,
})
required = {
    ("loucka_reconstruction", name) for name in (
        "reconstruction_changes", "reconstruction_batches", "reconstruction_candidates",
        "reference_stations", "reference_observations", "reference_daily",
        "reconstruction_humidity_202204", "rain_archive_original_202107", "rain_audit_202107",
        "rain_backup_202107_before_chmi_v1", "rain_qc_202107", "rain_qc_daily_202107",
        "rain_reconstruction_202107_chmi_v1",
    )
}
assert required <= column_tables
print("PASS: 1,410 columns, 120 index parts, 102 tables, archive metadata parity, and key auxiliary schemas reconcile")
