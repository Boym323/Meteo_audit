"""Transactional MariaDB writer for the approved INSERT-only archive mode.

No connection details are stored here.  The DB-API connection objects are
injected, making it possible to exercise the transaction contract against an
isolated MariaDB fixture.  This module must never be pointed at production
until the three owner approvals are recorded.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import replace
from typing import Any, Iterable, Mapping, Protocol

from .archive_sync import (
    ARCHIVE_FIELDS, PROTECTED_LOWER_BOUND, SyncError, SyncPlan,
    build_sync_plan, validate_action,
)

SOURCE_SCHEMA = "pocasi-loucka.eu"
TARGET_SCHEMA = "loucka_reconstruction"
CURSOR_TABLE = "archive_sync_cursor"
AUDIT_TABLE = "archive_sync_audit"
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class Cursor(Protocol):
    description: Any
    def execute(self, operation: str, params: Any = None) -> Any: ...
    def fetchall(self) -> list[Any]: ...
    def fetchone(self) -> Any: ...
    def close(self) -> None: ...


class Connection(Protocol):
    def cursor(self) -> Cursor: ...
    def begin(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...


def _qi(identifier: str) -> str:
    if not IDENTIFIER.fullmatch(identifier):
        raise SyncError(f"unsafe SQL identifier: {identifier!r}")
    return f"`{identifier}`"


def _fetch_dicts(cursor: Cursor) -> list[dict[str, Any]]:
    rows = cursor.fetchall()
    if not rows:
        return []
    if isinstance(rows[0], Mapping):
        return [dict(x) for x in rows]
    names = [x[0] for x in cursor.description]
    return [dict(zip(names, row)) for row in rows]


def read_archive_schema(connection: Connection, schema: str) -> tuple[str, ...]:
    if schema not in {SOURCE_SCHEMA, TARGET_SCHEMA}:
        raise SyncError("schema outside the fixed source/target allowlist")
    cur = connection.cursor()
    try:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position", (schema, "archive"))
        rows = cur.fetchall()
        cols = tuple((r[0] if not isinstance(r, Mapping) else r["column_name"]) for r in rows)
        if set(cols) != ARCHIVE_FIELDS or len(cols) != len(ARCHIVE_FIELDS):
            raise SyncError(f"{schema}.archive does not match the approved exact 80-column mapping")
        return cols
    finally:
        cur.close()


def load_source_snapshot(connection: Connection, *, watermark: int, lookback_seconds: int = 86_400) -> tuple[list[dict[str, Any]], int, int]:
    """Read one bounded source snapshot; exclusive end is captured max + 1."""
    read_archive_schema(connection, SOURCE_SCHEMA)
    # Full post-fence rescan catches delayed source arrivals older than any
    # arbitrary overlap window. The current frozen snapshot is about 4.6k rows.
    start = PROTECTED_LOWER_BOUND + 1
    cur = connection.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) AS source_count,MAX(`dateTime`) AS captured_max FROM `{SOURCE_SCHEMA}`.`archive` WHERE `dateTime` >= %s", (start,))
        result = cur.fetchone()
        if isinstance(result, Mapping):
            source_count, captured = int(result["source_count"]), result["captured_max"]
        else:
            source_count, captured = int(result[0]), result[1]
        if captured is None:
            if source_count != 0:
                raise SyncError("source count/max snapshot is internally inconsistent")
            return [], start, watermark + 1
        end_exclusive = int(captured) + 1
        fields = ",".join(_qi(x) for x in sorted(ARCHIVE_FIELDS))
        cur.execute(f"SELECT {fields} FROM `{SOURCE_SCHEMA}`.`archive` WHERE `dateTime` >= %s AND `dateTime` < %s ORDER BY `dateTime`", (start, end_exclusive))
        rows = _fetch_dicts(cur)
        if len(rows) != source_count:
            raise SyncError(f"source snapshot incomplete: expected {source_count} rows, fetched {len(rows)}")
        return rows, start, end_exclusive
    finally:
        cur.close()


def read_target_rows(connection: Connection, start: int, end_exclusive: int) -> list[dict[str, Any]]:
    read_archive_schema(connection, TARGET_SCHEMA)
    fields = ",".join(_qi(x) for x in sorted(ARCHIVE_FIELDS))
    cur = connection.cursor()
    try:
        cur.execute(f"SELECT {fields} FROM `{TARGET_SCHEMA}`.`archive` WHERE `dateTime` >= %s AND `dateTime` < %s ORDER BY `dateTime`", (start, end_exclusive))
        return _fetch_dicts(cur)
    finally:
        cur.close()


def read_frozen_source_rows(connection: Connection, start: int, end_exclusive: int, *, lock_shared: bool = False) -> list[dict[str, Any]]:
    """Read source rows only inside the manifest's exact exclusive bounds."""
    if (start, end_exclusive) != (1_793_286_600, 1_794_682_801):
        raise SyncError("frozen source query bounds differ from the approved manifest")
    read_archive_schema(connection, SOURCE_SCHEMA)
    fields = ",".join(_qi(x) for x in sorted(ARCHIVE_FIELDS))
    cur = connection.cursor()
    try:
        lock_clause = " LOCK IN SHARE MODE" if lock_shared else ""
        cur.execute(f"SELECT {fields} FROM `{SOURCE_SCHEMA}`.`archive` WHERE `dateTime` > %s AND `dateTime` < %s ORDER BY `dateTime`{lock_clause}", (start, end_exclusive))
        return _fetch_dicts(cur)
    finally:
        cur.close()


