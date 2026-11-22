#!/usr/bin/env python3
"""Capture read-only live archive/table metadata for the historical source catalog."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pymysql

DATABASES = [
    "pocasi-loucka.eu", "pocasi-loucka.eu_old", "pocasi-loucka.eu_GW1000",
    "old_weewx", "weewx_WH1080", "loucka_reconstruction",
]


def quote(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


def connect(database: str):
    conn = pymysql.connect(
        host=os.environ["WEATHER_DB_HOST"], port=int(os.environ.get("WEATHER_DB_PORT", "3306")),
        user=os.environ["WEATHER_DB_USER"], password=os.environ["WEATHER_DB_PASSWORD"],
        database=database, charset="utf8mb4", autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    cur.execute("SET SESSION TRANSACTION READ ONLY")
    cur.execute("START TRANSACTION READ ONLY")
    cur.close()
    return conn


def main() -> None:
    snapshot = {
        "schema": "loucka-historical-source-inventory-v1",
        "captured_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "read_only": True,
        "server_version": None,
        "archives": [],
        "reconstruction_evidence_tables": [],
        "reference_stations": [],
    }
    for database in DATABASES:
        conn = connect(database)
        try:
            cur = conn.cursor()
            cur.execute("SELECT VERSION() AS version")
            version = cur.fetchone()["version"]
            if snapshot["server_version"] is None:
                snapshot["server_version"] = version
            cur.execute(f"SHOW TABLES FROM {quote(database)}")
            table_names = [next(iter(row.values())) for row in cur.fetchall()]
            archive_exists = "archive" in table_names
            item = {"database": database, "accessible": True, "tables": sorted(table_names), "archive": None}
            if archive_exists:
                cur.execute(f"SELECT COUNT(*) AS row_count,MIN(`dateTime`) AS min_timestamp,MAX(`dateTime`) AS max_timestamp,COUNT(DISTINCT `dateTime`) AS distinct_timestamps FROM {quote(database)}.`archive`")
                stats = cur.fetchone()
                cur.execute(f"SELECT `usUnits`,COUNT(*) AS row_count FROM {quote(database)}.`archive` GROUP BY `usUnits` ORDER BY `usUnits`")
                units = {str(r["usUnits"]): int(r["row_count"]) for r in cur.fetchall()}
                cur.execute(f"SELECT `interval`,COUNT(*) AS row_count FROM {quote(database)}.`archive` GROUP BY `interval` ORDER BY `interval`")
                intervals = {str(r["interval"]): int(r["row_count"]) for r in cur.fetchall()}
                cur.execute(f"SHOW CREATE TABLE {quote(database)}.`archive`")
                ddl = cur.fetchone()["Create Table"]
                item["archive"] = {
                    "row_count": int(stats["row_count"]),
                    "distinct_timestamps": int(stats["distinct_timestamps"]),
                    "duplicate_timestamp_count": int(stats["row_count"] - stats["distinct_timestamps"]),
                    "min_timestamp": int(stats["min_timestamp"]) if stats["min_timestamp"] is not None else None,
                    "max_timestamp": int(stats["max_timestamp"]) if stats["max_timestamp"] is not None else None,
                    "usUnits_distribution": units,
                    "interval_minutes_distribution": intervals,
                    "schema_sha256": hashlib.sha256(ddl.encode()).hexdigest(),
                }
            snapshot["archives"].append(item)
            if database == "loucka_reconstruction":
                for table in sorted(t for t in table_names if t != "archive"):
                    cur.execute(f"SELECT COUNT(*) AS row_count FROM {quote(database)}.{quote(table)}")
                    snapshot["reconstruction_evidence_tables"].append({"table": table, "row_count": int(cur.fetchone()["row_count"])})
                if "reference_stations" in table_names:
                    cur.execute(f"SELECT * FROM {quote(database)}.`reference_stations` ORDER BY 1")
                    snapshot["reference_stations"] = cur.fetchall()
            conn.rollback()
            cur.close()
        finally:
            conn.close()
    print(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
