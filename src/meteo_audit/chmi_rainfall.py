"""Read-only aggregation helpers for CHMI 10-minute precipitation CSVs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo


def summarize_chmi_10min(
    rows: Iterable[Mapping[str, object]],
    start_exclusive: int,
    end_inclusive: int,
    timezone_name: str = "Europe/Prague",
) -> dict[tuple[str, date], dict[str, Decimal | int]]:
    """Sum quality-zero SRA10M readings by local interval-end day.

    CHMI timestamps are UTC interval ends. A sample ending exactly at local
    midnight belongs to the preceding local day, so each day uses
    (midnight, next midnight]. Nonzero quality, flags, or missing values are
    counted as rejected and are never treated as zero.
    """
    if start_exclusive >= end_inclusive:
        raise ValueError("start_exclusive must precede end_inclusive")
    zone = ZoneInfo(timezone_name)
    start_utc = datetime.fromtimestamp(start_exclusive, tz=timezone.utc)
    end_utc = datetime.fromtimestamp(end_inclusive, tz=timezone.utc)
    seen: set[tuple[str, int]] = set()
    result: dict[tuple[str, date], dict[str, Decimal | int]] = {}

    for row in rows:
        if str(row.get("ELEMENT", "")).strip() != "SRA10M":
            continue
        station = str(row.get("STATION", "")).strip()
        if not station:
            raise ValueError("SRA10M row has no STATION")
        raw_dt = str(row.get("DT", "")).strip()
        try:
            observed_utc = datetime.fromisoformat(raw_dt.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"invalid CHMI DT {raw_dt!r}") from exc
        if observed_utc.utcoffset() is None:
            raise ValueError(f"CHMI DT must include a UTC offset: {raw_dt!r}")
        observed_utc = observed_utc.astimezone(timezone.utc)
        if not start_utc < observed_utc <= end_utc:
            continue

        epoch = int(observed_utc.timestamp())
        identity = (station, epoch)
        if identity in seen:
            raise ValueError(f"duplicate SRA10M row for {station} at {raw_dt}")
        seen.add(identity)

        local_end = observed_utc.astimezone(zone)
        local_day = (local_end - timedelta(microseconds=1)).date()
        bucket = result.setdefault(
            (station, local_day),
            {
                "recorded_intervals": 0,
                "valid_intervals": 0,
                "rejected_intervals": 0,
                "valid_mm": Decimal("0"),
            },
        )
        bucket["recorded_intervals"] = int(bucket["recorded_intervals"]) + 1

        raw_value = row.get("VALUE")
        raw_quality = row.get("QUALITY")
        raw_flag = str(row.get("FLAG", "")).strip()
        try:
            value = Decimal(str(raw_value).strip())
            quality = Decimal(str(raw_quality).strip())
        except (InvalidOperation, AttributeError):
            value = Decimal("NaN")
            quality = Decimal("NaN")
        if raw_flag or quality != Decimal("0") or not value.is_finite() or value < 0:
            bucket["rejected_intervals"] = int(bucket["rejected_intervals"]) + 1
            continue
        bucket["valid_intervals"] = int(bucket["valid_intervals"]) + 1
        bucket["valid_mm"] = Decimal(bucket["valid_mm"]) + value

    return result
