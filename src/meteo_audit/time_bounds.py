"""Shared WeeWX interval-end SQL predicates and local calendar-year boundaries.

A stored observation is the end of its archive interval. Intervals counted
within a period therefore use (start, end], not [start, end).
"""
from __future__ import annotations

from datetime import datetime
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