def plan_snapshot(source: Connection, target: Connection, *, watermark: int, lookback_seconds: int = 86_400) -> SyncPlan:
    source_cols = read_archive_schema(source, SOURCE_SCHEMA)
    target_cols = read_archive_schema(target, TARGET_SCHEMA)
    rows, start, end = load_source_snapshot(source, watermark=watermark, lookback_seconds=lookback_seconds)
    targets = read_target_rows(target, start, end)
    return build_sync_plan(rows, targets, watermark=watermark, window_end=end,
                           lookback_seconds=lookback_seconds, source_schema=source_cols,
                           target_schema=target_cols)


def bounded_batch(plan: SyncPlan, limit: int) -> SyncPlan:
    """Return the first ordered INSERT batch with a cursor bounded to its tail."""
    if not 1 <= limit <= 100:
        raise SyncError("batch limit must be between 1 and 100")
    if plan.conflicts:
        return plan
    actions = plan.actions[:limit]
    if actions:
        cursor = max(plan.previous_watermark, actions[-1].timestamp)
    else:
        # No missing rows means the captured range was fully inspected.
        cursor = plan.proposed_watermark
    return replace(plan, proposed_watermark=cursor, actions=actions)


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _db_values_equal(left: Any, right: Any) -> bool:
    from decimal import Decimal
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, (int, float, Decimal)) and not isinstance(left, bool) and isinstance(right, (int, float, Decimal)) and not isinstance(right, bool):
        return Decimal(str(left)) == Decimal(str(right))
    return left == right


