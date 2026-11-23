"""Issue #26: audited READ-ONLY SQL snapshot for an exact correction manifest.

Operates against the existing loucka_reconstruction MariaDB instance only.
All reads execute in one explicit REPEATABLE READ consistent-snapshot, READ ONLY
transaction. No DDL, INSERT/UPDATE/DELETE, PBS checks or second DB server.
The output is a review artefact, NOT approval or validation of raw sources.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from math import isfinite
from typing import Any, Mapping

from .approval_dryrun import CandidateBatch, PreflightError, preflight
from .issue26_transaction import (
    TARGET, _verify_batch, _numeric_equal, APPROVED_RAIN_MM,
)

REVIEW_SCHEMA = "loucka-issue26-readonly-review-v1"
BASE_TABLES = frozenset({"archive", "reconstruction_changes"})
AUDIT_TABLES = frozenset({"issue26_batch_events", "issue26_field_events"})


def _single(cur: Any, sql: str, params: tuple = ()) -> tuple | None:
    cur.execute(sql, params)
    result = cur.fetchone()
    if result is None:
        return None
    if isinstance(result, Mapping):
        return tuple(result.values())
    return tuple(result)


def _as_manifest_number(value: Any) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise PreflightError("boolean observed value in archive")
    if isinstance(value, (Decimal, int, float)):
        number = float(value)
        if not isfinite(number):
            raise PreflightError("nonfinite observed archive reading")
        return number
    raise PreflightError("archive reading must be numeric or NULL")


def _live_target_schema(cur: Any) -> str:
    if _single(cur, "SELECT DATABASE()") != (TARGET,):
        raise PreflightError("read-only reviewer requires loucka_reconstruction selection")
    cur.execute(
        "SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME IN "
        "('archive','reconstruction_changes','issue26_batch_events','issue26_field_events')",
        (TARGET,),
    )
    rows = cur.fetchall()
    tables = dict(tuple(x.values()) if isinstance(x, Mapping) else x for x in rows)
    if not BASE_TABLES.issubset(tables):
        raise PreflightError("archive or legacy change ledger missing")
    if any(engine != "InnoDB" for engine in tables.values()):
        raise PreflightError("all relevant reconstruction tables must be InnoDB")
    present = AUDIT_TABLES.intersection(tables)
    if present and present != AUDIT_TABLES:
        raise PreflightError("partial issue26 audit schema: NO-GO")
    return "PRESENT_NOT_DDL_VERIFIED" if present else "NOT_INSTALLED"


def _assert_rain(cur: Any) -> None:
    total = _single(cur,
        "SELECT ROUND(SUM(COALESCE(rain,0))*10,3) "
        "FROM loucka_reconstruction.archive "
        "WHERE dateTime>=1625097600 AND dateTime<1627776000")
    if total is None or not _numeric_equal(total[0], APPROVED_RAIN_MM):
        raise PreflightError("protected July 2021 rainfall invariant differs")


def _assert_batch_unused(cur: Any, batch: CandidateBatch, audit: str) -> None:
    if _single(cur,
        "SELECT id FROM loucka_reconstruction.reconstruction_changes "
        "WHERE batch_key=%s LIMIT 1", (batch.batch_id,)):
        raise PreflightError("batch ID already exists in legacy history")
    if audit != "NOT_INSTALLED" and _single(cur,
        "SELECT batch_id FROM loucka_reconstruction.issue26_batch_events "
        "WHERE batch_id=%s LIMIT 1", (batch.batch_id,)):
        raise PreflightError("batch ID already exists in issue26 history")


def _fresh_value(cur: Any, op: Any, audit: str) -> int | float | None:
    # op.variable validated against the fixed VALUE_FIELDS allowlist upstream.
    identifier = chr(96) + op.variable + chr(96)
    observed = _single(
        cur,
        "SELECT " + identifier +
        " FROM loucka_reconstruction.archive WHERE dateTime=%s",
        (op.target_time_utc,),
    )
    if observed is None:
        raise PreflightError("archive timestamp missing for requested field")
    if _single(cur,
        "SELECT id FROM loucka_reconstruction.reconstruction_changes "
        "WHERE target_time=%s AND variable=%s LIMIT 1",
        (op.target_time_utc, op.variable)):
        raise PreflightError("legacy reconstruction history collision")
    if audit != "NOT_INSTALLED" and _single(cur,
        "SELECT id FROM loucka_reconstruction.issue26_field_events "
        "WHERE target_time=%s AND variable=%s LIMIT 1",
        (op.target_time_utc, op.variable)):
        raise PreflightError("issue26 reconstruction history collision")
    return _as_manifest_number(observed[0])


def export_current_review(
    connection: Any, batch: CandidateBatch, *,
    expected_hostname: str, expected_server_id: int,
) -> dict:
    """Read a pinned InnoDB snapshot, returning the exact review + metadata.

    Requires a dedicated DB-API connection, with no existing transaction.
    Each attempted review starts a read-only consistent transaction and
    always ROLLBACKs that read-only transaction. Never trust the returned
    snapshot as source evidence or owner permission on its own.
    """
    _verify_batch(batch)
    if not isinstance(expected_hostname, str) or not expected_hostname.strip():
        raise PreflightError("expected MariaDB hostname is mandatory")
    if type(expected_server_id) is not int or expected_server_id <= 0:
        raise PreflightError("expected MariaDB server_id is mandatory")

    cur = connection.cursor()
    started = False
    try:
        cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        cur.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY")
        started = True
        identity = _single(cur,
            "SELECT DATABASE(),@@hostname,@@server_id,CURRENT_USER(),@@version")
        if identity is None or len(identity) != 5:
            raise PreflightError("unable to establish exact database identity")
        database, hostname, server_id, db_user, version = identity
        if (database != TARGET or hostname != expected_hostname
                or int(server_id) != expected_server_id):
            raise PreflightError("SQL database server identity does not match operator target")
        audit = _live_target_schema(cur)
        _assert_rain(cur)
        _assert_batch_unused(cur, batch, audit)

        snapshot = {}
        for op in sorted(batch.operations, key=lambda item: item.key):
            snapshot[op.key] = _fresh_value(cur, op, audit)
        report = preflight(batch, snapshot)

        archive_rows = _single(
            cur, "SELECT COUNT(*) FROM loucka_reconstruction.archive")[0]
        change_events = _single(
            cur, "SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes")[0]

        return {
            "schema": REVIEW_SCHEMA,
            "status": "READ_ONLY_SQL_SNAPSHOT_NOT_APPROVED",
            "db_writes": 0,
            "identity": {
                "database": database,
                "hostname": hostname,
                "server_id": int(server_id),
                "current_user": str(db_user),
                "version": str(version),
            },
            "audit_schema": audit,
            "snapshot": report,
            "archive_rows": int(archive_rows),
            "legacy_change_events": int(change_events),
            "july_2021_mm": str(APPROVED_RAIN_MM),
            "source_evidence_verified": False,
            "owner_approval_granted": False,
            "exported_utc": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        try:
            if started:
                connection.rollback()
        finally:
            cur.close()
