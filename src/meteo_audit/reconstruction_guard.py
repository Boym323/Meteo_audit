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

# Historical effects verified by bounded SELECT snapshots. These are immutable
# expected audit values, not meteorological proof that a replacement was right.
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
    "rain_daily_reset_backup_2009_2011_v1": (328, 175.14, 0, 328, 0),
    "rain_phase_a_201006_backup_20261030_v1": (30, 161.76, 18, 12, 18),
    "rain_phase_a_backup_20261030_v1": (2, 61.22, 1, 1, 1),
}
BACKUP_BATCHES = {
    "rain_daily_reset_backup_2009_2011_v1": "rain-2009-2011-utc-midnight-reset-v1",
    "rain_phase_a_201006_backup_20261030_v1": "rain-phaseA-june2010-corrected-20261030-v1",
    "rain_phase_a_backup_20261030_v1": "rain-phaseA-apply-20261030-v1",
}
SUPERSEDED_NULL_BATCH = "rain-2010-2011-phaseA-unknown-null-review-v1"
SUPERSEDED_NULL_TARGETS = 19
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

    superseded_rows = _parse(read(
        "SELECT COUNT(*), COUNT(DISTINCT c.target_time), COUNT(DISTINCT c.variable), "
        "SUM(c.variable='rain'), SUM(c.variable='rainRate'), "
        "SUM(c.state='applied'), SUM(c.old_value=0), SUM(c.new_value IS NULL), "
        "SUM((c.variable='rain' AND a.rain <=> c.new_value) OR "
        "(c.variable='rainRate' AND a.rainRate <=> c.new_value)), "
        "COUNT(DISTINCT c.target_time,c.variable) "
        "FROM reconstruction_changes c JOIN archive a ON a.dateTime=c.target_time "
        "WHERE c.batch_key='" + SUPERSEDED_NULL_BATCH + "'"
    ), 10, "known Phase A supersession")
    expected_supersession = [
        2 * SUPERSEDED_NULL_TARGETS, SUPERSEDED_NULL_TARGETS, 2,
        SUPERSEDED_NULL_TARGETS, SUPERSEDED_NULL_TARGETS,
        2 * SUPERSEDED_NULL_TARGETS, 2 * SUPERSEDED_NULL_TARGETS,
        2 * SUPERSEDED_NULL_TARGETS, 2 * SUPERSEDED_NULL_TARGETS,
        2 * SUPERSEDED_NULL_TARGETS,
    ]
    observed_supersession = [int(value) for value in superseded_rows[0]] if len(superseded_rows) == 1 else []
    if observed_supersession != expected_supersession:
        errors.append("Phase A supersession event/current-archive chain differs from baseline")

    history_rows = _parse(read(
        "SELECT state,COUNT(*),COUNT(DISTINCT batch_key),"
        "COUNT(DISTINCT target_time,variable) FROM reconstruction_changes "
        "GROUP BY state ORDER BY state"
    ), 4, "reconstruction_changes state summary")
    history = {}
    for state, event_count, batch_count, target_count in history_rows:
        if state not in {"applied", "reverted"} or state in history:
            errors.append("unexpected or duplicate reconstruction_changes state")
            continue
        events, batches, targets = int(event_count), int(batch_count), int(target_count)
        if events < targets or batches < 1 or targets < 1:
            errors.append(f"{state}: invalid aggregate event counts")
        history[state] = {
            "event_rows": events, "batches": batches, "distinct_targets": targets,
            "additional_events_on_existing_targets": events - targets,
        }
    if set(history) != {"applied", "reverted"}:
        errors.append("reconstruction_changes state summary incomplete")

    staging_rows = _parse(read(
        "SELECT COUNT(*),SUM(b.candidate_count),SUM(COALESCE(c.stored_count,0)),"
        "SUM(b.candidate_count<>COALESCE(c.stored_count,0)),"
        "COALESCE(SUM(c.duplicate_pairs),0),"
        "SUM(GREATEST(b.candidate_count-COALESCE(c.stored_count,0),0)) "
        "FROM reconstruction_batches b LEFT JOIN ("
        "SELECT batch_id,COUNT(*) AS stored_count,"
        "COUNT(*)-COUNT(DISTINCT target_time,variable) AS duplicate_pairs "
        "FROM reconstruction_candidates GROUP BY batch_id"
        ") c ON c.batch_id=b.batch_id"
    ), 6, "staged candidate inventory")
    orphan_candidates = _parse(read(
        "SELECT COUNT(*) FROM reconstruction_candidates c "
        "LEFT JOIN reconstruction_batches b ON b.batch_id=c.batch_id "
        "WHERE b.batch_id IS NULL"
    ), 1, "orphan staged candidates")
    candidate_history_rows = _parse(read(
        "SELECT b.state,COUNT(*),COUNT(DISTINCT c.target_time,c.variable),"
        "SUM(EXISTS(SELECT 1 FROM reconstruction_changes h "
        "WHERE h.target_time=c.target_time AND BINARY h.variable=BINARY c.variable)) "
        "FROM reconstruction_candidates c JOIN reconstruction_batches b "
        "ON b.batch_id=c.batch_id GROUP BY b.state ORDER BY b.state"
    ), 4, "candidate/history overlap")
    duplicate_candidate_pairs = _parse(read(
        "SELECT COUNT(*) FROM (SELECT target_time,variable "
        "FROM reconstruction_candidates GROUP BY target_time,variable "
        "HAVING COUNT(DISTINCT batch_id)>1) d"
    ), 1, "cross-batch candidate duplicates")
    staging = {}
    if len(staging_rows) != 1 or len(orphan_candidates) != 1:
        errors.append("staged candidate inventory unavailable")
    else:
        batch_count, declared, stored, mismatched, duplicate_pairs, missing_rows = map(int, staging_rows[0])
        orphan_count = int(orphan_candidates[0][0])
        staging = {
            "batch_count": batch_count, "declared_candidates": declared,
            "stored_candidates": stored, "batches_with_count_mismatch": mismatched,
            "duplicate_pairs_within_batches": duplicate_pairs,
            "candidate_rows_missing": missing_rows, "orphan_candidate_rows": orphan_count,
            "cross_batch_duplicate_target_pairs": int(duplicate_candidate_pairs[0][0])
            if len(duplicate_candidate_pairs) == 1 else None,
            "history_overlap_by_state": {
                state: {
                    "candidate_rows": int(candidate_count),
                    "distinct_target_pairs": int(target_count),
                    "rows_overlapping_existing_history": int(overlap_count),
                }
                for state, candidate_count, target_count, overlap_count in candidate_history_rows
            },
        }
        if (mismatched or duplicate_pairs or missing_rows or orphan_count
                or len(duplicate_candidate_pairs) != 1):
            errors.append("staged candidate count/identity differs from batch metadata")
        if {row[0] for row in candidate_history_rows} != {"cancelled", "pending"}:
            errors.append("staged candidate states differ from the expected pending/cancelled set")
        for state, candidate_count, target_count, overlap_count in candidate_history_rows:
            if state not in {"pending", "cancelled"} or int(overlap_count) > int(candidate_count) or int(target_count) > int(candidate_count):
                errors.append("candidate/history overlap summary is inconsistent")

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
    for name, (count, expected_mm, expected_superseded, expected_zero, expected_null) in BACKUPS.items():
        initial_batch = BACKUP_BATCHES[name]
        rows = _parse(read(
            "SELECT COUNT(*),SUM(i.event_count=1),"
            "SUM(i.event_count IS NULL OR i.event_count=0),SUM(i.event_count>1),"
            "SUM(i.event_count=1 AND i.old_value <=> b.rain_before),"
            "SUM(i.event_count=1 AND i.applied_count=1),"
            "SUM(i.event_count=1 AND i.zero_count=1),SUM(l.state='applied'),"
            "SUM(l.batch_key='" + SUPERSEDED_NULL_BATCH + "'),SUM(a.rain=0),"
            "SUM(a.rain IS NULL),SUM(a.dateTime IS NOT NULL AND a.rainRate <=> a.rain),"
            "SUM(a.dateTime IS NOT NULL AND a.rain <=> CASE l.state "
            "WHEN 'applied' THEN l.new_value WHEN 'reverted' THEN l.old_value END),"
            "SUM(l.id=i.event_id),SUM(a.dateTime IS NOT NULL),"
            "ROUND(SUM(b.rain_before)*10,5) FROM " + name + " b "
            "LEFT JOIN (SELECT target_time,COUNT(id) event_count,MAX(id) event_id,"
            "MAX(old_value) old_value,SUM(state='applied') applied_count,"
            "SUM(new_value=0) zero_count FROM reconstruction_changes "
            "WHERE batch_key='" + initial_batch + "' AND variable='rain' "
            "GROUP BY target_time) i ON i.target_time=b.dateTime "
            "LEFT JOIN reconstruction_changes l ON l.target_time=b.dateTime "
            "AND l.variable='rain' AND l.id=(SELECT c2.id FROM reconstruction_changes c2 "
            "WHERE c2.target_time=b.dateTime AND c2.variable='rain' "
            "ORDER BY c2.created_at DESC,c2.id DESC LIMIT 1) "
            "LEFT JOIN archive a ON a.dateTime=b.dateTime"
        ), 16, name)
        if len(rows) != 1:
            errors.append(f"{name}: missing backup result")
            continue
        values = [int(value) if index < 15 else float(value)
                  for index, value in enumerate(rows[0])]
        (found, exactly_one, missing, multiple, old_match, initial_applied,
         initial_zero, latest_applied, superseded, current_zero, current_null,
         rate_matches_rain_state, matches_latest, initial_latest, archive_rows, total) = values
        backups[name] = {
            "rows": found, "initial_events": exactly_one, "missing_initial_events": missing,
            "duplicate_initial_events": multiple, "backup_old_values_match": old_match,
            "initial_events_applied": initial_applied, "initial_events_zero": initial_zero,
            "latest_events_applied": latest_applied, "superseded_to_unknown_null": superseded,
            "current_zero": current_zero, "current_null": current_null,
            "current_rainRate_matches_rain_state": rate_matches_rain_state,
            "current_matches_latest_event": matches_latest,
            "initial_event_still_latest": initial_latest,
            "archive_rows_present": archive_rows, "original_rain_mm": total,
        }
        expected_profile = [count, count, 0, 0, count, count, count, count,
                            expected_superseded, expected_zero, expected_null, count,
                            count, count - expected_superseded, count, expected_mm]
        if values[:15] != expected_profile[:15] or not _close(total, expected_mm):
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
        "superseded_null_review": {
            "batch_id": SUPERSEDED_NULL_BATCH,
            "target_timestamps": SUPERSEDED_NULL_TARGETS,
            "field_events": 2 * SUPERSEDED_NULL_TARGETS,
            "all_current_values_match": observed_supersession == expected_supersession,
        },
        "change_history": history,
        "staged_candidates": staging,
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