def _verify_committed(connection: Connection, plan: SyncPlan, batch_id: str) -> dict[str, Any]:
    """Read committed target, audit, and cursor through a separate connection."""
    if not plan.actions:
        return {"verified_rows": 0, "verified_target_postimage_hash": _canonical_hash([])}
    timestamps = [a.timestamp for a in plan.actions]
    placeholders = ",".join(["%s"] * len(timestamps))
    cols = ",".join(_qi(x) for x in sorted(ARCHIVE_FIELDS))
    cur = connection.cursor()
    try:
        cur.execute(f"SELECT {cols} FROM `{TARGET_SCHEMA}`.`archive` WHERE `dateTime` IN ({placeholders}) ORDER BY `dateTime`", tuple(timestamps))
        rows = _fetch_dicts(cur)
        expected = {a.timestamp: a.values for a in plan.actions}
        if len(rows) != len(plan.actions) or {r["dateTime"] for r in rows} != set(expected):
            raise SyncError("post-commit target row count/timestamp mismatch")
        for row in rows:
            if set(row) != ARCHIVE_FIELDS:
                raise SyncError("post-commit target does not contain all 80 archive columns")
            for name in ARCHIVE_FIELDS:
                if not _db_values_equal(row[name], expected[row["dateTime"]][name]):
                    raise SyncError(f"post-commit target differs at {row['dateTime']}.{name}")
        cur.execute(f"SELECT `dateTime`,`source_row_sha256` FROM `{TARGET_SCHEMA}`.{_qi(AUDIT_TABLE)} WHERE `batch_id`=%s ORDER BY `dateTime`", (batch_id,))
        audit = _fetch_dicts(cur)
        expected_hashes = {a.timestamp: _canonical_hash(a.values) for a in plan.actions}
        if {int(x["dateTime"]): x["source_row_sha256"] for x in audit} != expected_hashes:
            raise SyncError("post-commit audit event set/hash mismatch")
        cur.execute(f"SELECT `watermark`,`last_batch_id` FROM `{TARGET_SCHEMA}`.{_qi(CURSOR_TABLE)} WHERE `sync_name`=%s", ("gw3000-insert-only-v1",))
        cursor = cur.fetchone()
        if cursor is None:
            raise SyncError("post-commit cursor row missing")
        watermark = cursor["watermark"] if isinstance(cursor, Mapping) else cursor[0]
        last_batch = cursor["last_batch_id"] if isinstance(cursor, Mapping) else cursor[1]
        if int(watermark) != plan.proposed_watermark or last_batch != batch_id:
            raise SyncError("post-commit cursor identity/value mismatch")
        return {"verified_rows": len(rows), "verified_target_postimage_hash": _canonical_hash(rows)}
    finally:
        cur.close()


def _record_postcommit_incident(plan: SyncPlan, batch_id: str, reason: str) -> str:
    """Persist compact evidence and stop; this function never retries writes."""
    folder = Path(__file__).resolve().parents[2] / "runs" / "archive-sync-incidents"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = folder / f"{stamp}-{batch_id}.json"
    evidence = {
        "schema": "archive-sync-postcommit-incident-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "batch_id": batch_id,
        "reason": reason,
        "timestamps": [a.timestamp for a in plan.actions],
        "source_payload_hash": _canonical_hash([a.values for a in plan.actions]),
        "expected_target_row_hashes": {a.timestamp: _canonical_hash(a.values) for a in plan.actions},
        "cursor_expected": {"previous": plan.previous_watermark, "proposed": plan.proposed_watermark},
        "action": "HALT_NO_AUTOMATIC_RETRY_OR_DELETE",
    }
    path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return str(path)


