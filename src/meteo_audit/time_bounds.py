"""Shared WeeWX interval-end SQL predicates and local calendar-year boundaries.

A stored observation is the end of its archive interval. Intervals counted
within a period therefore use (start, end], not [start, end).
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

PRAGUE = ZoneInfo("Europe/Prague")


def local_year_bounds(year: int) -> tuple[int, int]:
    """UTC Unix timestamps for successive Prague-local year boundaries."""
    if not 1970 <= year < 2200:
        raise ValueError("Year must satisfy 1970 <= year < 2200")
    start = datetime(year, 1, 1, tzinfo=PRAGUE)
    end = datetime(year + 1, 1, 1, tzinfo=PRAGUE)
    return int(start.timestamp()), int(end.timestamp())


def archive_period_predicate(start_epoch: int, end_epoch: int) -> str:
    """Safe SQL predicate for archive.dateTime in (start_epoch, end_epoch].

    Accepts integers only, not user-provided SQL identifiers or expressions.
    """
    if type(start_epoch) is not int or type(end_epoch) is not int or start_epoch >= end_epoch:
        raise ValueError("Archive boundaries must be ordered integer Unix timestamps")
    return f"dateTime > {start_epoch} AND dateTime <= {end_epoch}"


def local_period_bounds(period: str) -> tuple[int, int]:
    """Return UTC epoch boundaries for YYYY-MM or YYYY local civil period."""
    parts=period.split("-")
    if len(parts)==1:
        year=int(parts[0]); start=date(year,1,1); stop=date(year+1,1,1)
    elif len(parts)==2:
        year,month=map(int,parts); start=date(year,month,1)
        stop=date(year+1,1,1) if month==12 else date(year,month+1,1)
    else: raise ValueError("Period must be YYYY or YYYY-MM")
    a=datetime.combine(start,time(),PRAGUE); b=datetime.combine(stop,time(),PRAGUE)
    return int(a.timestamp()),int(b.timestamp())


def interval_overlap_seconds(end_epoch: int, interval_seconds: int, period_start: int, period_end: int) -> int:
    """Civil-period overlap of a WeeWX interval whose timestamp is its end.

    WeeWX archives represent (end-interval, end]. Overlapping or irregular
    intervals are deliberately not deduplicated here; callers must detect and
    report them before calculating aggregate coverage.
    """
    values=(end_epoch,interval_seconds,period_start,period_end)
    if any(type(x) is not int for x in values) or interval_seconds<=0 or period_start>=period_end:
        raise ValueError("Expected integer epochs, positive interval, and ordered period bounds")
    start=end_epoch-interval_seconds
    return max(0,min(end_epoch,period_end)-max(start,period_start))


def interval_union_metrics(spans: list[tuple[int, int]]) -> dict[str, int]:
    """Measure interval union, duplicated overlap, and internal uncovered gaps.

    ``spans`` are half-open clipped epochs ``(start, end]``; endpoint
    convention does not affect duration. The union is always bounded by the
    input extents and therefore cannot exceed the evaluated period.
    """
    if any(type(a) is not int or type(b) is not int or a >= b for a, b in spans):
        raise ValueError("Every interval span must contain ordered integer epochs")
    if not spans:
        return {"covered_seconds": 0, "overlap_seconds": 0,
                "overlap_rows": 0, "internal_gap_seconds": 0,
                "gap_spans": [], "overlap_spans": []}
    ordered = sorted(spans)
    covered = overlap = overlap_rows = gaps = 0
    gap_spans=[];overlap_spans=[]
    left, right = ordered[0]
    for start, end in ordered[1:]:
        if start > right:
            covered += right - left
            gaps += start - right
            gap_spans.append((right,start))
            left, right = start, end
        else:
            if start < right:
                overlap_end=min(right,end)
                overlap += overlap_end - start
                overlap_rows += 1
                overlap_spans.append((start,overlap_end))
            right = max(right, end)
    covered += right - left
    return {"covered_seconds": covered, "overlap_seconds": overlap,
            "overlap_rows": overlap_rows, "internal_gap_seconds": gaps,
            "gap_spans": gap_spans, "overlap_spans": overlap_spans}
