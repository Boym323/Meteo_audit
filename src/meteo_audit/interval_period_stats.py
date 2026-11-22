"""Small, conservative time-weighted summaries for interval-end archive data."""
from __future__ import annotations

from decimal import Decimal
from typing import Iterable


def summarize_clipped_nonoverlapping(
    intervals: Iterable[tuple[int, int, str]], period_start: int, period_end: int
) -> dict:
    """Clip (start,end,value) spans to a period and exclude overlapping spans.

    Archive rows are ordered by end time. If a candidate span intersects any
    already-retained span, exclude that candidate wholesale rather than
    inventing a sub-interval allocation for its aggregate value.
    """
    retained: list[tuple[int, int, Decimal]] = []
    overlap_excluded = invalid = clipped = 0
    for start, end, value in sorted(intervals, key=lambda x: (x[1], x[0])):
        if end <= start:
            invalid += 1
            continue
        lo, hi = max(start, period_start), min(end, period_end)
        if lo >= hi:
            continue
        if lo != start or hi != end:
            clipped += 1
        # End times are monotone in the sorted iteration, so only the most
        # recently retained interval can be the first retained overlap.
        if retained and lo < retained[-1][1]:
            overlap_excluded += 1
            continue
        retained.append((lo, hi, Decimal(value)))
    retained.sort()
    covered = sum(hi - lo for lo, hi, _ in retained)
    weighted_sum = sum((Decimal(hi - lo) * value for lo, hi, value in retained), Decimal(0))
    gaps = []
    cursor = period_start
    for lo, hi, _ in retained:
        if lo > cursor:
            gaps.append((cursor, lo))
        cursor = max(cursor, hi)
    if cursor < period_end:
        gaps.append((cursor, period_end))
    duration = period_end - period_start
    return {
        "period_seconds": duration,
        "covered_seconds": covered,
        "time_coverage": covered / duration if duration else 0.0,
        "weighted_mean": str(weighted_sum / covered) if covered else None,
        "overlap_excluded_intervals": overlap_excluded,
        "invalid_intervals": invalid,
        "clipped_intervals": clipped,
        "longest_gap_seconds": max((b - a for a, b in gaps), default=0),
        "gap_count": len(gaps),
    }
