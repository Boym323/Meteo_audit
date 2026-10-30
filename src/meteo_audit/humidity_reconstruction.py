"""Humidity reconstruction helpers: produce candidates, never write weather data.

The astronomical/local observation date is not inferred from MariaDB's
session timezone. Caller supplies UTC epoch seconds and validates lineage.
Every output is an ESTIMATE, never an observed measurement.
"""
from __future__ import annotations

import math


def saturation_factor(temp_c: float) -> float:
    """Unitless Magnus saturation vapor-pressure factor over water.

    The factor 6.112 hPa cancels when transferring relative humidity.
    This is a candidate model, NOT a WeeWX historical algorithm fingerprint.
    """
    if not math.isfinite(temp_c) or not -40 <= temp_c <= 45:
        raise ValueError("Temperature outside the validated candidate domain")
    return math.exp(17.62 * temp_c / (243.12 + temp_c))


def reference_humidity_candidate(
    local_temp_c: float,
    reference_temp_c: float,
    reference_rh_pct: float,
) -> float:
    """Transfer reference vapor pressure to local temperature.

    Needs independent source QC and holdout validation. A plausible physical
    result does not establish a true local sensor measurement.
    """
    if not math.isfinite(reference_rh_pct) or not 1 <= reference_rh_pct <= 100:
        raise ValueError("Invalid reference relative humidity")
    result = reference_rh_pct * saturation_factor(reference_temp_c) / saturation_factor(local_temp_c)
    return min(100.0, max(1.0, result))


def short_gap_candidate(
    target_epoch: int,
    before_epoch: int,
    before_rh_pct: float,
    after_epoch: int,
    after_rh_pct: float,
    *,
    max_span_seconds: int = 1800,
    max_endpoint_difference_pp: float = 3.0,
) -> float | None:
    """Interpolate only a bounded gap with two validated LOCAL anchor readings.

    The caller MUST verify anchors are not frozen/corrupted, have true UTC
    timestamps, are not themselves modeled, and that independent weather
    evidence does not indicate a front or abrupt transition. Returns None
    when not safe enough even to propose.
    """
    if not isinstance(target_epoch, int) or not isinstance(before_epoch, int) or not isinstance(after_epoch, int):
        return None
    span = after_epoch - before_epoch
    if not (0 < target_epoch - before_epoch < span <= max_span_seconds):
        return None
    if target_epoch % 300 != 0 or before_epoch % 300 != 0 or after_epoch % 300 != 0:
        return None
    if not all(math.isfinite(x) and 1 <= x <= 100 for x in (before_rh_pct, after_rh_pct)):
        return None
    if abs(after_rh_pct - before_rh_pct) > max_endpoint_difference_pp:
        return None
    return before_rh_pct + (after_rh_pct - before_rh_pct) * (target_epoch - before_epoch) / span
