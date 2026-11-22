"""Strict, payload-bound execution path for the approved GW3000 backfill."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from .archive_sync import ARCHIVE_FIELDS, PROTECTED_LOWER_BOUND, SyncAction, SyncError, SyncPlan, validate_action

PAYLOAD_SHA256 = "1b4e953fa85f16f25582db9b177d9dab5d0d9fc30d4e364057760b9cfc7a9aad"
LOWER_EXCLUSIVE = 1_793_286_600
UPPER_EXCLUSIVE = 1_794_682_801
EXPECTED_ROWS = 4_651
FROZEN_NAME = "gw3000-insert-only-backfill-v1"


def row_hash(row: Mapping[str, Any]) -> str:
    raw = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                     allow_nan=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_frozen_payload(payload_path: str | Path, manifest_path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw = Path(payload_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PAYLOAD_SHA256:
        raise SyncError("canonical frozen payload SHA-256 mismatch")
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("schema") != "gw3000-insert-only-backfill-manifest-v1":
        raise SyncError("unexpected frozen manifest schema")
    if manifest.get("payload", {}).get("sha256") != PAYLOAD_SHA256:
        raise SyncError("manifest does not authorize the canonical payload")
    win = manifest.get("source_window", {})
    if (win.get("start_exclusive"), win.get("end_exclusive")) != (LOWER_EXCLUSIVE, UPPER_EXCLUSIVE):
        raise SyncError("frozen manifest window mismatch")
    rows = [json.loads(line) for line in raw.splitlines() if line]
    if len(rows) != EXPECTED_ROWS or len({r.get("dateTime") for r in rows}) != EXPECTED_ROWS:
        raise SyncError("frozen payload row count or timestamp uniqueness mismatch")
    if any(set(row) != ARCHIVE_FIELDS for row in rows):
        raise SyncError("frozen row does not contain the complete 80-column schema")
    timestamps = [row["dateTime"] for row in rows]
    if timestamps != sorted(timestamps) or timestamps[0] <= LOWER_EXCLUSIVE or timestamps[-1] >= UPPER_EXCLUSIVE:
        raise SyncError("frozen timestamps are unordered or outside approved bounds")
    if any(row["usUnits"] != 16 or row["interval"] != 5 for row in rows):
        raise SyncError("frozen payload units/interval mismatch")
    for row in rows:
        # Reuse the production schema and finite-number validation.
        validate_action(SyncAction("INSERT_ROW", row["dateTime"], row, 16, 5), upper_exclusive=UPPER_EXCLUSIVE)
    return rows, manifest


def frozen_plan(rows: list[dict[str, Any]], target_rows: list[dict[str, Any]], *, watermark: int,
                timestamps: set[int] | None = None) -> SyncPlan:
    """Build a batch exclusively from exact canonical payload timestamps."""
    selected = [r for r in rows if timestamps is None or r["dateTime"] in timestamps]
    if timestamps is not None and {r["dateTime"] for r in selected} != timestamps:
        raise SyncError("requested timestamps are not all present in frozen payload")
    target = {r["dateTime"]: r for r in target_rows}
    if len(target) != len(target_rows):
        raise SyncError("duplicate target timestamp in approved window")
    conflicts = []
    actions = []
    for row in selected:
        ts = row["dateTime"]
        if ts <= LOWER_EXCLUSIVE or ts >= UPPER_EXCLUSIVE:
            raise SyncError("frozen timestamp escaped approved bounds")
        existing = target.get(ts)
        if existing is not None:
            if dict(existing) != row:
                raise SyncError(f"target conflict at frozen timestamp {ts}")
            continue
        actions.append(SyncAction("INSERT_ROW", ts, row, 16, 5))
    proposed = max([watermark, *(a.timestamp for a in actions)])
    return SyncPlan(LOWER_EXCLUSIVE, UPPER_EXCLUSIVE, rows[-1]["dateTime"], watermark,
                    proposed, tuple(actions), tuple(conflicts))


def compare_source_rows(payload_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> None:
    """Compare all 80 source values for every timestamp in the frozen set."""
    expected = {r["dateTime"]: r for r in payload_rows}
    actual = {r["dateTime"]: r for r in source_rows}
    if len(actual) != len(source_rows) or set(actual) != set(expected):
        raise SyncError("live source timestamp set differs from frozen payload")
    for ts, row in expected.items():
        got = actual[ts]
        if set(got) != ARCHIVE_FIELDS:
            raise SyncError(f"source row {ts} schema differs from complete 80-column mapping")
        for name in ARCHIVE_FIELDS:
            a, b = row[name], got[name]
            if a is None or b is None:
                equal = a is None and b is None
            elif isinstance(a, (int, float, Decimal)) and isinstance(b, (int, float, Decimal)):
                equal = float(a) == float(b)
            else:
                equal = a == b
            if not equal:
                raise SyncError(f"live source differs from frozen payload at {ts}.{name}")
