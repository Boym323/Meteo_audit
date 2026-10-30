"""Read-only monthly rainfall summary using WeeWX interval-end semantics.

Archive records ending at ``t`` represent ``(t - interval, t]``. Calendar
periods therefore use ``dateTime > start AND dateTime <= end``. Rainfall is
assigned to the period containing the interval's right endpoint, so a record
at local midnight belongs to the day/month/year that just ended.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .db import ALLOWED_DATABASES, quote_database, query

TZ = ZoneInfo("Europe/Prague")
UTC = timezone.utc


def months(start_year: int, end_year: int, *, now: datetime | None = None):
    """Yield local calendar month boundaries, clipped at the current instant."""
    if start_year < 1970 or end_year < start_year or end_year > 2200:
        raise ValueError("Year range must satisfy 1970 <= start <= end <= 2200")
    now = now.astimezone(TZ) if now else datetime.now(TZ)
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            start = datetime(year, month, 1, tzinfo=TZ)
            if start >= now:
                return
            stop = datetime(year + (month == 12), 1 if month == 12 else month + 1, 1, tzinfo=TZ)
            yield start, min(stop, now)


def _is_null(value: str) -> bool:
    return value in (r"\N", "NULL", "")


def _period_key(epoch: int, grain: str) -> str:
    # Right-inclusive archive intervals ending exactly on a boundary belong
    # to the period ending there. Subtract one microsecond in UTC to preserve
    # that convention, including repeated/skipped Europe/Prague wall hours.
    local = datetime.fromtimestamp(epoch, UTC).astimezone(TZ)
    local = (local.astimezone(UTC) - timedelta(microseconds=1)).astimezone(TZ)
    if grain == "day":
        return local.date().isoformat()
    if grain == "hour":
        return f"{local.date().isoformat()}T{local.hour:02d}{local.strftime('%z')}"
    raise ValueError(f"Unsupported grain: {grain}")


def summarize_rows(
    rows: list[str], start: datetime, stop: datetime, first_epoch: int,
    last_epoch: int, default_interval: int,
) -> dict[str, object]:
    """Summarize TSV rows returned for the half-open period (start, stop]."""
    begin, end = int(start.timestamp()), int(stop.timestamp())
    intervals: Counter[int] = Counter()
    units: Counter[int] = Counter()
    days: defaultdict[str, float] = defaultdict(float)
    hours: defaultdict[str, float] = defaultdict(float)
    rain_values: list[float] = []
    five_minute_rain: list[float] = []
    rates: list[float] = []
    rain_null = rate_null = rain_zero = rain_positive = 0
    rain_positive_rate_zero = rate_positive_rain_zero = 0
    gaps = off_grid_5min = irregular_deltas = 0
    previous: tuple[int, int] | None = None
    for row in rows:
        parts = row.split("\t")
        if len(parts) != 5:
            raise ValueError("Expected dateTime, interval, usUnits, rain, rainRate TSV row")
        epoch, interval, unit = map(int, parts[:3])
        rain_s, rate_s = parts[3:]
        intervals[interval] += 1
        units[unit] += 1
        off_grid_5min += epoch % 300 != 0
        if previous:
            delta = epoch - previous[0]
            expected_step = previous[1] * 60
            if expected_step > 0 and delta > expected_step:
                quotient, remainder = divmod(delta, expected_step)
                if remainder == 0:
                    gaps += max(0, quotient - 1)
                else:
                    irregular_deltas += 1
        previous = epoch, interval
        if _is_null(rain_s):
            rain_null += 1
        else:
            rain = float(rain_s)
            rain_values.append(rain)
            if interval == 5:
                five_minute_rain.append(rain)
            rain_zero += rain == 0
            rain_positive += rain > 0
            days[_period_key(epoch, "day")] += rain
            hours[_period_key(epoch, "hour")] += rain
            if not _is_null(rate_s):
                rain_positive_rate_zero += rain > 0 and float(rate_s) == 0
        if _is_null(rate_s):
            rate_null += 1
        else:
            rate = float(rate_s)
            rates.append(rate)
            if not _is_null(rain_s):
                rate_positive_rain_zero += rate > 0 and float(rain_s) == 0

    count = len(rows)
    mode_interval = intervals.most_common(1)[0][0] if intervals else default_interval
    # Number of positions on the nominal UTC grid in (begin, end]. This is an
    # estimate of record opportunity, not measurement quality or verification.
    period_s = mode_interval * 60
    expected = max(0, end // period_s - begin // period_s)
    if begin >= last_epoch or end < first_epoch:
        expected = 0
    else:
        clipped_begin = max(begin, first_epoch)
        expected = max(0, end // period_s - clipped_begin // period_s)
    status = "outside_archive_range" if begin >= last_epoch or end < first_epoch else (
        "no_rows_within_archive_range" if not count else "has_rows"
    )
    unit_summary = ";".join(f"{key}:{value}" for key, value in sorted(units.items()))
    interval_summary = ";".join(f"{key}:{value}" for key, value in sorted(intervals.items()))
    mm_factor = 10.0 if units and set(units) == {16} else None
    rain_total = sum(rain_values) if rain_values else None
    return {
        "local_month": start.strftime("%Y-%m"),
        "calendar_month_complete": stop.day == 1 and stop.hour == 0 and stop.minute == 0,
        "first_archive_month_partial": begin < first_epoch < end,
        "last_archive_month_partial": begin < last_epoch < end,
        "range_status": status,
        "start_utc_epoch_exclusive": begin,
        "stop_utc_epoch_inclusive": end,
        "rows": count,
        "expected_grid_rows_estimated": expected,
        "row_coverage_pct_estimated": round(100 * count / expected, 3) if expected else None,
        "missing_rows_estimated": max(0, expected - count),
        "missing_intervals_between_rows_estimated": gaps,
        "irregular_timestamp_steps": irregular_deltas,
        "off_5min_utc_grid_rows": off_grid_5min,
        "rain_null_rows": rain_null,
        "rain_zero_rows": rain_zero,
        "rain_positive_rows": rain_positive,
        "rainRate_null_rows": rate_null,
        "rain_positive_rate_zero_rows": rain_positive_rate_zero,
        "rate_positive_rain_zero_rows": rate_positive_rain_zero,
        "interval_counts_min": interval_summary,
        "usUnits_counts": unit_summary,
        "rain_sum_stored": round(rain_total, 9) if rain_total is not None else None,
        "rain_sum_mm_if_usUnits16": round(rain_total * mm_factor, 9) if rain_total is not None and mm_factor else None,
        "max_interval_rain_stored": max(rain_values, default=None),
        "max_5min_rain_stored": max(five_minute_rain, default=None),
        "max_local_civic_day_sum_stored": max(days.values(), default=None),
        "max_local_clock_hour_sum_stored": max(hours.values(), default=None),
        "max_rainRate_stored": max(rates, default=None),
    }


def aggregate_yearly(results: list[dict[str, object]]) -> list[dict[str, object]]:
    """Sum monthly rows once by local year; do not infer mixed-unit totals."""
    grouped: dict[str, dict[str, object]] = {}
    year_units: dict[str, Counter[int]] = defaultdict(Counter)
    for row in results:
        year = str(row["local_month"])[:4]
        total = grouped.setdefault(year, {
            "year_local": year, "months_included": 0, "observed_rows": 0,
            "expected_grid_rows_estimated": 0, "rain_null_rows": 0,
            "rain_zero_rows": 0, "rain_positive_rows": 0, "rain_sum_stored": 0.0,
            "first_archive_month_partial": False, "last_archive_month_partial": False,
            "missing_rows_estimated": 0, "rainRate_null_rows": 0,
            "rain_positive_rate_zero_rows": 0, "rate_positive_rain_zero_rows": 0,
            "max_interval_rain_stored": None, "max_5min_rain_stored": None,
            "max_local_civic_day_sum_stored": None, "max_local_clock_hour_sum_stored": None,
            "max_rainRate_stored": None,
        })
        total["first_archive_month_partial"] = bool(total["first_archive_month_partial"]) or bool(row["first_archive_month_partial"])
        total["last_archive_month_partial"] = bool(total["last_archive_month_partial"]) or bool(row["last_archive_month_partial"])
        total["months_included"] = int(total["months_included"]) + (row["range_status"] != "outside_archive_range")
        for field in ("observed_rows", "expected_grid_rows_estimated", "missing_rows_estimated",
                      "rain_null_rows", "rain_zero_rows", "rain_positive_rows", "rainRate_null_rows",
                      "rain_positive_rate_zero_rows", "rate_positive_rain_zero_rows"):
            source_field = "rows" if field == "observed_rows" else field
            total[field] = int(total[field]) + int(row[source_field] or 0)
        total["rain_sum_stored"] = float(total["rain_sum_stored"]) + float(row["rain_sum_stored"] or 0)
        for key in ("max_interval_rain_stored", "max_5min_rain_stored",
                    "max_local_civic_day_sum_stored", "max_local_clock_hour_sum_stored",
                    "max_rainRate_stored"):
            value = row[key]
            if value is not None and (total.get(key) is None or float(value) > float(total[key])):
                total[key] = float(value)
        for pair in str(row["usUnits_counts"]).split(";"):
            if pair:
                unit, count = pair.split(":", 1)
                year_units[year][int(unit)] += int(count)

    yearly: list[dict[str, object]] = []
    for year, total in grouped.items():
        stored = round(float(total["rain_sum_stored"]), 9)
        units = year_units[year]
        total["rain_sum_stored"] = stored
        total["usUnits_counts"] = ";".join(f"{unit}:{count}" for unit, count in sorted(units.items()))
        total["rain_sum_mm_if_usUnits16"] = round(stored * 10, 9) if units and set(units) == {16} else None
        expected = int(total["expected_grid_rows_estimated"])
        total["row_coverage_pct_estimated"] = round(100 * int(total["observed_rows"]) / expected, 3) if expected else None
        yearly.append(total)
    return yearly


def audit_month(start: datetime, stop: datetime, first_epoch: int, last_epoch: int,
                default_interval: int, database: str) -> dict[str, object]:
    schema = quote_database(database)
    begin, end = int(start.timestamp()), int(stop.timestamp())
    sql = (
        "SELECT dateTime,`interval`,usUnits,rain,rainRate "
        f"FROM {schema}.`archive` WHERE dateTime > {begin} AND dateTime <= {end} "
        "ORDER BY dateTime"
    )
    rows = query(sql, timeout=120)
    return summarize_rows(rows, start, stop, first_epoch, last_epoch, default_interval)


def _code_version() -> str:
    try:
        git = ["git", "-c", f"safe.directory={Path.cwd().resolve()}"]
        revision = subprocess.run(
            git + ["rev-parse", "--short", "HEAD"], check=True, capture_output=True,
            text=True, timeout=3,
        ).stdout.strip()
        dirty = subprocess.run(
            git + ["status", "--porcelain", "--", "src/meteo_audit"],
            check=True, capture_output=True, text=True, timeout=3,
        ).stdout
        return revision + ("-dirty" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", choices=sorted(ALLOWED_DATABASES), required=True)
    parser.add_argument("--start-year", type=int, default=2009)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()
    schema = quote_database(args.database)
    range_rows = query(f"SELECT MIN(dateTime),MAX(dateTime) FROM {schema}.`archive`", timeout=30)
    first_epoch, last_epoch = map(int, range_rows[0].split("\t"))
    interval_rows = query(
        f"SELECT `interval`,COUNT(*) FROM {schema}.`archive` "
        "GROUP BY `interval` ORDER BY COUNT(*) DESC LIMIT 1", timeout=60,
    )
    default_interval = int(interval_rows[0].split("\t")[0])
    results: list[dict[str, object]] = []
    for start, stop in months(args.start_year, args.end_year):
        row = audit_month(start, stop, first_epoch, last_epoch, default_interval, args.database)
        results.append(row)
        print(f"{row['local_month']}: {row['rows']} rows", flush=True)

    version = _code_version()
    created = datetime.now(UTC).isoformat(timespec="seconds")
    processed_rows = sum(int(row["rows"]) for row in results)
    analyzed_start = results[0]["local_month"] if results else None
    analyzed_end = results[-1]["local_month"] if results else None
    header = {
        "database": args.database,
        "report_created_utc": created,
        "analyzed_local_period": f"{analyzed_start}..{analyzed_end}",
        "timezone": "Europe/Prague",
        "rain_units": "stored; mm conversion only when all rows use usUnits=16",
        "processed_rows": processed_rows,
        "analysis_code_version": version,
    }
    output = args.output_dir / args.database / "monthly_rain_coverage.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(header) + (list(results[0]) if results else [])
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({**header, **row} for row in results)

    yearly = aggregate_yearly(results)
    yearly_path = output.with_name("yearly_rain_coverage.csv")
    yearly_fields = list(header) + (list(yearly[0]) if yearly else [])
    with yearly_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=yearly_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({**header, **row} for row in yearly)

    metadata = {
        "database": args.database,
        "created_utc": created,
        "analyzed_local_period": [analyzed_start, analyzed_end],
        "start_utc_epoch_exclusive": results[0]["start_utc_epoch_exclusive"] if results else None,
        "stop_utc_epoch_inclusive": results[-1]["stop_utc_epoch_inclusive"] if results else None,
        "timezone": "Europe/Prague",
        "archive_time_basis": "WeeWX end of archive interval; (start, end]",
        "rain_units": "stored units; mm conversion included only when all rows use usUnits=16 (cm)",
        "processed_rows": processed_rows,
        "analysis_code_version": version,
        "coverage_note": "Estimated archive-row opportunity on the modal interval grid; not verified-measurement availability.",
    }
    metadata_path = output.with_name("monthly_rain_coverage.metadata.json")
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(results)} monthly rows to {output}")
    print(f"Wrote {len(yearly)} yearly rows to {yearly_path}")
    print(f"Wrote provenance metadata to {metadata_path}")


if __name__ == "__main__":
    main()
