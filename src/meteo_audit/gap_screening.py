"""Build bounded read-only SQL for annual archive-gap screening."""
from __future__ import annotations

from datetime import datetime, timezone

from .db import quote_database

UTC = timezone.utc


def utc_year_bounds(year: int) -> tuple[int, int]:
    if type(year) is not int or not 1970 <= year < 2200:
        raise ValueError("year must be in [1970, 2199]")
    start = int(datetime(year, 1, 1, tzinfo=UTC).timestamp())
    end = int(datetime(year + 1, 1, 1, tzinfo=UTC).timestamp())
    return start, end


def annual_gap_screening_sql(database: str, year: int) -> str:
    """Return aggregate-only SQL; query client still enforces SELECT-only."""
    schema = quote_database(database)
    start, end = utc_year_bounds(year)
    return (
        "SELECT prev_interval, current_interval, COUNT(*) gap_events, "
        "SUM(delta_seconds > prev_interval*60 AND delta_seconds > current_interval*60) exceeds_both_steps, "
        "SUM(delta_seconds <> prev_interval*60 AND delta_seconds <> current_interval*60) matches_neither_step, "
        "MAX(delta_seconds) max_delta_seconds FROM ("
        "SELECT dateTime, current_interval, "
        "LAG(dateTime) OVER (ORDER BY dateTime) prev_ts, "
        "LAG(current_interval) OVER (ORDER BY dateTime) prev_interval, "
        "dateTime-LAG(dateTime) OVER (ORDER BY dateTime) delta_seconds "
        "FROM ("
        f"SELECT dateTime, `interval` current_interval FROM (SELECT dateTime, `interval` "
        f"FROM {schema}.`archive` WHERE dateTime < {start} ORDER BY dateTime DESC LIMIT 1) predecessor "
        "UNION ALL "
        f"SELECT dateTime, `interval` current_interval FROM {schema}.`archive` "
        f"WHERE dateTime >= {start} AND dateTime < {end}"
        ") year_rows"
        ") adjacent WHERE prev_ts IS NOT NULL "
        f"AND dateTime >= {start} "
        "AND delta_seconds > LEAST(prev_interval,current_interval)*60 "
        "GROUP BY prev_interval,current_interval ORDER BY prev_interval,current_interval"
    )
