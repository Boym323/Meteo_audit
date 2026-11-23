"""Issue #26 transactional CAS apply/rollback on loucka_reconstruction only.

Injection-only SQL engine: NO connection factory, no CLI APPLY switch, no DDL,
no PBS dependencies and no automatic approval. Calls require an injected DB-API
connection plus a fresh owner-signed exact-batch receipt. Default exported
operation sql_preflight is strictly SELECT-only.

Audit tables are created separately from sql/issue26_transactional_audit_schema.sql
after explicit DBA review. The engine never writes production schema or daily
summaries. CI exercises it only on synthetic ephemeral MariaDB.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Mapping

from .approval_dryrun import CandidateBatch, FieldCorrection, PreflightError, preflight
from .approval_gate import SignedApproval, verify_exact_batch, verify_fresh_snapshot
from .issue26_audit_ddl_guard import verify_audit_ddl

TARGET = "loucka_reconstruction"
ARCHIVE = "loucka_reconstruction.archive"
BATCH_EVENTS = "loucka_reconstruction.issue26_batch_events"
FIELD_EVENTS = "loucka_reconstruction.issue26_field_events"
LEGACY = "loucka_reconstruction.reconstruction_changes"
ADVISORY_LOCK = "meteo_audit_issue26_archive_writer"
APPROVE_ROLLBACK = "VRATIT-DAVKU:"
MAX_OPS = 50
APPROVED_RAIN_MM = Decimal("42.567")
BATCH_NAME = re.compile(r"^[A-Za-z0-9_.:-]{3,80}$")


class TransactionRejected(PreflightError):
    """A safety gate rejected a batch; transaction must leave no modifications."""


@dataclass(frozen=True)
class DbReceipt:
    action: str
    batch_id: str
    payload_sha256: str
    before_image_sha256: str
    affected: int
    committed: bool


def _numeric_equal(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if type(a) is bool or type(b) is bool:
        return False
    try:
        return Decimal(str(a)) == Decimal(str(b))
    except (InvalidOperation, ValueError, TypeError):
        return False


def _verify_batch(batch: CandidateBatch) -> None:
    if not isinstance(batch, CandidateBatch) or not BATCH_NAME.fullmatch(batch.batch_id):
        raise TransactionRejected("unsafe batch_id")
    if not 1 <= len(batch.operations) <= MAX_OPS:
        raise TransactionRejected("only 1..50 explicitly reviewed field changes allowed")
    for op in batch.operations:
        if not isinstance(op, FieldCorrection):
            raise TransactionRejected("unexpected operation type")
        for label, limit in (("source_ref", 255),
                             ("unit_epoch_ref", 255),
                             ("rule_version", 120)):
            if len(getattr(op, label)) > limit:
                raise TransactionRejected("evidence reference exceeds journal capacity")


def _fetch_one(cur: Any, stmt: str, args: tuple = ()) -> tuple | None:
    cur.execute(stmt, args)
    result = cur.fetchone()
    if result is None:
        return None
    if isinstance(result, Mapping):
        return tuple(result.values())
    return tuple(result)


def _rows(cur: Any, stmt: str, args: tuple = ()) -> list[tuple]:
    cur.execute(stmt, args)
    rows = cur.fetchall()
    return [tuple(r.values()) if isinstance(r, Mapping) else tuple(r) for r in rows]


def _assert_target(cur: Any) -> None:
    selected = _fetch_one(cur, "SELECT DATABASE()")
    if selected != (TARGET,):
        raise TransactionRejected("database connection must select loucka_reconstruction explicitly")
    schemas = _rows(cur,
        "SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME IN "
        "('archive','reconstruction_changes','issue26_batch_events','issue26_field_events')",
        (TARGET,))
    if len(schemas) != 4 or any(engine != "InnoDB" for _, engine in schemas):
        raise TransactionRejected("expected four transactional reconstruction tables")
    # Never execute a write against partially installed or drifted audit DDL.
    verify_audit_ddl(cur)


def _check_rain(cur: Any) -> None:
    row = _fetch_one(cur,
        "SELECT ROUND(SUM(COALESCE(rain,0))*10,3) "
        "FROM loucka_reconstruction.archive "
        "WHERE dateTime>=1625097600 AND dateTime<1627776000")
    if row is None or not _numeric_equal(row[0], APPROVED_RAIN_MM):
        raise TransactionRejected("protected July 2021 rain invariant differs")


def _legacy_history(cur: Any, op: FieldCorrection) -> None:
    prior = _fetch_one(cur,
        "SELECT id FROM loucka_reconstruction.reconstruction_changes "
        "WHERE target_time=%s AND variable=%s LIMIT 1",
        (op.target_time_utc, op.variable))
    if prior is not None:
        raise TransactionRejected("target already has legacy reconstruction change history")


def _new_history(cur: Any, op: FieldCorrection) -> None:
    prior = _fetch_one(cur,
        "SELECT id FROM loucka_reconstruction.issue26_field_events "
        "WHERE target_time=%s AND variable=%s LIMIT 1",
        (op.target_time_utc, op.variable))
    if prior is not None:
        raise TransactionRejected("target already has issue26 audit history")


def _check_batch_id(cur: Any, batch_id: str) -> None:
    if _fetch_one(cur,
                  "SELECT batch_id FROM loucka_reconstruction.issue26_batch_events "
                  "WHERE batch_id=%s LIMIT 1", (batch_id,)):
        raise TransactionRejected("batch id already in immutable event history")
    if _fetch_one(cur,
                  "SELECT id FROM loucka_reconstruction.reconstruction_changes "
                  "WHERE batch_key=%s LIMIT 1", (batch_id,)):
        raise TransactionRejected("batch id collides with legacy reconstruction history")


def _field(cur: Any, op: FieldCorrection, *, lock: bool) -> float | None:
    # FieldCorrection validates the identifier against the fixed archive value-field allowlist.
    name = op.variable
    clause = " FOR UPDATE" if lock else ""
    record = _fetch_one(cur, "SELECT " + chr(96) + name + chr(96)
                        + " FROM loucka_reconstruction.archive WHERE dateTime=%s"
                        + clause, (op.target_time_utc,))
    if record is None:
        raise TransactionRejected("target archive timestamp missing")
    return record[0]


def _snapshot(cur: Any, batch: CandidateBatch, *, lock: bool) -> dict:
    # Stable timestamp + field ordering prevents avoidable lock-order deadlocks.
    raw = {}
    for op in sorted(batch.operations, key=lambda v: v.key):
        raw[op.key] = _field(cur, op, lock=lock)
        _legacy_history(cur, op)
        _new_history(cur, op)
    return raw


def sql_preflight(connection: Any, batch: CandidateBatch) -> dict:
    """Read-only SQL preflight. Does not begin a transaction or lock rows."""
    _verify_batch(batch)
    cur = connection.cursor()
    try:
        _assert_target(cur)
        _check_rain(cur)
        _check_batch_id(cur, batch.batch_id)
        return preflight(batch, _snapshot(cur, batch, lock=False))
    finally:
        cur.close()


def _lock(cur: Any) -> None:
    r = _fetch_one(cur, "SELECT GET_LOCK(%s,%s)", (ADVISORY_LOCK, 8))
    if r != (1,):
        raise TransactionRejected("issue26 writer advisory lock unavailable")


def _unlock(connection: Any) -> None:
    # Use a fresh cursor; release before the connection returns to any pool.
    cur = connection.cursor()
    try:
        result = _fetch_one(cur, "SELECT RELEASE_LOCK(%s)", (ADVISORY_LOCK,))
        if result != (1,):
            raise TransactionRejected("issue26 writer lock release uncertain")
    finally:
        cur.close()


def _insert_batch_event(cur: Any, batch: CandidateBatch, receipt: SignedApproval,
                        before_hash: str, action: str) -> None:
    cur.execute(
        "INSERT INTO loucka_reconstruction.issue26_batch_events "
        "(batch_id,event_type,payload_sha256,before_image_sha256,"
        "approval_mac_sha256,approver,operation_count) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (batch.batch_id, action, batch.payload_sha256, before_hash,
         receipt.mac_sha256, receipt.approver, len(batch.operations)))


def _insert_fields(cur: Any, batch: CandidateBatch, action: str) -> None:
    for op in batch.operations:
        prior, proposed = ((op.expected_old, op.proposed_new)
                           if action == "APPLY" else (op.proposed_new, op.expected_old))
        cur.execute(
            "INSERT INTO loucka_reconstruction.issue26_field_events "
            "(batch_id,event_type,target_time,variable,old_value,new_value,"
            "source_ref,unit_epoch_ref,rule_version,"
            "diagnosis_confidence,replacement_confidence) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (batch.batch_id, action, op.target_time_utc, op.variable,
             prior, proposed, op.source_ref, op.unit_epoch_ref, op.rule_version,
             op.diagnosis_confidence, op.replacement_confidence))


def _cas_update(cur: Any, op: FieldCorrection, *, rollback: bool = False) -> None:
    name = chr(96) + op.variable + chr(96)
    expected = op.proposed_new if rollback else op.expected_old
    value = op.expected_old if rollback else op.proposed_new
    cur.execute("UPDATE loucka_reconstruction.archive SET " + name
                + "=%s WHERE dateTime=%s AND " + name + " <=> %s",
                (value, op.target_time_utc, expected))
    if cur.rowcount != 1:
        raise TransactionRejected("NULL-safe CAS update lost race or touched wrong count")


def apply_approved_batch(connection: Any, batch: CandidateBatch,
                         approved_report: Mapping, receipt: SignedApproval,
                         *, approval_key: bytes, now: int | None = None) -> DbReceipt:
    """Apply a single explicitly reviewed batch in one InnoDB transaction.

    No connection is ever created by this module. Driver must support DB-API
    cursor and begin/commit/rollback (PyMySQL contract).
    """
    _verify_batch(batch)
    verify_exact_batch(batch, approved_report, receipt, secret_key=approval_key, now=now)
    cur = connection.cursor()
    locked = False
    try:
        _assert_target(cur)
        _lock(cur)
        locked = True
        connection.begin()
        try:
            _assert_target(cur)
            _check_rain(cur)
            _check_batch_id(cur, batch.batch_id)
            fresh = _snapshot(cur, batch, lock=True)
            verify_fresh_snapshot(batch, approved_report, fresh)
            # Revalidate expiry inside transaction (not just at caller start).
            verify_exact_batch(batch, approved_report, receipt,
                               secret_key=approval_key, now=now)
            _insert_batch_event(cur, batch, receipt,
                                approved_report["before_image_sha256"], "APPLY")
            _insert_fields(cur, batch, "APPLY")
            for op in batch.operations:
                _cas_update(cur, op)
            _check_rain(cur)
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        return DbReceipt("APPLY", batch.batch_id, batch.payload_sha256,
                         approved_report["before_image_sha256"],
                         len(batch.operations), True)
    finally:
        cur.close()
        if locked:
            _unlock(connection)


def _check_rollback_history(cur: Any, batch: CandidateBatch,
                            report: Mapping, receipt: SignedApproval) -> None:
    record = _fetch_one(cur,
        "SELECT payload_sha256,before_image_sha256,operation_count,approval_mac_sha256 "
        "FROM loucka_reconstruction.issue26_batch_events "
        "WHERE batch_id=%s AND event_type='APPLY' FOR UPDATE",
        (batch.batch_id,))
    if record is None or record[:3] != (
        batch.payload_sha256, report["before_image_sha256"],
        len(batch.operations)
    ):
        raise TransactionRejected("missing or altered persisted APPLY event")
    if record[3] == receipt.mac_sha256:
        raise TransactionRejected("rollback requires a DIFFERENT newly signed approval receipt")
    if _fetch_one(cur,
                  "SELECT batch_id FROM loucka_reconstruction.issue26_batch_events "
                  "WHERE batch_id=%s AND event_type='ROLLBACK' FOR UPDATE",
                  (batch.batch_id,)):
        raise TransactionRejected("batch already rolled back")
    existing = _rows(cur,
        "SELECT target_time,variable,old_value,new_value,source_ref,"
        "unit_epoch_ref,rule_version,diagnosis_confidence,replacement_confidence "
        "FROM loucka_reconstruction.issue26_field_events "
        "WHERE batch_id=%s AND event_type='APPLY' "
        "ORDER BY target_time,variable FOR UPDATE", (batch.batch_id,))
    expected = sorted(batch.operations, key=lambda op: op.key)
    if len(existing) != len(expected):
        raise TransactionRejected("missing persisted per-field APPLY audit")
    for row, op in zip(existing, expected):
        if (row[0] != op.target_time_utc or row[1] != op.variable
                or not _numeric_equal(row[2], op.expected_old)
                or not _numeric_equal(row[3], op.proposed_new)
                or row[4:] != (op.source_ref, op.unit_epoch_ref,
                               op.rule_version, op.diagnosis_confidence,
                               op.replacement_confidence)):
            raise TransactionRejected("persisted before/after audit differs from manifest")


def rollback_approved_batch(
    connection: Any, batch: CandidateBatch, approved_report: Mapping,
    receipt: SignedApproval, *, approval_key: bytes,
    entered_rollback_challenge: str, now: int | None = None,
) -> DbReceipt:
    """Rollback only this exact applied batch under current=new_value CAS.

    Must have a fresh owner signature for this manifest plus an explicit
    rollback challenge. Never relies on a host-level backup.
    """
    _verify_batch(batch)
    verify_exact_batch(batch, approved_report, receipt, secret_key=approval_key, now=now)
    phrase = (APPROVE_ROLLBACK + batch.batch_id + ":" + batch.payload_sha256
              + ":" + approved_report["before_image_sha256"])
    if entered_rollback_challenge != phrase:
        raise TransactionRejected("exact rollback confirmation missing")
    cur = connection.cursor()
    locked = False
    try:
        _assert_target(cur)
        _lock(cur)
        locked = True
        connection.begin()
        try:
            _assert_target(cur)
            _check_rain(cur)
            _check_rollback_history(cur, batch, approved_report, receipt)
            # Rollback is conditional on each field still being equal to
            # the originally approved post-image, even after row locks.
            for op in sorted(batch.operations, key=lambda item: item.key):
                current = _field(cur, op, lock=True)
                if not _numeric_equal(current, op.proposed_new):
                    raise TransactionRejected("post-image differs; rollback refused")
            verify_exact_batch(batch, approved_report, receipt,
                               secret_key=approval_key, now=now)
            _insert_batch_event(cur, batch, receipt,
                                approved_report["before_image_sha256"], "ROLLBACK")
            _insert_fields(cur, batch, "ROLLBACK")
            for op in batch.operations:
                _cas_update(cur, op, rollback=True)
            _check_rain(cur)
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        return DbReceipt("ROLLBACK", batch.batch_id, batch.payload_sha256,
                         approved_report["before_image_sha256"],
                         len(batch.operations), True)
    finally:
        cur.close()
        if locked:
            _unlock(connection)
