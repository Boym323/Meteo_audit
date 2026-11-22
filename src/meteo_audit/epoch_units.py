"""Fail-closed historical unit conversions, never writes or reads a database."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


class UnresolvedUnitEpoch(ValueError):
    """Physical units or source epoch are not verified."""


@dataclass(frozen=True)
class UnitEpoch:
    """Verified physical semantics for archive end timestamps in [start, end)."""
    source: str
    start_utc: int
    end_utc: int
    us_units: int
    wind_numeric_unit: str
    rain_semantics: str
    evidence_ref: str = ""
    verified: bool = False

    def __post_init__(self):
        if not isinstance(self.source, str) or not self.source.strip():
            raise UnresolvedUnitEpoch("source identity missing")
        if (type(self.start_utc) is not int or type(self.end_utc) is not int
                or self.start_utc < 0 or self.start_utc >= self.end_utc):
            raise UnresolvedUnitEpoch("invalid UTC epoch boundaries")
        if type(self.us_units) is not int or self.us_units not in (16, 17):
            raise UnresolvedUnitEpoch("unsupported usUnits")
        if self.wind_numeric_unit not in ("km/h", "m/s", "UNRESOLVED"):
            raise UnresolvedUnitEpoch("unsupported wind numeric unit")
        if self.rain_semantics not in (
                "interval_mm", "interval_cm", "counter_mm", "counter_cm", "UNRESOLVED"):
            raise UnresolvedUnitEpoch("unsupported rain semantics")
        if type(self.verified) is not bool:
            raise UnresolvedUnitEpoch("verified must be boolean")
        if self.verified and (not isinstance(self.evidence_ref, str)
                              or not self.evidence_ref.strip()):
            raise UnresolvedUnitEpoch("verified epoch needs evidence reference")


def resolve_epoch(epochs: Iterable[UnitEpoch], *, source: str,
                  end_time_utc: int, us_units: int) -> UnitEpoch:
    """Require exactly one verified physical source epoch."""
    if type(end_time_utc) is not int or end_time_utc < 0:
        raise UnresolvedUnitEpoch("invalid archive end timestamp")
    if type(us_units) is not int or us_units not in (16, 17):
        raise UnresolvedUnitEpoch("unsupported record usUnits")
    matches = [e for e in epochs
               if e.source == source and e.start_utc <= end_time_utc < e.end_utc]
    if len(matches) != 1:
        raise UnresolvedUnitEpoch("source epoch missing or ambiguous")
    epoch = matches[0]
    if epoch.us_units != us_units:
        raise UnresolvedUnitEpoch("record usUnits differs from source epoch")
    if not epoch.verified:
        raise UnresolvedUnitEpoch("epoch not verified by original evidence")
    return epoch


def _measurement(value: int | float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UnresolvedUnitEpoch("not a numerical measurement")
    n = float(value)
    if not isfinite(n) or n < 0:
        raise UnresolvedUnitEpoch("negative or nonfinite sensor value")
    return n


def wind_speed_kmh(value: int | float | None, *, source: str, end_time_utc: int,
                   us_units: int, epochs: Iterable[UnitEpoch]) -> float | None:
    """Never infer a wind conversion from usUnits alone."""
    if value is None:
        return None
    n = _measurement(value)
    epoch = resolve_epoch(epochs, source=source, end_time_utc=end_time_utc,
                          us_units=us_units)
    if epoch.wind_numeric_unit == "km/h":
        return n
    if epoch.wind_numeric_unit == "m/s":
        return n * 3.6
    raise UnresolvedUnitEpoch("unresolved historical wind numeric unit")


def rain_interval_cm(value: int | float | None, *, source: str, end_time_utc: int,
                     us_units: int, epochs: Iterable[UnitEpoch]) -> float | None:
    """Convert verified interval rain, never counters or rainRate."""
    if value is None:
        return None
    n = _measurement(value)
    epoch = resolve_epoch(epochs, source=source, end_time_utc=end_time_utc,
                          us_units=us_units)
    if epoch.rain_semantics == "interval_mm":
        return n / 10
    if epoch.rain_semantics == "interval_cm":
        return n
    raise UnresolvedUnitEpoch("rain counter or unresolved interval semantics")
