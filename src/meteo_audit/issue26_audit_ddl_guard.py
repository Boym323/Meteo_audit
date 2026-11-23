"""Strict, SELECT-only audit DDL compatibility check for issue #26.

This module never creates tables, accounts, grants, backups or corrections.
Fail-closed when any column, key, FK, engine or audit trigger differs from
the exact reviewed schema. Intended for the current MariaDB instance only.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from .approval_dryrun import PreflightError

SCHEMA = "loucka_reconstruction"
BATCH = "issue26_batch_events"
FIELD = "issue26_field_events"
COLUMNS = {
    BATCH: {
        "batch_id": ("varchar", "NO", 80),
        "event_type": ("enum", "NO", None),
        "payload_sha256": ("char", "NO", 64),
        "before_image_sha256": ("char", "NO", 64),
        "approval_mac_sha256": ("char", "NO", 64),
        "approver": ("varchar", "NO", 120),
        "operation_count": ("int", "NO", None),
        "event_time": ("timestamp", "NO", None),
    },
    FIELD: {
        "id": ("bigint", "NO", None),
        "batch_id": ("varchar", "NO", 80),
        "event_type": ("enum", "NO", None),
        "target_time": ("bigint", "NO", None),
        "variable": ("varchar", "NO", 64),
        "old_value": ("double", "YES", None),
        "new_value": ("double", "YES", None),
        "source_ref": ("varchar", "NO", 255),
        "unit_epoch_ref": ("varchar", "NO", 255),
        "rule_version": ("varchar", "NO", 120),
        "diagnosis_confidence": ("varchar", "NO", 16),
        "replacement_confidence": ("varchar", "NO", 16),
        "event_time": ("timestamp", "NO", None),
    },
}
KEYS = {
    (BATCH, "PRIMARY"): (True, ("batch_id", "event_type")),
    (FIELD, "PRIMARY"): (True, ("id",)),
    (FIELD, "uniq_issue26_batch_action_target"):
        (True, ("batch_id", "event_type", "target_time", "variable")),
    (FIELD, "idx_issue26_target_variable"): (False, ("target_time", "variable")),
}


def _tuple(row: Any, fields: tuple[str, ...]) -> tuple:
    if isinstance(row, dict):
        return tuple(row[field] for field in fields)
    return tuple(row)


def verify_audit_ddl(cur: Any, *, allow_missing: bool = False) -> dict:
    """Check exact audit tables, refusing partial installs and structural drift."""
    cur.execute(
        "SELECT TABLE_NAME, TABLE_TYPE, ENGINE FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME IN (%s,%s)",
        (SCHEMA, BATCH, FIELD),
    )
    names = {str(name): (kind, engine) for name, kind, engine
             in (_tuple(row, ("TABLE_NAME", "TABLE_TYPE", "ENGINE"))
                 for row in cur.fetchall())}
    if not names:
        if allow_missing:
            return {"status": "NOT_INSTALLED", "tables": 0}
        raise PreflightError("issue26 audit tables are not installed")
    if set(names) != {BATCH, FIELD}:
        raise PreflightError("partial issue26 audit DDL: no writes permitted")
    if any(kind != "BASE TABLE" or engine != "InnoDB" for kind, engine in names.values()):
        raise PreflightError("issue26 audit tables must be InnoDB BASE TABLE")

    cur.execute(
        "SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE,IS_NULLABLE,"
        "CHARACTER_MAXIMUM_LENGTH,COLUMN_TYPE,COLLATION_NAME,EXTRA "
        "FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME IN (%s,%s)",
        (SCHEMA, BATCH, FIELD),
    )
    seen: dict[str, dict[str, tuple]] = defaultdict(dict)
    for row in cur.fetchall():
        table, name, typ, nullable, length, col_type, collation, extra = _tuple(
            row, ("TABLE_NAME", "COLUMN_NAME", "DATA_TYPE", "IS_NULLABLE",
                  "CHARACTER_MAXIMUM_LENGTH", "COLUMN_TYPE", "COLLATION_NAME", "EXTRA")
        )
        seen[table][name] = (typ, nullable, length, col_type, collation, extra)
    for table, expected in COLUMNS.items():
        if set(seen[table]) != set(expected):
            raise PreflightError("issue26 audit column set differs for " + table)
        for name, (typ, nullable, length) in expected.items():
            real = seen[table][name]
            if real[0] != typ or real[1] != nullable:
                raise PreflightError("issue26 audit column type/nullability differs: " + name)
            if length is not None and int(real[2] or 0) != length:
                raise PreflightError("issue26 audit column length differs: " + name)
            if typ == "enum" and str(real[3]).lower() != "enum('apply','rollback')":
                raise PreflightError("issue26 event enum differs")
            if name in {"payload_sha256", "before_image_sha256", "approval_mac_sha256"}:
                if real[4] != "ascii_bin":
                    raise PreflightError("issue26 hash must use ascii_bin collation")
            if name == "id" and "auto_increment" not in str(real[5]).lower():
                raise PreflightError("issue26 journal id must auto_increment")
            if name == "operation_count" and "unsigned" not in str(real[3]).lower():
                raise PreflightError("issue26 operation count must be unsigned")
            if name == "id" and "unsigned" not in str(real[3]).lower():
                raise PreflightError("issue26 event id must be unsigned")

    cur.execute(
        "SELECT TABLE_NAME,INDEX_NAME,NON_UNIQUE,SEQ_IN_INDEX,COLUMN_NAME "
        "FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME IN (%s,%s) "
        "ORDER BY TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX",
        (SCHEMA, BATCH, FIELD),
    )
    keys: dict[tuple[str, str], list[tuple[int, int, str]]] = defaultdict(list)
    for row in cur.fetchall():
        table, name, not_unique, seq, column = _tuple(
            row, ("TABLE_NAME", "INDEX_NAME", "NON_UNIQUE", "SEQ_IN_INDEX", "COLUMN_NAME"))
        keys[(table, name)].append((int(seq), int(not_unique), column))
    for key, (unique, columns) in KEYS.items():
        actual = sorted(keys.get(key, []))
        if tuple(col for _, _, col in actual) != columns:
            raise PreflightError("issue26 journal index differs: " + key[1])
        if any(is_not_unique != (0 if unique else 1) for _, is_not_unique, _ in actual):
            raise PreflightError("issue26 journal index uniqueness differs: " + key[1])
    if not set(KEYS).issubset(keys):
        raise PreflightError("issue26 audit indexes missing")

    cur.execute(
        "SELECT CONSTRAINT_NAME,COLUMN_NAME,ORDINAL_POSITION,"
        "REFERENCED_TABLE_SCHEMA,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME "
        "FROM information_schema.KEY_COLUMN_USAGE "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s "
        "AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY ORDINAL_POSITION",
        (SCHEMA, FIELD),
    )
    fk = [_tuple(r, ("CONSTRAINT_NAME","COLUMN_NAME","ORDINAL_POSITION",
                      "REFERENCED_TABLE_SCHEMA","REFERENCED_TABLE_NAME",
                      "REFERENCED_COLUMN_NAME")) for r in cur.fetchall()]
    if fk != [
        ("fk_issue26_batch_event", "batch_id", 1, SCHEMA, BATCH, "batch_id"),
        ("fk_issue26_batch_event", "event_type", 2, SCHEMA, BATCH, "event_type"),
    ]:
        raise PreflightError("issue26 audit FK missing or altered")

    cur.execute(
        "SELECT TRIGGER_NAME FROM information_schema.TRIGGERS "
        "WHERE TRIGGER_SCHEMA=%s AND EVENT_OBJECT_TABLE IN (%s,%s)",
        (SCHEMA, BATCH, FIELD),
    )
    if cur.fetchone() is not None:
        raise PreflightError("unexpected trigger attached to issue26 journal")

    return {"status": "DDL_VERIFIED", "tables": 2, "indexes_checked": len(KEYS)}
