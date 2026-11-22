"""Pure, fail-closed reconstruction approval simulation (issue #26).

NO database adapters, connections, mutating SQL or automatic approval. This
module models preflight, immutable before-image, null-safe CAS, one-batch
approval and rollback for test snapshots; real DB apply is intentionally absent.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from numbers import Real
from typing import Mapping

from .archive_sync import VALUE_FIELDS


class PreflightError(ValueError):
    """Unsafe or insufficiently evidenced correction; no changes applied."""


PROTECTED_UTC_RANGES = (
    (1514764800, 1522540800, None),  # 2018 Q1: ALL variables
    (1609459200, 1640995200, frozenset({"rain", "rainRate"})),  # 2021 rainfall
)


def _valid_number(value: object) -> bool:
    return value is None or (
        isinstance(value, Real) and not isinstance(value, bool)
        and isfinite(float(value))
    )


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class FieldCorrection:
    target_time_utc: int
    variable: str
    expected_old: float | None
    proposed_new: float | None
    source_ref: str
    unit_epoch_ref: str
    rule_version: str
    diagnosis_confidence: str
    replacement_confidence: str

    def __post_init__(self):
        if type(self.target_time_utc) is not int or self.target_time_utc <= 0:
            raise PreflightError("invalid target_time_utc")
        if self.variable not in VALUE_FIELDS:
            raise PreflightError("variable not in approved archive value fields")
        for value in (self.expected_old, self.proposed_new):
            if not _valid_number(value):
                raise PreflightError("old/new value must be finite numeric or NULL")
        if self.expected_old == self.proposed_new:
            raise PreflightError("no-op correction is not a proposal")
        for name in ("source_ref", "unit_epoch_ref", "rule_version"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise PreflightError("missing " + name)
        for name in ("diagnosis_confidence", "replacement_confidence"):
            if getattr(self, name) not in {"LOW", "MEDIUM", "HIGH", "UNRESOLVED"}:
                raise PreflightError("invalid confidence")
        for lo, hi, fields in PROTECTED_UTC_RANGES:
            if lo <= self.target_time_utc < hi and (
                fields is None or self.variable in fields
            ):
                raise PreflightError("historical period/field protected; requires separate authority")

    @property
    def key(self) -> tuple[int, str]:
        return (self.target_time_utc, self.variable)


@dataclass(frozen=True)
class CandidateBatch:
    batch_id: str
    operations: tuple[FieldCorrection, ...]
    schema: str = "loucka-field-correction-review-v1"
    target: str = "loucka_reconstruction.archive"

    def __post_init__(self):
        if self.schema != "loucka-field-correction-review-v1" or self.target != "loucka_reconstruction.archive":
            raise PreflightError("correction batch target or schema not allowed")
        if not isinstance(self.batch_id, str) or not self.batch_id.strip():
            raise PreflightError("batch_id required")
        if type(self.operations) is not tuple or not self.operations:
            raise PreflightError("non-empty immutable operation tuple required")
        keys = [op.key for op in self.operations]
        if len(set(keys)) != len(keys):
            raise PreflightError("duplicate target_time_utc/variable in batch")
        if any(not isinstance(op, FieldCorrection) for op in self.operations):
            raise PreflightError("batch contains unvalidated operation")

    @property
    def payload_sha256(self) -> str:
        return _digest({
            "schema": self.schema,
            "target": self.target,
            "batch_id": self.batch_id,
            "operations": [asdict(op) for op in self.operations],
        })


@dataclass(frozen=True)
class BatchApproval:
    """Simulated explicit exact-payload approval, not a DB trust signature."""
    batch_id: str
    payload_sha256: str
    approval_ref: str


@dataclass(frozen=True)
class SimulatedCommit:
    batch_id: str
    payload_sha256: str
    before_image_sha256: str
    approval_ref: str
    affected_keys: tuple[tuple[int, str], ...]


def preflight(
    batch: CandidateBatch,
    snapshot: Mapping[tuple[int, str], float | None],
    *,
    changed_keys: frozenset[tuple[int, str]] = frozenset(),
) -> dict:
    """Read-only exact-old CAS eligibility (never authorizes an actual apply)."""
    before_image = []
    for op in batch.operations:
        if op.key not in snapshot:
            raise PreflightError("target timestamp/field absent from selected snapshot")
        if op.key in changed_keys:
            raise PreflightError("target already has reconstruction change history")
        observed = snapshot[op.key]
        if not _valid_number(observed):
            raise PreflightError("current target value is invalid")
        if observed != op.expected_old:  # Python None vs 0 models SQL NULL-safe <=>
            raise PreflightError("old value mismatch; CAS would fail")
        before_image.append({
            "target_time_utc": op.target_time_utc,
            "variable": op.variable,
            "old": observed,
        })
    return {
        "status": "READY_FOR_EXPLICIT_APPROVAL_NOT_APPLIED",
        "batch_id": batch.batch_id,
        "target": batch.target,
        "operation_count": len(batch.operations),
        "payload_sha256": batch.payload_sha256,
        "before_image_sha256": _digest(before_image),
        "before_image": before_image,
        "db_writes": 0,
    }


def simulate_atomic_apply(
    batch: CandidateBatch,
    snapshot: Mapping[tuple[int, str], float | None],
    approval: BatchApproval,
    *,
    changed_keys: frozenset[tuple[int, str]] = frozenset(),
) -> tuple[dict[tuple[int, str], float | None], SimulatedCommit]:
    """Atomic copy-only test of an exact-value approved apply.

    This never writes any database. The caller must NOT adapt it as SQL without
    separate DB-transaction integration tests and owner approval.
    """
    if (approval.batch_id != batch.batch_id
            or approval.payload_sha256 != batch.payload_sha256
            or not isinstance(approval.approval_ref, str)
            or not approval.approval_ref.strip()):
        raise PreflightError("approval does not match exact batch/payload")
    report = preflight(batch, snapshot, changed_keys=changed_keys)
    updated = dict(snapshot)
    for op in batch.operations:
        updated[op.key] = op.proposed_new
    evidence = SimulatedCommit(
        batch.batch_id, batch.payload_sha256,
        report["before_image_sha256"], approval.approval_ref,
        tuple(op.key for op in batch.operations),
    )
    return updated, evidence


def simulate_atomic_rollback(
    batch: CandidateBatch,
    current: Mapping[tuple[int, str], float | None],
    commit: SimulatedCommit,
    before_image: list[dict],
) -> dict[tuple[int, str], float | None]:
    """Copy-only rollback under post-image CAS and immutable before-image digest."""
    if (commit.batch_id != batch.batch_id
            or commit.payload_sha256 != batch.payload_sha256
            or commit.affected_keys != tuple(op.key for op in batch.operations)
            or commit.before_image_sha256 != _digest(before_image)):
        raise PreflightError("rollback history/before-image identity mismatch")
    old_by_key = {}
    for record in before_image:
        key = (record.get("target_time_utc"), record.get("variable"))
        if key in old_by_key or key not in commit.affected_keys:
            raise PreflightError("rollback before-image contains duplicate or foreign key")
        old_by_key[key] = record.get("old")
    if set(old_by_key) != set(commit.affected_keys):
        raise PreflightError("rollback before-image incomplete")
    for op in batch.operations:
        if (op.key not in current or current[op.key] != op.proposed_new
                or old_by_key[op.key] != op.expected_old):
            raise PreflightError("rollback post-image CAS mismatch")
    result = dict(current)
    for op in batch.operations:
        result[op.key] = old_by_key[op.key]
    return result
