"""Offline atomic simulator for future correction packages.

This module never connects to a database. Its transaction and idempotency
behavior are local simulation policies, not claims about DB rollback behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence


class SimulationConflict(ValueError):
    """A package does not match its expected local snapshot or source evidence."""


@dataclass(frozen=True)
class ArchiveRow:
    us_units: int
    interval_minutes: int
    fields: Mapping[str, float | None]


@dataclass(frozen=True)
class Correction:
    operation: str
    timestamp: int
    variable: str
    new_value: float | None
    expected_old_value: float | None
    source_database: str
    source_time: int
    source_value: float | None
    reason: str
    us_units: int | None = None
    interval_minutes: int | None = None


@dataclass(frozen=True)
class BatchResult:
    batch_id: str
    payload_sha256: str
    status: str
    input_rows: Mapping[int, ArchiveRow]
    output_rows: Mapping[int, ArchiveRow]
    before_stats: Mapping[str, Mapping[str, float | int]]
    after_stats: Mapping[str, Mapping[str, float | int]]
    applied_operations: int


def _same_value(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-9)


def _copy_rows(rows: Mapping[int, ArchiveRow]) -> dict[int, ArchiveRow]:
    return {
        timestamp: ArchiveRow(
            us_units=row.us_units,
            interval_minutes=row.interval_minutes,
            fields=dict(row.fields),
        )
        for timestamp, row in rows.items()
    }


def _stats(rows: Mapping[int, ArchiveRow], schema_columns: Sequence[str]) -> dict[str, dict[str, float | int]]:
    output: dict[str, dict[str, float | int]] = {}
    for variable in schema_columns:
        values = [row.fields.get(variable) for row in rows.values()]
        present = [float(value) for value in values if value is not None]
        output[variable] = {
            "row_count": len(values),
            "nonnull_count": len(present),
            "null_count": len(values) - len(present),
            "sum": sum(present),
            "min": min(present) if present else 0.0,
            "max": max(present) if present else 0.0,
        }
    return output


def _payload_hash(corrections: Sequence[Correction]) -> str:
    encoded = json.dumps(
        [asdict(item) for item in corrections], sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def simulate_batch(
    rows: Mapping[int, ArchiveRow],
    corrections: Sequence[Correction],
    source_values: Mapping[tuple[str, int, str], float | None],
    schema_columns: Sequence[str],
    *,
    batch_id: str,
    prior_batches: Mapping[str, str] | None = None,
    fail_after: int | None = None,
) -> tuple[BatchResult, dict[str, str]]:
    """Apply a package to an in-memory copy or return an idempotent no-op.

    Any validation or injected mid-batch failure raises before the caller's
    archive mapping or batch ledger is modified. Insert + following updates
    for one new timestamp are modeled as a single ordered atomic package.
    """
    if not batch_id:
        raise SimulationConflict("batch_id must be non-empty and stable")
    if not corrections or len(corrections) > 50:
        raise SimulationConflict("batch must contain between 1 and 50 corrections")
    payload_digest = _payload_hash(corrections)
    ledger = dict(prior_batches or {})
    if batch_id in ledger:
        if ledger[batch_id] != payload_digest:
            raise SimulationConflict("stable batch_id was already used with different content")
        snapshot = _copy_rows(rows)
        stats = _stats(snapshot, schema_columns)
        return BatchResult(batch_id, payload_digest, "idempotent_noop", snapshot,
                           snapshot, stats, stats, 0), ledger

    seen: set[tuple[int, str]] = set()
    for correction in corrections:
        key = (correction.timestamp, correction.variable)
        if key in seen:
            raise SimulationConflict(f"duplicate target in batch: {key}")
        seen.add(key)
        if correction.operation not in ("insert", "update"):
            raise SimulationConflict(f"unsupported operation: {correction.operation}")
        if correction.timestamp < 0 or correction.source_time < 0:
            raise SimulationConflict("timestamps must be non-negative Unix seconds")
        if correction.variable not in schema_columns:
            raise SimulationConflict(f"unknown archive variable: {correction.variable}")
        if not correction.reason.strip() or not correction.source_database.strip():
            raise SimulationConflict("source_database and reason are required")
        source_key = (correction.source_database, correction.source_time, correction.variable)
        if source_key not in source_values:
            raise SimulationConflict(f"source observation is absent: {source_key}")
        if not _same_value(source_values[source_key], correction.source_value):
            raise SimulationConflict(f"source_value differs from local source row: {source_key}")

    before = _copy_rows(rows)
    working = _copy_rows(rows)
    before_stats = _stats(before, schema_columns)
    applied = 0
    for correction in corrections:
        row = working.get(correction.timestamp)
        if correction.operation == "insert":
            if row is not None:
                raise SimulationConflict(f"insert target timestamp already exists: {correction.timestamp}")
            if correction.expected_old_value is not None:
                raise SimulationConflict("insert expected_old_value must be NULL")
            if correction.us_units is None or correction.interval_minutes is None:
                raise SimulationConflict("insert requires us_units and interval_minutes")
            if correction.interval_minutes <= 0:
                raise SimulationConflict("insert interval_minutes must be positive")
            fields = {variable: None for variable in schema_columns}
            fields[correction.variable] = correction.new_value
            working[correction.timestamp] = ArchiveRow(
                us_units=correction.us_units,
                interval_minutes=correction.interval_minutes,
                fields=fields,
            )
        else:
            if row is None:
                raise SimulationConflict(f"update target timestamp is absent: {correction.timestamp}")
            if correction.us_units is not None and correction.us_units != row.us_units:
                raise SimulationConflict("update cannot change us_units")
            if correction.interval_minutes is not None and correction.interval_minutes != row.interval_minutes:
                raise SimulationConflict("update cannot change interval_minutes")
            current = row.fields.get(correction.variable)
            if not _same_value(current, correction.expected_old_value):
                raise SimulationConflict(
                    f"expected_old_value mismatch for {correction.timestamp}/{correction.variable}"
                )
            fields = dict(row.fields)
            fields[correction.variable] = correction.new_value
            working[correction.timestamp] = ArchiveRow(row.us_units, row.interval_minutes, fields)
        applied += 1
        if fail_after is not None and applied == fail_after:
            raise RuntimeError("injected local mid-batch failure; in-memory transaction discarded")

    ledger[batch_id] = payload_digest
    after = _copy_rows(working)
    return BatchResult(batch_id, payload_digest, "simulated_applied", before, after,
                       before_stats, _stats(after, schema_columns), applied), ledger


def order_batches(batches: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return a stable topological order for sidecar-declared batch dependencies."""
    by_id: dict[str, set[str]] = {}
    for batch in batches:
        batch_id = batch.get("batch_id")
        if not isinstance(batch_id, str) or not batch_id:
            raise SimulationConflict("every batch needs a stable batch_id")
        if batch_id in by_id:
            raise SimulationConflict(f"duplicate batch_id: {batch_id}")
        dependencies = set(batch.get("depends_on", []))
        if batch_id in dependencies:
            raise SimulationConflict(f"batch depends on itself: {batch_id}")
        by_id[batch_id] = dependencies
    unknown = {dep for deps in by_id.values() for dep in deps if dep not in by_id}
    if unknown:
        raise SimulationConflict(f"unknown batch dependencies: {sorted(unknown)}")
    order: list[str] = []
    remaining = {key: set(value) for key, value in by_id.items()}
    while remaining:
        ready = sorted(key for key, deps in remaining.items() if not deps)
        if not ready:
            raise SimulationConflict("batch dependency cycle")
        for batch_id in ready:
            order.append(batch_id)
            del remaining[batch_id]
        for deps in remaining.values():
            deps.difference_update(ready)
    return order
