"""Small, dependency-free checks for rainfall archive reconstruction."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo


LOCAL_RAIN_FIELDS = ("production_rain", "gw1000_rain", "legacy_rain")


def agreed_local_rain(row: Mapping[str, object]) -> Decimal | None:
    """Return an exact value shared by the three archive copies.

    Missing or conflicting sources return None. Agreement is a source-integrity
    check only: it does not prove three independent instruments or meteorological
    plausibility. Callers must assess quality separately. This function never
    writes to a database.
    """
    values: list[Decimal] = []
    for field in LOCAL_RAIN_FIELDS:
        raw = row.get(field)
        if raw is None or str(raw).strip() == "":
            return None
        try:
            values.append(Decimal(str(raw)))
        except InvalidOperation:
            return None
    if values[0] == values[1] == values[2]:
        return values[0]
    return None


def archive_local_day(
    date_time: int, interval_minutes: int, timezone_name: str = "Europe/Prague"
) -> date:
    """Assign a WeeWX archive row to the local date its interval starts."""
    if isinstance(date_time, bool) or not isinstance(date_time, int):
        raise ValueError("date_time must be an integer Unix timestamp")
    if isinstance(interval_minutes, bool) or not isinstance(interval_minutes, int):
        raise ValueError("interval_minutes must be an integer")
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be positive")
    interval_start = datetime.fromtimestamp(
        date_time - interval_minutes * 60, tz=timezone.utc
    )
    return interval_start.astimezone(ZoneInfo(timezone_name)).date()


def summarize_archive(
    rows: Iterable[Mapping[str, object]],
    start_exclusive: int,
    end_inclusive: int,
    timezone_name: str = "Europe/Prague",
) -> dict[date, dict[str, Decimal | int]]:
    """Summarize cm-valued rain by interval-start date over WeeWX (start,end]."""
    if start_exclusive >= end_inclusive:
        raise ValueError("start_exclusive must precede end_inclusive")
    result: dict[date, dict[str, Decimal | int]] = {}
    for row in rows:
        timestamp = int(row["dateTime"])
        if not start_exclusive < timestamp <= end_inclusive:
            continue
        day = archive_local_day(timestamp, int(row["interval"]), timezone_name)
        bucket = result.setdefault(
            day,
            {"intervals": 0, "unknown_intervals": 0, "known_mm": Decimal("0")},
        )
        bucket["intervals"] = int(bucket["intervals"]) + 1
        raw_rain = row.get("rain")
        if raw_rain is None or str(raw_rain).strip() == "":
            bucket["unknown_intervals"] = int(bucket["unknown_intervals"]) + 1
        else:
            try:
                rain_cm = Decimal(str(raw_rain))
            except InvalidOperation as exc:
                raise ValueError(f"invalid rain value at {timestamp}") from exc
            bucket["known_mm"] = Decimal(bucket["known_mm"]) + rain_cm * 10
    return result
