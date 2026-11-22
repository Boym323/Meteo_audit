#!/usr/bin/env python3
"""Export a bounded UTC interval from one allowlisted archive using SELECT only."""
from __future__ import annotations
import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from meteo_audit.db import ALLOWED_DATABASES, quote_database, query

FIELD = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
MAX_RANGE_SECONDS = 366 * 24 * 60 * 60
MAX_ROWS = 100_000
DEFAULT_FIELDS = ("dateTime", "usUnits", "interval", "outTemp", "outHumidity",
                  "rain", "rainRate", "windSpeed", "windGust", "windDir", "barometer")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, choices=sorted(ALLOWED_DATABASES))
    parser.add_argument("--start-utc", type=int, required=True, help="Unix seconds; exclusive lower bound")
    parser.add_argument("--end-utc", type=int, required=True, help="Unix seconds; inclusive upper bound")
    parser.add_argument("--fields", default=",".join(DEFAULT_FIELDS), help="comma-separated archive columns")
    parser.add_argument("--limit", type=int, default=50_000)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output", type=Path, required=True, help="new CSV path; existing files are not overwritten")
    args = parser.parse_args()

    if args.start_utc < 0 or args.end_utc <= args.start_utc:
        parser.error("require 0 <= start-utc < end-utc")
    if args.end_utc - args.start_utc > MAX_RANGE_SECONDS:
        parser.error("UTC extraction range is limited to 366 days")
    if not 1 <= args.limit <= MAX_ROWS:
        parser.error(f"limit must be between 1 and {MAX_ROWS}")
    fields = [item.strip() for item in args.fields.split(",")]
    if not fields or len(fields) != len(set(fields)) or any(not FIELD.fullmatch(item) for item in fields):
        parser.error("fields must be unique simple archive column names")
    if "dateTime" not in fields:
        parser.error("fields must include dateTime")
    if args.output.exists():
        parser.error("output already exists; choose a new path")

    cols = ", ".join(f"\u0060{field}\u0060" for field in fields)
    sql = (f"SELECT {cols} FROM {quote_database(args.database)}.\u0060archive\u0060 "
           f"WHERE \u0060dateTime\u0060 > {args.start_utc} AND \u0060dateTime\u0060 <= {args.end_utc} "
           f"ORDER BY \u0060dateTime\u0060 LIMIT {args.limit}")
    raw_rows = query(sql, env_file=args.env_file, timeout=600)
    rows = [line.split("\t") for line in raw_rows]
    if any(len(row) != len(fields) for row in rows):
        raise RuntimeError("database output column count does not match requested fields")
    if len(rows) == args.limit:
        raise RuntimeError("row limit reached; narrow the time range or increase limit within the cap")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        for row in rows:
            writer.writerow(["" if value == r"\N" else value for value in row])
    print(f"READ_ONLY export: database={args.database}; rows={len(rows)}; "
          f"UTC range=({args.start_utc},{args.end_utc}]; fields={len(fields)}; file={args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
