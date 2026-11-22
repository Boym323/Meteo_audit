"""Fail-closed, read-only guard for reconstruction history and proposed batches.

This module has NO SQL write path. A passing preflight is NOT permission to apply.
Use the existing meteo_audit.db.query() adapter (READ ONLY transaction).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Callable

from .db import ALLOWED_DATABASES, query

Reader = Callable[[str], list[str]]

# Baseline verified by SELECT on 2026-10-30. These are immutable *expected*
# historical effects, not meteorological proof that proposed zeros were right.
APPLIED = {
    ("rain-2009-2011-utc-midnight-reset-v1", "rain"): (328, 175.14),
    ("rain-phaseA-june2010-corrected-20261030-v1", "rain"): (30, 161.76),
    ("rain-phaseA-apply-20261030-v1", "rain"): (2, 61.22),
    ("rain-phaseA-apply-20261030-v1", "rainRate"): (1, None),
    ("rainrate-restore-2009-2025-v1", "rainRate"): (58936, None),
}
CANCELLED = {
    "loucka-rain-phaseA-201006-review-20261030-v1": (
        16, "79e02da07723905d46c4e861e0e096fa6651db9a291c49733781036134efaa11"
    ),
    "loucka-rain-phaseA-confirmed-20261030-v1": (
        3, "fff346be13992b9cb678ed2b395455cf24f9e459d841a82bd087494a55591a30"
    ),
}
BACKUPS = {
    "rain_daily_reset_backup_2009_2011_v1": (328, 175.14),
    "rain_phase_a_201006_backup_20261030_v1": (30, 161.76),
    "rain_phase_a_backup_20261030_v1": (2, 61.22),
}
ARCHIVE_ROWS_AT_BASELINE = 1679802  # Historical reference, NOT fixed invariant.
JULY_2021_MM = 42.5673
JULY_START_EXCLUSIVE = 1625090400
JULY_END_INCLUSIVE = 1627768800
SAFE_VARIABLES = frozenset(("rain", "rainRate"))
ID_PATTERN = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9_-]{2,63}\Z")


class GuardError(ValueError):
    """Preflight rejected a request without making any database changes."""


def _parse(lines: list[str], width: int, label: str) -> list[list[str]]:
    result: list[list[str]] = []
    for line in lines:
        parts = line.split("\t")
        if len(parts) != width:
            raise GuardError(f"{label}: unexpected result width, fail closed")
        result.append(parts)
    return result


def _close(actual: float, expected: float, *, tolerance: float = 0.001) -> bool:
    return math.isfinite(actual) and abs(actual - expected) <= tolerance


def inspect_baseline(read: Reader) -> dict:
    """Verify historical audit, backups and boundary-safe rainfall; no writes."""
    errors: list[str] = []
    keys = sorted({k for k, _ in APPLIED})
    keylist = ",".join("'" + key + "'" for key in keys)
    rows = _parse(read(
        "SELECT batch_key, variable, state, COUNT(*), "
        "ROUND(SUM(CASE WHEN variable='rain' THEN old_value-new_value "
        "ELSE 0 END)*10, 5) "
        "FROM reconstruction_changes WHERE batch_key IN (" + keylist + ") "
        "GROUP BY batch_key,variable,state ORDER BY batch_key,variable,state"
    ), 5, "reconstruction_changes")
    observations = {}
    for batch, variable, state, count, mm in rows:
        key = (batch, variable)
        if key in observations:
            errors.append(f"{batch}/{variable}: duplicate state group")
        observations[key] = {"state": state, "count": int(count), "rain_delta_mm": float(mm)}
    for (batch, variable), (expected_count, expected_mm) in APPLIED.items():
        observed = observations.get((batch, variable))
        if observed is None or observed["state"] != "applied" or observed["count"] != expected_count:
            errors.append(f"{batch}/{variable}: missing or changed applied audit")
        elif expected_mm is not None and not _close(observed["rain_delta_mm"], expected_mm):
            errors.append(f"{batch}/{variable}: changed historical rain delta")
    if len(observations) != len(APPLIED):
        errors.append("applied audit group count differs from baseline")

    batch_ids = ",".join("'" + key + "'" for key in sorted(CANCELLED))
    canceled_rows = _parse(read(
        "SELECT batch_id,state,candidate_count,payload_hash FROM reconstruction_batches "
        "WHERE batch_id IN (" + batch_ids + ") ORDER BY batch_id"
    ), 4, "reconstruction_batches")
    canceled = {}
    for batch_id, state, count, digest in canceled_rows:
        canceled[batch_id] = {"state": state, "candidate_count": int(count), "payload_hash": digest}
    for batch_id, (expected_count, digest) in CANCELLED.items():
        seen = canceled.get(batch_id)
        if seen is None or seen != {
            "state": "cancelled", "candidate_count": expected_count, "payload_hash": digest
        }:
            errors.append(f"{batch_id}: source proposal unexpectedly changed")
    if len(canceled_rows) != len(CANCELLED):
        errors.append("expected cancelled proposal count differs")

    backups = {}
    for name, (count, expected_mm) in BACKUPS.items():
        rows = _parse(read(
            "SELECT COUNT(*), SUM(a.rain=0 AND a.rainRate=0), "
            "ROUND(SUM(b.rain_before)*10,5) "
            "FROM archive a JOIN " + name + " b ON b.dateTime=a.dateTime"
        ), 3, name)
        if len(rows) != 1:
            errors.append(f"{name}: missing backup result")
            continue
        found, zero, total = rows[0]
        backups[name] = {"rows": int(found), "zeroed": int(zero), "original_rain_mm": float(total)}
        if int(found) != count or int(zero) != count or not _close(float(total), expected_mm):
            errors.append(f"{name}: backup/current archive inconsistency")

    totals = _parse(read(
        "SELECT COUNT(*), ROUND(SUM(CASE WHEN dateTime>" + str(JULY_START_EXCLUSIVE) +
        " AND dateTime<=" + str(JULY_END_INCLUSIVE) +
        " THEN COALESCE(rain,0) ELSE 0 END)*10,4) FROM archive"
    ), 2, "archive")
    if len(totals) != 1:
        errors.append("archive count or July baseline unavailable")
        archive_count, july_mm = None, None
    else:
        archive_count, july_mm = int(totals[0][0]), float(totals[0][1])
        if not _close(july_mm, JULY_2021_MM, tolerance=0.0001):
            errors.append("July 2021 rainfall invariant changed")
    return {
        "verified": not errors,
        "errors": errors,
        "archive_count": archive_count,
        "archive_count_reference_only": ARCHIVE_ROWS_AT_BASELINE,
        "july_2021_mm": july_mm,
        "applied": [{"batch_id": k[0], "variable": k[1], **v}
                    for k, v in sorted(observations.items())],
        "cancelled": canceled,
        "backups": backups,
        "notes": [
            "Archive row count can grow; it is not a blocking invariant.",
            "payload_hash is the staging proposal payload digest, NOT a source-data snapshot hash.",
            "Original Navicat 2021 SQL hash and before-image provenance remain unknown.",
            "Observed applied status does not prove the physical correctness of a replacement value."
        ],
    }


def _number_or_none(value: object, name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GuardError(f"{name} must be a JSON number or null")
    number = float(value)
    if not math.isfinite(number):
        raise GuardError(f"{name} is non-finite")
    return number


def _same(actual: float | None, expected: float | None) -> bool:
    if actual is None or expected is None:
        return actual is expected
    return math.isclose(actual, expected, abs_tol=1e-12, rel_tol=0)


def _read_value(raw: str) -> float | None:
    return None if raw in ("NULL", "\\N") else float(raw)


def inspect_proposal(document: object, read: Reader, baseline: dict) -> dict:
    """Reject reused batches, protected/overlapping timestamps and stale values.

    This function *never* authorizes APPLY: even a clean result means only that
    no conflicting previous audit was found during the read-only preflight.
    """
    if not baseline.get("verified"):
        raise GuardError("Baseline failed; new candidates are blocked")
    if not isinstance(document, dict):
        raise GuardError("Candidate manifest must be an object")
    batch_id = document.get("batch_id")
    if not isinstance(batch_id, str) or not ID_PATTERN.fullmatch(batch_id):
        raise GuardError("Invalid batch_id")
    candidates = document.get("candidates")
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 100:
        raise GuardError("Expected 1..100 candidates")
    if batch_id in CANCELLED or batch_id in {key for key, _ in APPLIED}:
        raise GuardError("Historical batch ID may never be reused")
    identities = set()
    for item in candidates:
        if not isinstance(item, dict):
            raise GuardError("Candidate must be an object")
        timestamp = item.get("target_time")
        variable = item.get("variable")
        if isinstance(timestamp, bool) or not isinstance(timestamp, int) or not 0 < timestamp < 2147483647:
            raise GuardError("target_time must be a positive UTC integer epoch")
        if not isinstance(variable, str) or variable not in SAFE_VARIABLES:
            raise GuardError("Only rain and rainRate are supported by this first guard")
        key = (timestamp, variable)
        if key in identities:
            raise GuardError("Duplicate target_time/variable within proposal")
        identities.add(key)
        if "expected_old_value" not in item or "proposed_value" not in item:
            raise GuardError("A before/after value is required, including explicit JSON null")
        old = _number_or_none(item["expected_old_value"], "expected_old_value")
        new = _number_or_none(item["proposed_value"], "proposed_value")
        if _same(old, new):
            raise GuardError("No-op proposal must not be staged")
        if not isinstance(item.get("source_database"), str) or item["source_database"] not in ALLOWED_DATABASES:
            raise GuardError("source_database is not allowlisted")
        if (isinstance(item.get("source_time"), bool) or not isinstance(item.get("source_time"), int)
                or not 0 < item["source_time"] < 2147483647):
            raise GuardError("source_time must be UTC integer epoch")
        if not isinstance(item.get("reason"), str) or len(item["reason"].strip()) < 12:
            raise GuardError("Candidate must have a concrete reason")
        if item.get("diagnosis_confidence") not in ("HIGH", "MEDIUM", "LOW", "UNRESOLVED"):
            raise GuardError("diagnosis_confidence missing or invalid")
        if item.get("replacement_confidence") not in ("HIGH", "MEDIUM", "LOW", "UNRESOLVED"):
            raise GuardError("replacement_confidence missing or invalid")

    if _parse(read(
        "SELECT batch_id,state FROM reconstruction_batches WHERE batch_id='" + batch_id + "'"
    ), 2, "batch_id"):
        raise GuardError("Batch ID already exists in reconstruction_batches")
    if _parse(read(
        "SELECT batch_key,state FROM reconstruction_changes WHERE batch_key='" + batch_id +
        "' LIMIT 1"
    ), 2, "batch_key"):
        raise GuardError("Batch ID already exists in reconstruction_changes")

    times = ",".join(str(t) for t in sorted({t for t, _ in identities}))
    historic = _parse(read(
        "SELECT target_time,variable,batch_key,state FROM reconstruction_changes "
        "WHERE target_time IN (" + times + ")"
    ), 4, "prior changes")
    collisions = sorted({
        (int(t), var, batch, state) for t, var, batch, state in historic
        if (int(t), var) in identities
    })
    if collisions:
        raise GuardError(
            f"Target overlaps {len(collisions)} existing audit records; "
            "never restage applied/prepared/cancelled corrections"
        )
    prior_candidates = _parse(read(
        "SELECT c.target_time,c.variable,c.batch_id,b.state "
        "FROM reconstruction_candidates c "
        "JOIN reconstruction_batches b ON b.batch_id=c.batch_id "
        "WHERE c.target_time IN (" + times + ")"
    ), 4, "prior candidate proposals")
    candidate_collisions = [
        (int(t), variable, batch, state)
        for t, variable, batch, state in prior_candidates
        if (int(t), variable) in identities
    ]
    if candidate_collisions:
        raise GuardError(
            f"Target overlaps {len(candidate_collisions)} historical candidate proposals; "
            "cancelled/pending proposals may not be silently resurrected"
        )
    existing = _parse(read(
        "SELECT dateTime,rain,rainRate FROM archive WHERE dateTime IN (" + times + ")"
    ), 3, "archive before-image")
    before = {
        (int(time), var): _read_value(value)
        for time, rain, rate in existing
        for var, value in (("rain", rain), ("rainRate", rate))
    }
    for item in candidates:
        key = (item["target_time"], item["variable"])
        if key not in before:
            raise GuardError("Target timestamp is absent from archive")
        if not _same(before[key], _number_or_none(item["expected_old_value"], "expected_old_value")):
            raise GuardError("Expected previous value does not match current archive")
    canonical = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "batch_id": batch_id,
        "candidate_count": len(candidates),
        "proposal_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "duplicate_audit_targets": 0,
        "archive_precondition_mismatch": 0,
        "preflight_clean": True,
        "authorized_to_apply": False,
        "message": "Read-only preflight only. Explicit approval, backup and atomic CAS are still required."
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only reconstruction audit / preflight")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--proposal", type=Path, help="Optional JSON candidate manifest; never applied")
    args = parser.parse_args()
    reader = lambda sql: query(sql, env_file=args.env_file)
    try:
        baseline = inspect_baseline(reader)
        result: dict = {"baseline": baseline}
        if args.proposal:
            # Use local file supplied by operator; no network and no write.
            document = json.loads(args.proposal.read_text(encoding="utf-8"))
            result["preflight"] = inspect_proposal(document, reader, baseline)
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        return 0 if baseline["verified"] else 2
    except (GuardError, RuntimeError, ValueError, OSError) as exc:
        # No credentials or raw SQL are logged by this CLI.
        print(json.dumps({"verified": False, "authorized_to_apply": False,
                          "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
