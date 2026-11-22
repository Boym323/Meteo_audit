"""Read-only per-field observation-quality API contract (issue #25).

This is pure data validation and serialization; not a database migration,
meteorological truth assessment, or permission to publish historical values.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone, timedelta
from math import isfinite
from numbers import Real
from re import fullmatch
from zoneinfo import ZoneInfo

STATES = frozenset({
    "MEASURED", "CORRECTED", "ESTIMATED", "MISSING",
    "NOT_INSTALLED", "SENSOR_ERROR",
})
CONFIDENCE = frozenset({"UNRESOLVED", "LOW", "MEDIUM", "HIGH"})
PRAGUE = ZoneInfo("Europe/Prague")


class QualityContractError(ValueError):
    """Malformed or unproven observation metadata; reject rather than invent."""


@dataclass(frozen=True)
class FieldObservation:
    timestamp_utc: int
    variable: str
    state: str
    measurement_value: float | None
    display_value: float | None
    unit: str
    source_ref: str | None = None
    epoch_ref: str | None = None
    change_ref: str | None = None
    approved: bool = False
    independent_validation: bool = False
    diagnosis_confidence: str = "UNRESOLVED"
    replacement_confidence: str = "UNRESOLVED"
    qc_flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.timestamp_utc) is not int or self.timestamp_utc < 0:
            raise QualityContractError("timestamp_utc must be a UTC integer")
        if not isinstance(self.variable, str) or not fullmatch(r"[A-Za-z][A-Za-z0-9_]*", self.variable):
            raise QualityContractError("invalid variable")
        if self.state not in STATES:
            raise QualityContractError("unsupported quality state")
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise QualityContractError("unit must be documented")
        for field in ("measurement_value", "display_value"):
            value = getattr(self, field)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, Real)
                or not isfinite(float(value))
            ):
                raise QualityContractError(field + " must be a finite number or NULL")
        if self.diagnosis_confidence not in CONFIDENCE or self.replacement_confidence not in CONFIDENCE:
            raise QualityContractError("invalid confidence")
        if type(self.approved) is not bool or type(self.independent_validation) is not bool:
            raise QualityContractError("approval and validation must be boolean")
        if (not isinstance(self.qc_flags, tuple)
                or any(not isinstance(x, str) or not fullmatch(r"[A-Z][A-Z0-9_]*", x)
                       for x in self.qc_flags)
                or len(set(self.qc_flags)) != len(self.qc_flags)):
            raise QualityContractError("invalid or duplicate quality flag")
        if self.state in {"MISSING", "NOT_INSTALLED", "SENSOR_ERROR"}:
            if self.display_value is not None:
                raise QualityContractError("non-displayable state cannot have display value")
            if self.approved:
                raise QualityContractError("a missing/fault state cannot be marked approved")
        else:
            if self.display_value is None or self.measurement_value is None:
                raise QualityContractError("numeric quality state requires explicit values")
            if not self.source_ref or not self.epoch_ref:
                raise QualityContractError("numeric observation requires source and sensor epoch provenance")
        if self.state in {"CORRECTED", "ESTIMATED"}:
            if not self.change_ref or not self.approved:
                raise QualityContractError("correction or estimate requires an approved change reference")
        if self.state == "MEASURED" and self.change_ref:
            raise QualityContractError("measured value cannot claim reconstruction history")
        if self.state == "NOT_INSTALLED" and not self.epoch_ref:
            raise QualityContractError("NOT_INSTALLED requires installation-epoch evidence")
        if self.state in {"MISSING", "SENSOR_ERROR"} and not self.qc_flags:
            raise QualityContractError("missing or fault state requires an explicit quality reason")

    @property
    def extrema_eligible(self) -> bool:
        """Strict-by-default statistical policy, not evidence of physical truth."""
        return (
            self.state == "MEASURED"
            and self.independent_validation
            and not self.qc_flags
        )

    @property
    def join_chart_line(self) -> bool:
        """Never imply interpolation across missing, faulty, or estimated values."""
        return self.state in {"MEASURED", "CORRECTED"} and self.display_value is not None


def serialize_field(record: FieldObservation) -> dict:
    """Lossless QC distinction for a single field of an archive timestamp."""
    timestamp = datetime.fromtimestamp(record.timestamp_utc, tz=timezone.utc)
    local = timestamp.astimezone(PRAGUE)
    return {
        "schema": "loucka-field-qc-v1",
        "timestamp_utc": record.timestamp_utc,
        "local_end_iso": local.isoformat(),
        "local_fold": local.fold,
        "variable": record.variable,
        "unit": record.unit,
        "state": record.state,
        "measurement_value": record.measurement_value,
        "display_value": record.display_value,
        "source_ref": record.source_ref,
        "epoch_ref": record.epoch_ref,
        "change_ref": record.change_ref,
        "approved": record.approved,
        "diagnosis_confidence": record.diagnosis_confidence,
        "replacement_confidence": record.replacement_confidence,
        "qc_flags": list(record.qc_flags),
        "extrema_eligible": record.extrema_eligible,
        "join_chart_line": record.join_chart_line,
    }


def civil_day_bounds(local_day: date, zone: ZoneInfo = PRAGUE) -> tuple[int, int]:
    """Return UTC WeeWX archive-end boundaries (local midnight, next midnight].

    Caller uses timestamp > lower AND timestamp <= upper. DST days are 23/25h.
    """
    if type(local_day) is not date:
        raise QualityContractError("local_day must be a date")
    start = datetime.combine(local_day, time.min, tzinfo=zone)
    end = datetime.combine(local_day + timedelta(days=1), time.min, tzinfo=zone)
    return (
        int(start.astimezone(timezone.utc).timestamp()),
        int(end.astimezone(timezone.utc).timestamp()),
    )


def belongs_to_civil_day(end_time_utc: int, local_day: date) -> bool:
    """WeeWX intervals end at dateTime; midnight belongs to previous day."""
    if type(end_time_utc) is not int:
        raise QualityContractError("end_time_utc must be a UTC epoch")
    lower, upper = civil_day_bounds(local_day)
    return lower < end_time_utc <= upper
