"""Source-first correction gates. This module is local and never accesses a database."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable

@dataclass(frozen=True)
class SourceFirstDecision:
    status: str
    reason: str


def classify_before_estimate(*, source_checks_complete: bool,
                             sources: Iterable[dict[str, Any]],
                             target_row_exists: bool,
                             change_event_count: int | None,
                             exact_timestamp: bool = True) -> SourceFirstDecision:
    """Prevent an estimate whenever exact source data or an incomplete source audit exists.

    A source value is never automatically RESTORED: authenticated source role, unit/time
    semantics, target state and physical/context checks are separate gates.
    """
    source_list = list(sources)
    if not source_checks_complete:
        return SourceFirstDecision("REVIEW_REQUIRED", "not all relevant source archives checked")
    if not exact_timestamp:
        return SourceFirstDecision("REVIEW_REQUIRED", "source timestamp mapping is not exact/verified")
    if any(bool(s.get("historical_transformation_unresolved")) for s in source_list):
        return SourceFirstDecision("REVIEW_REQUIRED", "historical transformation is unresolved")
    if any(bool(s.get("historical_removal_suspected")) for s in source_list):
        return SourceFirstDecision("REVIEW_REQUIRED", "possible intentional historical removal requires review")
    if any(bool(s.get("source_row_exists")) for s in source_list):
        has_variable = any(s.get("value") is not None for s in source_list)
        reason = "exact source value exists; resolve RESTORED/source conflict before estimate" if has_variable else "source row exists; assess multi-variable row before estimate"
        return SourceFirstDecision("REVIEW_REQUIRED", reason)
    if target_row_exists:
        return SourceFirstDecision("REVIEW_REQUIRED", "target row exists; target field/state must be reconciled")
    if change_event_count is None:
        return SourceFirstDecision("REVIEW_REQUIRED", "change history was not checked")
    if change_event_count != 0:
        return SourceFirstDecision("REVIEW_REQUIRED", "target timestamp has change history")
    return SourceFirstDecision("ESTIMATED_ELIGIBLE_FOR_REVIEW", "all exact source archives empty; no target row/history; other model gates still apply")


def restored_gate(*, original_identity: bool, source_role_verified: bool,
                  timestamp_verified: bool, unit_verified: bool,
                  expected_target_state_verified: bool, history_checked: bool,
                  context_checked: bool, anomaly_screen_passed: bool,
                  uncertainty_documented: bool,
                  historical_transformation_resolved: bool = False,
                  historical_removal_screen_passed: bool = False) -> SourceFirstDecision:
    """A candidate is a RESTORED proposal only when all mandatory gates pass."""
    gates = [original_identity, source_role_verified, timestamp_verified, unit_verified,
             expected_target_state_verified, history_checked, context_checked,
             anomaly_screen_passed, uncertainty_documented,
             historical_transformation_resolved, historical_removal_screen_passed]
    if all(gates):
        return SourceFirstDecision("RESTORED_ELIGIBLE_FOR_REVIEW", "all required provenance and row gates passed")
    return SourceFirstDecision("REVIEW_REQUIRED", "one or more identity/provenance/context gates are unverified")


def validate_dependency_order(operations: Iterable[dict[str, Any]]) -> None:
    """Require a whole-row insert before field updates on a previously absent row.

    This validates proposal ordering only; it performs no database operation.
    A whole-row operation uses operation='insert_row', variable='__row__'. A later
    field operation against an absent starting row declares expected_row_state='ABSENT'.
    """
    seen_row_insert: set[int] = set()
    for op in operations:
        timestamp = int(op['timestamp'])
        if op.get('operation') == 'insert_row' and op.get('variable') == '__row__':
            seen_row_insert.add(timestamp)
            continue
        if op.get('expected_row_state') == 'ABSENT' and op.get('operation') in ('update', 'set_field'):
            if timestamp not in seen_row_insert:
                raise ValueError(f'field operation precedes whole-row insert at {timestamp}')
