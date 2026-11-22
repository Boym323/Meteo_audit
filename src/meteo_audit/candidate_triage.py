"""Fail-closed classification of legacy pending reconstruction candidates.

A staged proposal is NOT an approved archive correction. This pure module has
no database/network access and NEVER authorizes new writes. In particular,
historical review flags and already-applied proposals are not to be replayed.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from numbers import Real


class UnsafePendingCandidate(ValueError):
    """Malformed or ambiguous candidate metadata."""


@dataclass(frozen=True)
class PendingCandidateState:
    variable: str
    target_time_utc: int
    proposed_value: float | None
    target_exists: bool
    current_value: float | None
    matching_applied_change_count: int
    independent_source_validated: bool = False
    backup_restore_verified: bool = False
    explicit_batch_approval: bool = False
    physical_source_conflict: bool = False

    def __post_init__(self) -> None:
        if not self.variable or not isinstance(self.variable, str):
            raise UnsafePendingCandidate("variable required")
        if type(self.target_time_utc) is not int or self.target_time_utc <= 0:
            raise UnsafePendingCandidate("UTC end timestamp required")
        if type(self.target_exists) is not bool:
            raise UnsafePendingCandidate("target_exists must be boolean")
        if type(self.matching_applied_change_count) is not int or self.matching_applied_change_count < 0:
            raise UnsafePendingCandidate("invalid applied change count")
        for name in ("independent_source_validated", "backup_restore_verified",
                     "explicit_batch_approval", "physical_source_conflict"):
            if type(getattr(self, name)) is not bool:
                raise UnsafePendingCandidate(name + " must be boolean")
        for value in (self.proposed_value, self.current_value):
            if value is not None and (
                not isinstance(value, Real) or isinstance(value, bool)
                or not isfinite(float(value))
            ):
                raise UnsafePendingCandidate("non-finite or non-numeric value")
        if not self.target_exists and self.current_value is not None:
            raise UnsafePendingCandidate("missing target cannot hold a value")


def disposition(c: PendingCandidateState) -> str:
    """One safe review status; never returns APPROVED/EXECUTE/APPLY."""
    if c.proposed_value is None:
        return "REVIEW_FLAG_NO_NUMERIC_PROPOSAL"

    # Exact (including numeric zero), not tolerance-matched, applied audit.
    if c.target_exists and c.current_value == c.proposed_value and c.matching_applied_change_count > 0:
        return "ALREADY_APPLIED_NO_REPEAT"

    if c.physical_source_conflict:
        return "HOLD_SOURCE_CONFLICT"

    if not c.target_exists:
        return "HOLD_MISSING_TARGET_UNVERIFIED"

    if c.matching_applied_change_count > 0:
        return "HOLD_EXISTING_AUDIT_CONFLICT"

    if not c.independent_source_validated:
        return "HOLD_SOURCE_NOT_INDEPENDENTLY_VERIFIED"

    if not c.backup_restore_verified:
        return "HOLD_BACKUP_RESTORE_NOT_VERIFIED"

    if not c.explicit_batch_approval:
        return "HOLD_BATCH_NOT_EXPLICITLY_APPROVED"

    # Any real approval requires separate hash-pinned transactional integration
    # in a controlled DB adapter, which intentionally is not in this module.
    return "REVIEW_READY_FOR_SEPARATE_TRANSACTIONAL_PREFLIGHT"


def summary(states: list[PendingCandidateState]) -> dict[str, int]:
    """Aggregates safe dispositions, never returning value-level data."""
    result: dict[str, int] = {}
    for state in states:
        category = disposition(state)
        result[category] = result.get(category, 0) + 1
    return dict(sorted(result.items()))
