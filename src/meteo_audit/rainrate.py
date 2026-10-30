"""Read-only yearly comparison counts for stored rain and rainRate values."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

from .db import ALLOWED_DATABASES, quote_database, query
from .monthly import UTC, _code_version
from .time_bounds import archive_period_predicate, local_year_bounds


def year_bounds(year: int) -> tuple[int, int]:
    """Return UTC endpoints for the local WeeWX year (start, end]."""
    return local_year_bounds(year)


def audit_year(database: str, year: int) -> dict[str, object]:
    schema = quote_database(database)
    start, stop = year_bounds(year)
    sql = (
        "SELECT COUNT(*),SUM(rain IS NULL),SUM(rain=0),SUM(rain>0),"
        "SUM(rainRate IS NULL),SUM(rainRate=0),SUM(rainRate>0),"
        "SUM(rain>0 AND rainRate=0),SUM(rainRate>0 AND rain=0) "
        f"FROM {schema}.archive WHERE {archive_period_predicate(start, stop)}"
    )
    values = query(sql, timeout=120)[0].split("\t")

    def number(value: str) -> int:
        # SUM() is NULL for an empty time range; this means zero rows were
        # present, not that missing weather observations were converted to 0.
        return int(value) if value not in ("NULL", r"\N", "") else 0

    names = (
        "archive_rows", "rain_null_rows", "rain_zero_rows", "rain_positive_rows",
        "rainRate_null_rows", "rainRate_zero_rows", "rainRate_positive_rows",
        "rain_positive_rate_zero_rows", "rate_positive_rain_zero_rows",
    )
    if len(values) != len(names):
        raise ValueError("Unexpected MariaDB result shape for yearly rainRate audit")
    result: dict[str, object] = {"database": database, "local_year": year,
                                 "start_utc_epoch_exclusive": start,
                                 "stop_utc_epoch_inclusive": stop}
    result.update({name: number(value) for name, value in zip(names, values)})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=2009)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/rainrate"))
    args = parser.parse_args()
    if not 1970 <= args.start_year <= args.end_year < 2200:
        parser.error("Year range must satisfy 1970 <= start <= end < 2200")

    created = datetime.now(UTC).isoformat(timespec="seconds")
    version = _code_version()
    for database in sorted(ALLOWED_DATABASES):
        rows = [audit_year(database, year) for year in range(args.start_year, args.end_year + 1)]
        processed = sum(int(row["archive_rows"]) for row in rows)
        header = {
            "database": database,
            "report_created_utc": created,
            "timezone": "Europe/Prague",
            "rain_and_rainRate_units": "stored values; no conversion or semantic inference",
            "processed_rows": processed,
            "analysis_code_version": version,
        }
        folder = args.output_dir / database
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / "annual_rainrate_divergence.csv"
        fields = list(header) + (list(rows[0]) if rows else [])
        with output.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows({**header, **row} for row in rows)
        metadata = {
            **header,
            "analyzed_local_period": [args.start_year, args.end_year],
            "start_utc_epoch_exclusive": year_bounds(args.start_year)[0],
            "stop_utc_epoch_inclusive": year_bounds(args.end_year)[1],
            "source_table": f"{database}.archive",
            "filters": "WeeWX interval end: dateTime > local-year start and dateTime <= next local-year start",
            "measurements": "stored rain/rainRate fields; NULL, zero, and positive counts are separate",
            "output_csv": str(output),
        }
        output.with_name("annual_rainrate_divergence.metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Wrote {len(rows)} local years ({processed} rows) to {output}")


if __name__ == "__main__":
    main()
