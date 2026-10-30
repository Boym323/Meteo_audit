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


def july2022_dual_station_candidate(
    local_temp_c: float,
    ilouka4_temp_c: float,
    ilouka4_rh_pct: float,
    luhamet_rh_pct: float,
    *,
    max_reference_gap_pp: float = 3.0,
    max_temperature_gap_c: float = 1.5,
) -> float | None:
    """Conservative 2022-07 model v1, ESTIMATED_EXTERNAL only.

    It was applied *only* to qualifying early-July missing RH (UTC date
    2022-07-01 through 2022-07-05). Historical WH1080 RH is deliberately
    excluded: faulty sensor values were intentionally removed on migration.
    Validation MAE of qualifying points varies across July holdouts:
    about 4.2, 7.6, and 5.2 percentage points, not a measurement guarantee.
    Caller validates each source timestamp and that no duplicate reference
    observation maps to its five-minute slot.
    """
    from decimal import Decimal, ROUND_HALF_UP

    values = (local_temp_c, ilouka4_temp_c, ilouka4_rh_pct, luhamet_rh_pct)
    if not all(math.isfinite(x) for x in values):
        return None
    if not (-40 <= local_temp_c <= 45 and -40 <= ilouka4_temp_c <= 45):
        return None
    if not (1 <= ilouka4_rh_pct <= 100 and 1 <= luhamet_rh_pct <= 100):
        return None
    if not (0 < max_reference_gap_pp <= 6 and 0 < max_temperature_gap_c <= 3):
        raise ValueError("Candidate-gate thresholds outside validated July 2022 bounds")
    if abs(ilouka4_rh_pct - luhamet_rh_pct) > max_reference_gap_pp:
        return None
    if abs(ilouka4_temp_c - local_temp_c) > max_temperature_gap_c:
        return None
    candidate = max(1.0, min(100.0, 0.8 * ilouka4_rh_pct + 0.2 * luhamet_rh_pct - 3.5))
    return float(Decimal(str(candidate)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