def apply_plan(connection: Connection, plan: SyncPlan, *, batch_id: str, batch_size: int = 100,
               postcommit_connection: Connection | None = None,
               authorization_mode: str,
               frozen_payload_sha256: str | None = None) -> dict[str, Any]:
    """Atomically append rows plus immutable audit and cursor state.

    The caller must first obtain all approvals and a restricted writer account.
    Existing target rows are locked/rechecked before each insert; a race aborts
    the complete transaction.  Cursor state is committed with inserts/audit.
    """
    if plan.conflicts:
        raise SyncError("refusing to apply a conflicted plan")
    if authorization_mode not in {"frozen_backfill", "continuous"}:
        raise SyncError("writer requires an explicit backfill or continuous authorization mode")
    if authorization_mode == "frozen_backfill":
        from .archive_sync_frozen import (LOWER_EXCLUSIVE, UPPER_EXCLUSIVE, PAYLOAD_SHA256,
                                          load_frozen_payload)
        if frozen_payload_sha256 != PAYLOAD_SHA256 or (plan.window_start, plan.window_end_exclusive) != (LOWER_EXCLUSIVE, UPPER_EXCLUSIVE):
            raise SyncError("frozen writer authorization or manifest bounds mismatch")
        payload_path = Path(__file__).resolve().parents[2] / "data" / "GW3000_INSERT_ONLY_BACKFILL_PAYLOAD.jsonl"
        manifest_path = Path(__file__).resolve().parents[2] / "data" / "GW3000_INSERT_ONLY_BACKFILL_MANIFEST.json"
        approved_rows, _ = load_frozen_payload(payload_path, manifest_path)
        approved = {row["dateTime"]: row for row in approved_rows}
        if any(a.timestamp not in approved or dict(a.values) != approved[a.timestamp] for a in plan.actions):
            raise SyncError("action is not an exact row from the canonical frozen payload")
    elif frozen_payload_sha256 is not None:
        raise SyncError("continuous authorization cannot carry frozen backfill identity")
    if not isinstance(batch_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", batch_id):
        raise SyncError("batch_id must be non-empty and <=128 characters")
    if not 1 <= batch_size <= 100:
        raise SyncError("batch_size must be between 1 and 100")
    if not isinstance(plan.actions, tuple) or len(plan.actions) > batch_size:
        raise SyncError("plan exceeds the atomic batch limit")
    if type(plan.window_start) is not int or type(plan.window_end_exclusive) is not int or plan.window_end_exclusive <= plan.window_start:
        raise SyncError("plan window bounds are invalid")
    if type(plan.previous_watermark) is not int or type(plan.proposed_watermark) is not int or plan.previous_watermark < PROTECTED_LOWER_BOUND:
        raise SyncError("plan cursor values are invalid or below protection fence")
    if plan.proposed_watermark < plan.previous_watermark:
        raise SyncError("plan cursor cannot move backwards")
    timestamps = [a.timestamp for a in plan.actions]
    if len(timestamps) != len(set(timestamps)):
        raise SyncError("duplicate timestamps in plan actions")
    if timestamps != sorted(timestamps):
        raise SyncError("plan actions must be ordered by timestamp")
    for action in plan.actions:
        validate_action(action, upper_exclusive=plan.window_end_exclusive)
    if timestamps and plan.proposed_watermark < timestamps[-1]:
        raise SyncError("proposed cursor is behind the final action")
    if plan.captured_source_max is not None and (type(plan.captured_source_max) is not int or plan.captured_source_max >= plan.window_end_exclusive):
        raise SyncError("captured source maximum is inconsistent with plan window")
    if plan.actions and postcommit_connection is None:
        raise SyncError("independent post-commit read connection is required before any write")

    columns = read_archive_schema(connection, TARGET_SCHEMA)
    qcols = ",".join(_qi(x) for x in columns)
    placeholders = ",".join(["%s"] * len(columns))
    insert_sql = f"CALL `{TARGET_SCHEMA}`.`gw3000_insert_frozen_archive`({placeholders})"
    cur = connection.cursor()
    connection.begin()
    try:
        # Serializes approved synchronizer instances.  GET_LOCK is session scoped;
        # release is guaranteed in finally after transaction commit/rollback.
        cur.execute("SELECT GET_LOCK(%s, %s)", ("loucka_archive_insert_sync", 5))
        lock_row = cur.fetchone()
        locked = (lock_row[0] if not isinstance(lock_row, Mapping) else next(iter(lock_row.values()))) == 1
        if not locked:
            raise SyncError("could not acquire the single-writer lock")
        cur.execute(f"SELECT `watermark` FROM `{TARGET_SCHEMA}`.{_qi(CURSOR_TABLE)} WHERE `sync_name`=%s FOR UPDATE", ("gw3000-insert-only-v1",))
        stored = cur.fetchone()
        current = stored[0] if stored is not None and not isinstance(stored, Mapping) else (stored["watermark"] if stored else 0)
        if int(current) != plan.previous_watermark:
            raise SyncError("cursor changed since planning; re-read source and replan")

        for action in plan.actions:
            cur.execute(f"SELECT {qcols} FROM `{TARGET_SCHEMA}`.`archive` WHERE `dateTime`=%s FOR UPDATE", (action.timestamp,))
            if cur.fetchone() is not None:
                raise SyncError(f"target timestamp {action.timestamp} appeared after planning")
            values = tuple(action.values[name] for name in columns)
            try:
                cur.execute(insert_sql, values)
            except Exception as exc:
                raise SyncError(f"insert failed at timestamp {action.timestamp}; transaction rolled back: {exc}") from exc
            cur.execute(f"INSERT INTO `{TARGET_SCHEMA}`.{_qi(AUDIT_TABLE)} (`batch_id`,`dateTime`,`source_schema`,`target_schema`,`source_row_sha256`,`row_json`,`created_utc`) VALUES (%s,%s,%s,%s,%s,%s,UTC_TIMESTAMP(6))",
                        (batch_id, action.timestamp, SOURCE_SCHEMA, TARGET_SCHEMA,
                         _canonical_hash(action.values), json.dumps(action.values, sort_keys=True, allow_nan=False, default=str)))

        cur.execute(f"UPDATE `{TARGET_SCHEMA}`.{_qi(CURSOR_TABLE)} SET `watermark`=%s,`last_batch_id`=%s,`updated_utc`=UTC_TIMESTAMP(6) WHERE `sync_name`=%s",
                    (plan.proposed_watermark, batch_id, "gw3000-insert-only-v1"))
        if getattr(cur, "rowcount", 1) != 1:
            raise SyncError("cursor update affected no row; refusing commit")
        try:
            connection.commit()
        except Exception as commit_error:
            # COMMIT may have reached the server even if its acknowledgement was
            # lost. Never replay automatically: resolve from a fresh connection.
            if postcommit_connection is None:
                raise SyncError("ambiguous COMMIT; writes halted for manual state inspection") from commit_error
            try:
                verified = _verify_committed(postcommit_connection, plan, batch_id)
            except Exception as verify_error:
                evidence = _record_postcommit_incident(plan, batch_id, f"ambiguous commit recovery failed: {verify_error}")
                raise SyncError(f"ambiguous COMMIT; recovery failed; evidence={evidence}") from verify_error
            evidence = _record_postcommit_incident(plan, batch_id, "ambiguous COMMIT acknowledgement; independent postimage verified; automatic continuation halted")
            raise SyncError(f"ambiguous COMMIT; postimage was verified but runner halted without retry; evidence={evidence}") from commit_error
        try:
            verified = _verify_committed(postcommit_connection, plan, batch_id) if plan.actions else {"verified_rows": 0, "verified_target_postimage_hash": _canonical_hash([])}
        except Exception as verify_error:
            evidence = _record_postcommit_incident(plan, batch_id, f"post-commit verification failed: {verify_error}")
            raise SyncError(f"post-commit verification failed; evidence={evidence}") from verify_error
        return {"batch_id": batch_id, "inserted_rows": verified["verified_rows"], "watermark": plan.proposed_watermark,
                "source_payload_hash": _canonical_hash([a.values for a in plan.actions]), **verified}
    except Exception:
        connection.rollback()
        raise
    finally:
        try:
            cur.execute("SELECT RELEASE_LOCK(%s)", ("loucka_archive_insert_sync",))
        except Exception:
            pass
        cur.close()


def pymysql_connection_from_env(database: str, *, readonly: bool = False) -> Connection:
    """Optional production adapter. Credentials come only from process env."""
    if database not in {SOURCE_SCHEMA, TARGET_SCHEMA}:
        raise SyncError("database outside fixed allowlist")
    try:
        import pymysql  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("install the pinned requirements-sync.txt dependencies") from exc
    import os
    prefix = "SOURCE_DB" if database == SOURCE_SCHEMA else "TARGET_DB"
    required = (f"{prefix}_HOST", f"{prefix}_PORT", f"{prefix}_USER", f"{prefix}_PASSWORD")
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError("missing DB environment settings: " + ", ".join(missing))
    conn = pymysql.connect(host=os.environ[f"{prefix}_HOST"], port=int(os.environ[f"{prefix}_PORT"]),
                           user=os.environ[f"{prefix}_USER"], password=os.environ[f"{prefix}_PASSWORD"],
                           database=database, charset="utf8mb4", autocommit=False,
                           cursorclass=pymysql.cursors.DictCursor)
    if readonly:
        cur = conn.cursor()
        cur.execute("SET SESSION TRANSACTION READ ONLY")
        cur.close()
    return conn
