#!/usr/bin/env python3
"""Validate the six-schema information_schema.TABLES export."""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "reports/2026-11-13-database-table-catalog.csv"
with path.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream))
assert len(rows) == 102
counts = Counter(row["TABLE_SCHEMA"] for row in rows)
assert counts == Counter({
    "loucka_reconstruction": 18,
    "old_weewx": 1,
    "pocasi-loucka.eu": 80,
    "pocasi-loucka.eu_GW1000": 1,
    "pocasi-loucka.eu_old": 1,
    "weewx_WH1080": 1,
})
assert all(row["TABLE_TYPE"] == "BASE TABLE" and row["ENGINE"] == "InnoDB" for row in rows)
present = {(row["TABLE_SCHEMA"], row["TABLE_NAME"]) for row in rows}
required = {
    ("loucka_reconstruction", name) for name in (
        "reconstruction_changes", "reconstruction_batches", "reconstruction_candidates",
        "reference_stations", "reference_observations", "reference_daily",
        "reconstruction_humidity_202204", "rain_archive_original_202107", "rain_audit_202107",
        "rain_backup_202107_before_chmi_v1", "rain_qc_202107", "rain_qc_daily_202107",
        "rain_reconstruction_202107_chmi_v1",
    )
}
assert required <= present
assert all(int(row["TABLE_ROWS"] or 0) >= 0 for row in rows)
print("PASS: 102 table metadata rows, six schema counts, and all named audit tables reconcile")
