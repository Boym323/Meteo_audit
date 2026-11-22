#!/usr/bin/env python3
"""Read-only planner and approval-gated INSERT-only MariaDB batch runner."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from meteo_audit.archive_sync import (  # noqa: E402
    PROTECTED_LOWER_BOUND, SyncAction, SyncConflict, SyncError, SyncPlan,
)
from meteo_audit.archive_sync_writer import (  # noqa: E402
    bounded_batch, plan_snapshot, apply_plan, pymysql_connection_from_env,
    read_frozen_source_rows, read_target_rows,
    TARGET_SCHEMA, CURSOR_TABLE,
)
from meteo_audit.archive_sync_frozen import (  # noqa: E402
    LOWER_EXCLUSIVE, UPPER_EXCLUSIVE, PAYLOAD_SHA256, compare_source_rows,
    frozen_plan, load_frozen_payload,
)


def canonical_hash(doc: object) -> str:
    raw = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def read_watermark(target) -> int:
    cur = target.cursor()
    try:
        cur.execute(f"SELECT `watermark` FROM `{TARGET_SCHEMA}`.`{CURSOR_TABLE}` WHERE `sync_name`=%s", ("gw3000-insert-only-v1",))
        row = cur.fetchone()
        if row is None:
            return PROTECTED_LOWER_BOUND
        value = row[0] if not isinstance(row, dict) else row["watermark"]
        return int(value)
    finally:
        cur.close()


def restore_plan(doc: dict) -> SyncPlan:
    return SyncPlan(
        window_start=int(doc["window_start"]),
        window_end_exclusive=int(doc["window_end_exclusive"]),
        captured_source_max=doc.get("captured_source_max"),
        previous_watermark=int(doc["previous_watermark"]),
        proposed_watermark=int(doc["proposed_watermark"]),
        actions=tuple(SyncAction(**x) for x in doc["actions"]),
        conflicts=tuple(SyncConflict(**x) for x in doc["conflicts"]),
    )


def plan_command(args) -> int:
    source = pymysql_connection_from_env("pocasi-loucka.eu", readonly=True)
    target = pymysql_connection_from_env("loucka_reconstruction", readonly=True)
    try:
        watermark = args.watermark if args.watermark is not None else read_watermark(target)
        full = plan_snapshot(source, target, watermark=watermark)
        plan = bounded_batch(full, args.max_rows)
        payload = {
            "schema": "loucka-insert-only-sync-plan-v1",
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "source": "pocasi-loucka.eu.archive",
            "target": "loucka_reconstruction.archive",
            "plan": plan.to_dict(),
        }
        payload["plan_sha256"] = canonical_hash(payload["plan"])
        output = Path(args.output)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"plan_sha256": payload["plan_sha256"], "actions": len(plan.actions),
                          "conflicts": len(plan.conflicts), "captured_source_max": plan.captured_source_max,
                          "proposed_watermark": plan.proposed_watermark, "output": str(output)}, indent=2))
        return 0 if not plan.conflicts else 2
    finally:
        source.close(); target.close()


def frozen_plan_command(args) -> int:
    rows, manifest = load_frozen_payload(ROOT / "data/GW3000_INSERT_ONLY_BACKFILL_PAYLOAD.jsonl",
                                         ROOT / "data/GW3000_INSERT_ONLY_BACKFILL_MANIFEST.json")
    source = pymysql_connection_from_env("pocasi-loucka.eu", readonly=True)
    target = pymysql_connection_from_env("loucka_reconstruction", readonly=True)
    try:
        current_source = read_frozen_source_rows(source, LOWER_EXCLUSIVE, UPPER_EXCLUSIVE)
        compare_source_rows(rows, current_source)
        target_rows = read_target_rows(target, LOWER_EXCLUSIVE, UPPER_EXCLUSIVE)
        watermark = args.watermark if args.watermark is not None else read_watermark(target)
        selected = {r["dateTime"] for r in rows[:args.rows]}
        full = frozen_plan(rows, target_rows, watermark=watermark, timestamps=selected)
        plan = bounded_batch(full, args.max_rows)
        body = {"schema": "gw3000-frozen-backfill-batch-v1", "payload_sha256": PAYLOAD_SHA256,
                "manifest_schema": manifest["schema"], "plan": plan.to_dict()}
        body["plan_sha256"] = canonical_hash(body["plan"])
        Path(args.output).write_text(json.dumps(body, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"mode": "frozen-backfill-preflight", "payload_sha256": PAYLOAD_SHA256,
                          "rows": len(plan.actions), "conflicts": len(plan.conflicts),
                          "first_timestamp": plan.actions[0].timestamp if plan.actions else None,
                          "last_timestamp": plan.actions[-1].timestamp if plan.actions else None,
                          "plan_sha256": body["plan_sha256"], "output": args.output}, indent=2))
        return 0 if not plan.conflicts else 2
    finally:
        source.close(); target.close()


def apply_command(args) -> int:
    if args.mode == "backfill" and not args.backfill_approval_ref:
        raise SyncError("backfill mode requires its separate owner approval reference")
    if args.mode == "continuous" and not args.deployment_approval_ref:
        raise SyncError("continuous mode requires its separate deployment approval reference")
    if __import__("os").environ.get("METEO_SYNC_WRITES_ALLOWED") != "OWNER_APPROVED_INSERT_ONLY":
        raise SyncError("writer disabled: set METEO_SYNC_WRITES_ALLOWED only after the required owner approval")
    payload = json.loads(Path(args.plan_file).read_text(encoding="utf-8"))
    frozen_rows = frozen_manifest = None
    if args.mode == "backfill":
        if payload.get("schema") != "gw3000-frozen-backfill-batch-v1" or payload.get("payload_sha256") != PAYLOAD_SHA256:
            raise SyncError("backfill accepts only a plan bound to the canonical frozen payload")
        frozen_rows, frozen_manifest = load_frozen_payload(ROOT / "data/GW3000_INSERT_ONLY_BACKFILL_PAYLOAD.jsonl",
                                                            ROOT / "data/GW3000_INSERT_ONLY_BACKFILL_MANIFEST.json")
    plan = restore_plan(payload["plan"])
    if canonical_hash(payload["plan"]) != payload.get("plan_sha256"):
        raise SyncError("plan hash mismatch")
    if payload["plan_sha256"] != args.expected_sha256:
        raise SyncError("expected plan SHA-256 does not match")
    if plan.conflicts:
        raise SyncError("plan has conflicts; no writes are allowed")

    source = pymysql_connection_from_env("pocasi-loucka.eu", readonly=True)
    target_ro = pymysql_connection_from_env("loucka_reconstruction", readonly=True)
    target_writer = pymysql_connection_from_env("loucka_reconstruction", readonly=False)
    try:
        if args.mode == "backfill":
            live_source = read_frozen_source_rows(source, LOWER_EXCLUSIVE, UPPER_EXCLUSIVE)
            compare_source_rows(frozen_rows, live_source)
            target_rows = read_target_rows(target_ro, LOWER_EXCLUSIVE, UPPER_EXCLUSIVE)
            timestamps = {a.timestamp for a in plan.actions}
            authorized_rows = {r["dateTime"]: r for r in frozen_rows}
            if any(ts not in authorized_rows or authorized_rows[ts] != dict(plan.actions[i].values)
                   for i, ts in enumerate([a.timestamp for a in plan.actions])):
                raise SyncError("backfill actions differ from canonical frozen payload")
            rechecked = frozen_plan(frozen_rows, target_rows, watermark=plan.previous_watermark, timestamps=timestamps)
            if rechecked.to_dict() != plan.to_dict():
                raise SyncError("approved frozen target state/cursor differs; stop for review")
        else:
            fresh = plan_snapshot(source, target_ro, watermark=plan.previous_watermark)
            fresh = bounded_batch(fresh, len(plan.actions) or args.max_rows)
            if fresh.to_dict() != plan.to_dict():
                raise SyncError("live source/target state differs from continuous plan; replan")
        result = apply_plan(target_writer, plan, batch_id=args.batch_id or str(uuid4()), batch_size=args.max_rows,
                            postcommit_connection=target_ro,
                            authorization_mode="frozen_backfill" if args.mode == "backfill" else "continuous",
                            frozen_payload_sha256=PAYLOAD_SHA256 if args.mode == "backfill" else None)
        result.update({"mode": args.mode, "deployment_approval_ref": args.deployment_approval_ref,
                       "backfill_approval_ref": args.backfill_approval_ref})
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    finally:
        source.close(); target_ro.close(); target_writer.close()



def run_frozen_command(args) -> int:
    """Execute exact frozen canary and remaining batches; safe to restart at committed batch boundaries."""
    import os
    from meteo_audit.archive_sync_writer import _canonical_hash
    rows, manifest = load_frozen_payload(ROOT / "data/GW3000_INSERT_ONLY_BACKFILL_PAYLOAD.jsonl",
                                         ROOT / "data/GW3000_INSERT_ONLY_BACKFILL_MANIFEST.json")
    source = pymysql_connection_from_env("pocasi-loucka.eu", readonly=True)
    target_ro = pymysql_connection_from_env("loucka_reconstruction", readonly=True)
    source_lock = None
    try:
        live = read_frozen_source_rows(source, LOWER_EXCLUSIVE, UPPER_EXCLUSIVE)
        compare_source_rows(rows, live)
        print(json.dumps({"phase":"read-only-preflight","source_rows":len(live),"columns_per_row":80,"verified_values":len(live)*80,"payload_sha256":PAYLOAD_SHA256,"manifest_rows":len(rows)},indent=2),flush=True)
        target_rows = read_target_rows(target_ro, LOWER_EXCLUSIVE, UPPER_EXCLUSIVE)
        # A target row is never accepted as a prior success without exact immutable audit evidence.
        expected = {r["dateTime"]: r for r in rows}
        target_by_ts = {r["dateTime"]: r for r in target_rows}
        if len(target_by_ts) != len(target_rows):
            raise SyncError("duplicate target timestamp")
        cur = target_ro.cursor()
        cur.execute(f"SELECT `batch_id`,`dateTime`,`source_row_sha256` FROM `{TARGET_SCHEMA}`.`archive_sync_audit` WHERE `dateTime` >= %s AND `dateTime` < %s ORDER BY `dateTime`", (LOWER_EXCLUSIVE, UPPER_EXCLUSIVE))
        audit_rows = cur.fetchall()
        cur.execute(f"SELECT `batch_id`,`row_count`,`source_payload_sha256`,`verified_target_postimage_sha256` FROM `{TARGET_SCHEMA}`.`archive_sync_verification` ORDER BY `batch_id`")
        verification_rows = cur.fetchall()
        cur.close()
        audit = {int(x["dateTime"]): x for x in audit_rows}
        if len(audit) != len(audit_rows):
            raise SyncError("duplicate audit evidence for a frozen timestamp")
        for ts, target_row in target_by_ts.items():
            if ts not in expected or target_row != expected[ts]:
                raise SyncError(f"unexpected or differing target row at {ts}")
            ev = audit.get(ts)
            if ev is None or ev["source_row_sha256"] != _canonical_hash(expected[ts]):
                raise SyncError(f"target row {ts} lacks matching approved audit evidence")
        if set(audit) != set(target_by_ts):
            raise SyncError("audit timestamps do not exactly match existing frozen target rows")
        verification = {x["batch_id"]: x for x in verification_rows}
        if len(verification) != len(verification_rows):
            raise SyncError("duplicate post-commit verification batch evidence")
        if args.preflight_only:
            print(json.dumps({"status":"PREFLIGHT_PASS","target_rows":len(target_rows),"audit_rows":len(audit_rows),"cursor":read_watermark(target_ro)},indent=2))
            return 0
        if os.environ.get("METEO_SYNC_WRITES_ALLOWED") != "OWNER_APPROVED_INSERT_ONLY" or not os.environ.get("GW3000_BACKFILL_APPROVAL_REF"):
            raise SyncError("apply requires METEO_SYNC_WRITES_ALLOWED and GW3000_BACKFILL_APPROVAL_REF")
        # Freeze the source snapshot through all batches. Shared row/gap locks prevent
        # concurrent source edits/inserts in this exact timestamp window until completion.
        source_lock = pymysql_connection_from_env("pocasi-loucka.eu", readonly=False)
        source_lock.begin()
        locked_source = read_frozen_source_rows(source_lock, LOWER_EXCLUSIVE, UPPER_EXCLUSIVE, lock_shared=True)
        compare_source_rows(rows, locked_source)

        batches = [("canary", rows[:25])]
        batches.extend((f"batch-{i:03d}", rows[25+i:25+i+100]) for i in range(0, len(rows)-25, 100))
        watermark = read_watermark(target_ro)
        expected_cursor = LOWER_EXCLUSIVE
        newly_applied = 0
        for label, batchrows in batches:
            timestamps = [r["dateTime"] for r in batchrows]
            batch_id = f"gw3000-{label}-{timestamps[0]}-{timestamps[-1]}"
            present = [ts in target_by_ts for ts in timestamps]
            if any(present) and not all(present):
                raise SyncError(f"partial target batch {batch_id}; halt for manual inspection")
            if all(present):
                for ts in timestamps:
                    if audit[ts]["batch_id"] != batch_id:
                        raise SyncError(f"audit batch identity mismatch at {ts}")
                ev = verification.get(batch_id)
                actual_postimage = [target_by_ts[ts] for ts in timestamps]
                if (ev is None or int(ev["row_count"]) != len(batchrows)
                    or ev["source_payload_sha256"] != _canonical_hash(batchrows)
                    or ev["verified_target_postimage_sha256"] != _canonical_hash(actual_postimage)):
                    raise SyncError(f"batch {batch_id} append-only post-commit evidence does not match the current target")
                expected_cursor = timestamps[-1]
                if watermark < expected_cursor:
                    raise SyncError("cursor is behind a fully audited batch")
                continue
            if watermark != expected_cursor:
                raise SyncError("cursor does not identify the next complete batch boundary")
            if os.environ.get("METEO_SYNC_WRITES_ALLOWED") != "OWNER_APPROVED_INSERT_ONLY":
                raise SyncError("writer disabled; set METEO_SYNC_WRITES_ALLOWED after owner approval")
            approval = os.environ.get("GW3000_BACKFILL_APPROVAL_REF", "")
            if not approval:
                raise SyncError("GW3000_BACKFILL_APPROVAL_REF is required")
            timestamps_set = set(timestamps)
            plan = frozen_plan(rows, target_rows, watermark=watermark, timestamps=timestamps_set)
            if len(plan.actions) != len(batchrows) or plan.proposed_watermark != timestamps[-1]:
                raise SyncError("batch plan is not a complete exact frozen insertion set")
            # The held source shared lock protects this exact snapshot against concurrent mutation;
            # action values are still the independently SHA-256-bound immutable payload values.
            writer = pymysql_connection_from_env("loucka_reconstruction", readonly=False)
            verifier = pymysql_connection_from_env("loucka_reconstruction", readonly=True)
            evidence_conn = pymysql_connection_from_env("loucka_reconstruction", readonly=False)
            try:
                result = apply_plan(writer, plan, batch_id=batch_id, batch_size=100,
                    postcommit_connection=verifier, authorization_mode="frozen_backfill",
                    frozen_payload_sha256=PAYLOAD_SHA256)
                # Separate append-only evidence; the legacy immutable audit row's nullable field is intentionally never backfilled.
                evcur = evidence_conn.cursor()
                evcur.execute(f"INSERT INTO `{TARGET_SCHEMA}`.`archive_sync_verification` (`batch_id`,`row_count`,`source_payload_sha256`,`verified_target_postimage_sha256`,`verified_utc`) VALUES (%s,%s,%s,%s,UTC_TIMESTAMP(6))",
                    (batch_id, result["verified_rows"], result["source_payload_hash"], result["verified_target_postimage_hash"]))
                evidence_conn.commit()
                evcur.close()
            except Exception:
                evidence_conn.rollback()
                raise
            finally:
                writer.close(); verifier.close(); evidence_conn.close()
            verification[batch_id] = {"row_count": len(batchrows), "source_payload_sha256": result["source_payload_hash"],
                                      "verified_target_postimage_sha256": result["verified_target_postimage_hash"]}
            for row in batchrows:
                target_by_ts[row["dateTime"]] = row
            target_rows.extend(batchrows)
            for ts in timestamps:
                audit[ts] = {"batch_id": batch_id, "source_row_sha256": _canonical_hash(expected[ts])}
            expected_cursor = watermark = timestamps[-1]
            newly_applied += 1
            print(json.dumps({"batch_id": batch_id, **result}, ensure_ascii=False), flush=True)
            if args.stop_after_batches and newly_applied >= args.stop_after_batches:
                print(json.dumps({"status":"PAUSED_AT_COMMITTED_BATCH_BOUNDARY","completed_this_run":newly_applied,"cursor":watermark}),flush=True)
                return 0
        # Final independent all-row check on a fresh connection.
        final_conn = pymysql_connection_from_env("loucka_reconstruction", readonly=True)
        try:
            final_rows = read_target_rows(final_conn, LOWER_EXCLUSIVE, UPPER_EXCLUSIVE)
            compare_source_rows(rows, final_rows)
            c = final_conn.cursor()
            c.execute(f"SELECT COUNT(*) AS n FROM `{TARGET_SCHEMA}`.`archive_sync_audit` WHERE `dateTime` >= %s AND `dateTime` < %s", (LOWER_EXCLUSIVE, UPPER_EXCLUSIVE))
            audit_count = int(c.fetchone()["n"])
            c.execute(f"SELECT COUNT(*) AS n FROM `{TARGET_SCHEMA}`.`archive_sync_verification`")
            verification_count = int(c.fetchone()["n"])
            c.execute(f"SELECT `watermark` FROM `{TARGET_SCHEMA}`.`archive_sync_cursor` WHERE `sync_name`=%s", ("gw3000-insert-only-v1",))
            cursor = int(c.fetchone()["watermark"])
            c.close()
        finally:
            final_conn.close()
        expected_verification_ids = {f"gw3000-{label}-{batchrows[0]['dateTime']}-{batchrows[-1]['dateTime']}" for label,batchrows in batches}
        if (len(final_rows) != len(rows) or audit_count != len(rows)
            or verification_count != len(batches) or set(verification) != expected_verification_ids
            or cursor != rows[-1]["dateTime"]):
            raise SyncError("final row/audit/verification/cursor count mismatch")
        print(json.dumps({"status":"PASS","rows":len(rows),"compared_values":len(rows)*80,
            "differences":0,"audit_rows":audit_count,"verification_batches":verification_count,
            "cursor":cursor,"payload_sha256":PAYLOAD_SHA256},indent=2))
        return 0
    finally:
        if source_lock is not None:
            source_lock.rollback()
            source_lock.close()
        source.close(); target_ro.close()

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    rf = sub.add_parser("run-frozen", help="preflight, canary, resume, and complete the exact frozen manifest")
    rf.add_argument("--stop-after-batches",type=int,default=0,help="test/support restart at a committed batch boundary")
    rf.add_argument("--preflight-only",action="store_true")
    rf.set_defaults(func=run_frozen_command)
    args = parser.parse_args()
    if hasattr(args, "max_rows") and not 1 <= args.max_rows <= 100:
        parser.error("--max-rows must be between 1 and 100")
    try:
        return args.func(args)
    except Exception as exc:
        print(f"archive-sync stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
