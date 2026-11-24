#!/usr/bin/env python3
"""Capture a consistent, read-only operation-level archive diff from MariaDB.

Uses the existing migration package schema and policy. It never writes to either
database. Credentials are read from a private MariaDB option file.
"""
from __future__ import annotations

import argparse
import configparser
import gzip
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pymysql

WATERMARK = 1795541700
PROD = "pocasi-loucka.eu"
RECON = "loucka_reconstruction"
LOCAL = ZoneInfo("Europe/Prague")
EXPECTED_FIELDS = {
    "outTemp": 47, "outHumidity": 20422, "rain": 2201, "rainRate": 59595,
    "extraTemp1": 2, "extraTemp2": 14, "soilTemp1": 13, "soilTemp5": 10,
    "soilTemp6": 21,
}
EXPECTED_TOTAL = 92724
EXPECTED_INSERTS = 10399


def jdefault(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def quote_ident(value: str) -> str:
    return "`" + value.replace("`", "``") + "`"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cnf", type=Path, default=Path(os.environ.get("METEO_DB_CNF", "/root/meteo-loucka-ro.cnf")))
    ap.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()
    if not args.cnf.is_file() or args.cnf.stat().st_mode & 0o077:
        raise SystemExit("credential option file missing or permissions wider than 0600")
    config = configparser.ConfigParser()
    config.read(args.cnf)
    client = config["client"]
    conn = pymysql.connect(
        host=client.get("host", "localhost"), port=client.getint("port", 3306),
        user=client["user"], password=client["password"], database=RECON,
        charset="utf8mb4", cursorclass=pymysql.cursors.SSCursor,
        autocommit=False, connect_timeout=15, read_timeout=900, write_timeout=30,
    )
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    operations_path = out / "FINAL_MIGRATION_OPERATIONS.jsonl.gz"
    errors: list[str] = []
    summary: dict = {}
    try:
        with conn.cursor(pymysql.cursors.Cursor) as cur:
            cur.execute("SET SESSION wait_timeout=3600")
            cur.execute("SET SESSION net_read_timeout=900")
            cur.execute("SET SESSION net_write_timeout=900")
            cur.execute("SET SESSION max_statement_time=300")
            cur.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            cur.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY")
            snapshot_started = datetime.now(timezone.utc).isoformat()
            cur.execute("SELECT DATABASE(), @@hostname, @@server_id, @@version, USER(), CURRENT_USER()")
            identity = cur.fetchone()
            if identity[1] != "lo-infra-db-mariadb01" or int(identity[2]) != 1:
                raise RuntimeError("unexpected MariaDB source identity")

            cur.execute(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='archive' ORDER BY ORDINAL_POSITION", (RECON,)
            )
            columns = [r[0] for r in cur.fetchall()]
            cur.execute(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='archive' ORDER BY ORDINAL_POSITION", (PROD,)
            )
            prod_columns = [r[0] for r in cur.fetchall()]
            if len(columns) != 80 or columns != prod_columns or columns[0] != "dateTime":
                raise RuntimeError(f"archive schemas differ or column count is not 80 ({len(columns)}/{len(prod_columns)})")

            counts = {}
            for schema in (PROD, RECON):
                cur.execute(f"SELECT COUNT(*) FROM {quote_ident(schema)}.archive WHERE dateTime <= %s", (WATERMARK,))
                counts[schema] = int(cur.fetchone()[0])
            cur.execute(
                f"SELECT COUNT(*) FROM {quote_ident(RECON)}.archive r LEFT JOIN {quote_ident(PROD)}.archive p "
                "ON p.dateTime=r.dateTime WHERE r.dateTime <= %s AND p.dateTime IS NULL", (WATERMARK,)
            )
            insert_count = int(cur.fetchone()[0])
            cur.execute(
                f"SELECT COUNT(*) FROM {quote_ident(PROD)}.archive p LEFT JOIN {quote_ident(RECON)}.archive r "
                "ON r.dateTime=p.dateTime WHERE p.dateTime <= %s AND r.dateTime IS NULL", (WATERMARK,)
            )
            production_only = int(cur.fetchone()[0])

            # Pull historical event and candidate provenance from the same snapshot.
            cur.execute(
                f"SELECT id,batch_key,target_time,variable,old_value,new_value,source_database,source_time,source_value,reason,state,created_at,applied_at "
                f"FROM {quote_ident(RECON)}.reconstruction_changes WHERE target_time <= %s ORDER BY id", (WATERMARK,)
            )
            events: dict[tuple[int, str], list[dict]] = defaultdict(list)
            for row in cur:
                ev = dict(zip(("id","batch_key","target_time","variable","old_value","new_value","source_database","source_time","source_value","reason","state","created_at","applied_at"), row))
                events[(int(ev["target_time"]), ev["variable"])].append(ev)
            cur.execute(
                f"SELECT batch_id,ordinal,source_database,source_time,target_time,source_variable,variable,source_unit,target_unit,source_value,proposed_value,rule,rule_version,reason,created_at "
                f"FROM {quote_ident(RECON)}.reconstruction_candidates WHERE target_time <= %s ORDER BY target_time,variable,ordinal", (WATERMARK,)
            )
            candidates: dict[tuple[int, str], list[dict]] = defaultdict(list)
            for row in cur:
                item = dict(zip(("batch_id","ordinal","source_database","source_time","target_time","source_variable","variable","source_unit","target_unit","source_value","proposed_value","rule","rule_version","reason","created_at"), row))
                candidates[(int(item["target_time"]), item["variable"])].append(item)
            candidates_by_time: dict[int, list[dict]] = defaultdict(list)
            for (target_time, variable), values in candidates.items():
                candidates_by_time[target_time].extend({"target_time": target_time, "variable": variable, "candidate": value} for value in values)
            events_by_time: dict[int, list[dict]] = defaultdict(list)
            for (target_time, _variable), values in events.items():
                events_by_time[target_time].extend(values)
            cur.execute(f"SELECT batch_id,state,payload_hash,candidate_count FROM {quote_ident(RECON)}.reconstruction_batches")
            batch_states = {r[0]: {"state": r[1], "payload_hash": r[2], "candidate_count": int(r[3])} for r in cur.fetchall()}

            non_dt = [c for c in columns if c != "dateTime"]
            differences = " OR ".join(f"NOT (p.{quote_ident(c)} <=> r.{quote_ident(c)})" for c in non_dt)
            select_changed = ",".join(["r.dateTime"] + [f"p.{quote_ident(c)}" for c in non_dt] + [f"r.{quote_ident(c)}" for c in non_dt])
            q_changed = (
                f"SELECT {select_changed} FROM {quote_ident(RECON)}.archive r "
                f"JOIN {quote_ident(PROD)}.archive p ON p.dateTime=r.dateTime "
                f"WHERE r.dateTime <= %s AND ({differences}) ORDER BY r.dateTime"
            )
            q_inserts = (
                f"SELECT {','.join('r.'+quote_ident(c) for c in columns)} FROM {quote_ident(RECON)}.archive r "
                f"LEFT JOIN {quote_ident(PROD)}.archive p ON p.dateTime=r.dateTime "
                "WHERE r.dateTime <= %s AND p.dateTime IS NULL ORDER BY r.dateTime"
            )

            op_counts, field_counts, types = Counter(), Counter(), Counter()
            null_clear_count, null_clear_event_count = 0, 0
            new_null_clear_checks, new_null_clear_errors = 0, []
            audit_event_missing_count, audit_state_mismatch_count = 0, 0
            field_source_claim_missing_count = 0
            insert_audit_link_count, insert_source_claim_count = 0, 0
            audit_states = Counter()
            changed_timestamps = set()
            with gzip.GzipFile(filename=str(operations_path), mode="wb", compresslevel=6, mtime=0) as gz:
                def emit(record):
                    gz.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=jdefault, allow_nan=False).encode("utf-8") + b"\n")
                with conn.cursor(pymysql.cursors.SSCursor) as data_cur:
                    data_cur.execute(q_changed, (WATERMARK,))
                    for rec in data_cur:
                        dt = int(rec[0]); old_values = rec[1:1+len(non_dt)]; new_values = rec[1+len(non_dt):]
                        local = datetime.fromtimestamp(dt, LOCAL)
                        row_events = []
                        for field, old, new in zip(non_dt, old_values, new_values):
                            if old == new:
                                continue
                            key = (dt, field)
                            hist = events.get(key, [])
                            event = hist[-1] if hist else None
                            cands = candidates.get(key, [])
                            batch = (event or {}).get("batch_key") or (cands[-1]["batch_id"] if cands else None)
                            state = (event or {}).get("state")
                            op_type = "NULL_CLEAR" if old is not None and new is None else "NULL_FILL" if old is None and new is not None else "VALUE_REPLACE"
                            if op_type == "NULL_CLEAR":
                                null_clear_count += 1
                                if event and event["state"] == "applied" and event["new_value"] is None:
                                    null_clear_event_count += 1
                                if batch in {"qc-extra-temp-outliers-20261123-v1", "qc-soil-negative-outliers-20261123-v1"}:
                                    new_null_clear_checks += 1
                                    good = bool(event and event["state"] == "applied" and event["old_value"] == old and event["new_value"] is None and new is None)
                                    if not good:
                                        new_null_clear_errors.append({"dateTime": dt, "variable": field, "latest_event_id": event["id"] if event else None, "event_old": event["old_value"] if event else None, "production_old": old, "event_new": event["new_value"] if event else None, "reconstruction_new": new, "state": state})
                            audit_state_matches = None
                            if event:
                                audit_states[event["state"]] += 1
                                expected_current = event["new_value"] if event["state"] == "applied" else event["old_value"] if event["state"] == "reverted" else object()
                                audit_state_matches = expected_current == new
                                if not audit_state_matches:
                                    audit_state_mismatch_count += 1
                            else:
                                audit_event_missing_count += 1
                            source_db = (event or {}).get("source_database") or (cands[-1]["source_database"] if cands else None)
                            if not source_db:
                                field_source_claim_missing_count += 1
                            rec_out = {
                                "dateTime": dt, "utc": datetime.fromtimestamp(dt, timezone.utc).isoformat(), "local": local.isoformat(),
                                "operation_type": op_type, "variable": field, "production_value": old, "reconstruction_value": new,
                                "usUnits": rec[1 + non_dt.index("usUnits")] if "usUnits" in non_dt else None,
                                "source_database": source_db,
                                "source_time": (event or {}).get("source_time") or (cands[-1]["source_time"] if cands else None),
                                "source_value": (event or {}).get("source_value") if event else (cands[-1]["source_value"] if cands else None),
                                "source_provenance_status": "AUDIT_OR_CANDIDATE_CLAIM_NOT_DIRECTLY_REQUERIED" if source_db else "SOURCE_CLAIM_MISSING",
                                "audit_event_id": (event or {}).get("id"), "audit_event": event,
                                "audit_history_event_ids": [e["id"] for e in hist], "audit_state_matches_reconstruction": audit_state_matches,
                                "candidate_history": cands, "reconstruction_batch": batch_states.get(batch) if batch else None,
                                "production_approval_status": "NOT_APPROVED",
                            }
                            emit(rec_out); op_counts["FIELD"] += 1; field_counts[field] += 1; types[op_type] += 1
                            changed_timestamps.add(dt)
                    data_cur.execute(q_inserts, (WATERMARK,))
                    for rec in data_cur:
                        row = dict(zip(columns, rec)); dt = int(row["dateTime"])
                        local = datetime.fromtimestamp(dt, LOCAL)
                        cand_events = candidates_by_time.get(dt, [])
                        time_events = events_by_time.get(dt, [])
                        source_schemas = sorted({e["source_database"] for e in time_events if e.get("source_database")})
                        insert_audit_link_count += bool(time_events)
                        insert_source_claim_count += bool(source_schemas or cand_events)
                        emit({
                            "dateTime": dt, "utc": datetime.fromtimestamp(dt, timezone.utc).isoformat(), "local": local.isoformat(),
                            "operation_type": "INSERT", "variable": "__ARCHIVE_ROW__", "production_value": None,
                            "reconstruction_value": row, "full_row": row,
                            "source_evidence": cand_events, "source_schema_claims_from_related_events": source_schemas,
                            "source_provenance_status": "RELATED_AUDIT_CLAIM_NOT_DIRECTLY_REQUERIED" if source_schemas or cand_events else "SOURCE_CLAIM_MISSING",
                            "related_audit_events": time_events,
                            "audit_event_ids_for_timestamp": [e["id"] for e in time_events],
                            "audit_event_id": None, "audit_event_status": "NO_SINGLE_ROW_INSERT_EVENT" if not time_events else "RELATED_FIELD_EVENTS_ONLY",
                            "usUnits": row.get("usUnits"),
                            "production_approval_status": "NOT_APPROVED",
                        })
                        op_counts["INSERT"] += 1; types["INSERT"] += 1
            field_rows = sum(field_counts.values())
            summary = {
                "schema": "loucka-final-live-diff-summary-v1", "snapshot_started_utc": snapshot_started,
                "source_identity": {"database": identity[0], "host": identity[1], "server_id": int(identity[2]), "version": identity[3], "user": identity[4], "current_user": identity[5]},
                "transaction": "REPEATABLE READ; START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY; all source tables are InnoDB",
                "watermark_inclusive": WATERMARK, "watermark_utc": datetime.fromtimestamp(WATERMARK, timezone.utc).isoformat(),
                "archive_rows": {"production": counts[PROD], "reconstruction": counts[RECON]},
                "production_only_timestamps": production_only, "reconstruction_only_timestamps": insert_count,
                "field_operations": field_rows, "field_counts": dict(field_counts), "operation_counts": dict(types),
                "field_operations_missing_audit_event": audit_event_missing_count,
                "field_operations_latest_audit_state_mismatch": audit_state_mismatch_count,
                "field_operation_audit_states": dict(audit_states),
                "field_operations_missing_source_claim": field_source_claim_missing_count,
                "insert_rows_with_related_audit_events": insert_audit_link_count,
                "insert_rows_with_source_claim": insert_source_claim_count,
                "operations_total": field_rows + insert_count, "changed_existing_timestamps": len(changed_timestamps),
                "null_clear_count": null_clear_count,
                "null_clear_applied_event_count": null_clear_event_count,
                "new_temperature_null_clear_count": new_null_clear_checks,
                "new_temperature_null_clear_audit_matches": new_null_clear_checks - len(new_null_clear_errors),
                "new_temperature_null_clear_audit_errors": new_null_clear_errors, "schema_columns": len(columns),
                "operations_file": operations_path.name,
                "production_approval": "No production approval exists in reconstruction audit state; every operation is explicitly NOT_APPROVED.",
                "validation": "PASS" if counts[PROD] == 1687316 and counts[RECON] == 1697715 and production_only == 0 and insert_count == EXPECTED_INSERTS and field_rows == 82325 and field_counts == EXPECTED_FIELDS and null_clear_count == 895 and null_clear_event_count == 895 and new_null_clear_checks == 60 and not new_null_clear_errors else "REVIEW_REQUIRED",
                "expected_baseline": {"production_rows": 1687316, "reconstruction_rows": 1697715, "inserts": EXPECTED_INSERTS, "field_operations": 82325, "total": EXPECTED_TOTAL, "changed_timestamps": 80237, "field_counts": EXPECTED_FIELDS, "null_clear_total_including_prior_invalidations": 895, "new_temperature_null_clear": 60},
            }
            summary["operations_sha256"] = digest_file(operations_path)
            summary["operations_size_bytes"] = operations_path.stat().st_size
            cur.execute("COMMIT")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    summary_path = out / "FINAL_MIGRATION_DIFF_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    repo = out.parent
    manifest_path = repo / "FINAL_MIGRATION_MANIFEST.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["generated_at_utc"] = summary["snapshot_started_utc"]
        manifest["snapshot"].update({
            "watermark_inclusive": WATERMARK,
            "watermark_utc": summary["watermark_utc"],
            "source_identity": summary["source_identity"],
            "isolation_level": summary["transaction"],
        })
        manifest["audit_baseline"] = {
            "reconstruction_rows_at_watermark": counts[RECON],
            "production_rows_at_watermark": counts[PROD],
            "inserts": insert_count,
            "field_updates": field_rows,
            "operations_total": field_rows + insert_count,
            "changed_existing_timestamps": len(changed_timestamps),
            "production_timestamps_missing_from_reconstruction": production_only,
            "columns_with_differences": dict(field_counts),
        }
        manifest["operation_types"] = ["INSERT", "NULL_FILL", "NULL_CLEAR", "VALUE_REPLACE"]
        manifest["null_clear_audit"] = {
            "all_null_clear_operations_in_diff": null_clear_count,
            "all_null_clears_linked_to_applied_null_audit_event": null_clear_event_count,
            "new_temperature_null_clear_operations": new_null_clear_checks,
            "new_temperature_null_clear_exact_audit_matches": new_null_clear_checks - len(new_null_clear_errors),
            "new_temperature_null_clear_audit_errors": new_null_clear_errors,
            "prior_rain_and_humidity_invalidations_are_separate_from_the_60_new_temperature_clears": True,
        }
        manifest["audit_reconciliation"] = {
            "field_operations_missing_audit_event": audit_event_missing_count,
            "field_operations_latest_audit_state_mismatch": audit_state_mismatch_count,
            "field_operation_audit_states": dict(audit_states),
            "note": "Latest event state mismatch is preserved as an explicit review risk; it does not override the current archive value.",
        }
        manifest["production_approval"] = "NOT_APPROVED_FOR_EVERY_OPERATION; reconstruction audit state is not production approval."
        manifest["production_migration"] = "NO-GO pending isolated-instance restore, test migration, WeeWX daily-statistics test and whole-migration rollback."
        manifest["production_changed"] = False
        manifest["detail_artifacts"] = [
            "final_migration_package/FINAL_MIGRATION_OPERATIONS.jsonl.gz",
            "final_migration_package/FINAL_MIGRATION_DIFF_SUMMARY.json",
            "final_migration_package/scripts/capture_final_migration_diff.py",
            "FINAL_DATABASE_AUDIT.md", "WIND_QUALITY_REPORT.md",
            "final_migration_package/MIGRATION_ROLLBACK_PLAN.md",
        ]
        manifest["hashes"] = {
            "operations_sha256": summary["operations_sha256"],
            "operations_size_bytes": summary["operations_size_bytes"],
            "summary_sha256": digest_file(summary_path),
            "capture_script_sha256": digest_file(Path(__file__).resolve()),
            "all_operations_digest_status": summary["validation"],
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary.get("validation") == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
