#!/usr/bin/env python3
"""Issue #26 operator runner, using ONLY the pre-existing loucka_audit account.

Default is --mode status (read-only). No CREATE USER, GRANT or DDL.
A live field APPLY or ROLLBACK requires a previously reviewed, exactly signed
per-batch receipt, --execute, an interactive exact phrase, fresh row locks and
SQL CAS. This script NEVER self-approves a batch and cannot target production.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import stat
import sys

# When invoked as ``python scripts/issue26_operator.py``, Python puts the
# scripts directory first on sys.path. Its meteo_audit.py helper shadows the
# actual src/meteo_audit package unless src is explicitly preferred.
_REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if _REPO_SRC.is_dir():
    sys.path.insert(0, str(_REPO_SRC))

from meteo_audit.approval_dryrun import CandidateBatch, FieldCorrection, PreflightError
from meteo_audit.approval_gate import (
    SignedApproval, challenge_for, verify_exact_batch, verify_fresh_snapshot,
)
from meteo_audit.issue26_audit_ddl_guard import verify_audit_ddl
from meteo_audit.issue26_transaction import (
    TARGET, APPROVE_ROLLBACK, _check_rain, _assert_target,
    apply_approved_batch, rollback_approved_batch, sql_preflight,
)

EXPECTED_HOST = "lo-infra-db-mariadb01"
EXPECTED_SERVER_ID = 1
EXISTING_ACCOUNT = "loucka_audit@%"
READ_ONLY_ACCOUNT = "loucka_web_ro@192.168.0.131"
REVIEW_SCHEMA = "loucka-issue26-readonly-review-v1"
APPLY_CONFIRM = "APLIKUJI-DAVKU:"


def _json_file(path: str) -> object:
    p = Path(path)
    if not p.is_absolute() or p.is_symlink() or not p.is_file():
        raise PreflightError("JSON evidence must be absolute, existing and non-symlink")
    return json.loads(p.read_text(encoding="utf-8"))


def _private_file(name: str) -> Path:
    p = Path(name)
    if not p.is_absolute() or p.is_symlink():
        raise PreflightError("private file must be absolute and not a symlink")
    info = p.stat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
            or info.st_mode & 0o077 or not info.st_mode & stat.S_IRUSR):
        raise PreflightError("private file must be owned by operator and mode 0600")
    return p


def _signed_receipt(path: str) -> SignedApproval:
    private = _private_file(path)
    data = json.loads(private.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != set(SignedApproval.__dataclass_fields__):
        raise PreflightError("signed receipt has unexpected JSON fields")
    return SignedApproval(**data)


def _manifest(path: str) -> CandidateBatch:
    raw = _json_file(path)
    if not isinstance(raw, dict) or set(raw) != {
        "schema", "target", "batch_id", "operations",
    } or not isinstance(raw["operations"], list):
        raise PreflightError("manifest has wrong structure")
    operations = tuple(FieldCorrection(**item) for item in raw["operations"])
    return CandidateBatch(raw["batch_id"], operations, raw["schema"], raw["target"])


def _review(path: str, batch: CandidateBatch) -> dict:
    item = _json_file(path)
    if (not isinstance(item, dict)
            or item.get("schema") != REVIEW_SCHEMA
            or item.get("status") != "READ_ONLY_SQL_SNAPSHOT_NOT_APPROVED"
            or item.get("db_writes") != 0
            or item.get("owner_approval_granted") is not False
            or item.get("audit_schema") not in {
                "PRESENT_NOT_DDL_VERIFIED", "NOT_INSTALLED",
            }):
        raise PreflightError("not a verified read-only SQL review artifact")
    identity = item.get("identity")
    if (not isinstance(identity, dict)
            or identity.get("database") != TARGET
            or identity.get("hostname") != EXPECTED_HOST
            or identity.get("server_id") != EXPECTED_SERVER_ID
            or identity.get("current_user") not in (EXISTING_ACCOUNT, READ_ONLY_ACCOUNT)):
        raise PreflightError("source review DB/account identity differs")
    from meteo_audit.approval_gate import _check_preflight
    report = item.get("snapshot")
    if not isinstance(report, dict):
        raise PreflightError("missing approved before-image report")
    _check_preflight(batch, report)
    return report


def live_status(connection, *, expected_hostname: str = EXPECTED_HOST,
                expected_server_id: int = EXPECTED_SERVER_ID,
                expected_account: str | None = None) -> dict:
    """Read-only status; explicitly allow two PRE-EXISTING accounts only."""
    valid_accounts = (EXISTING_ACCOUNT, READ_ONLY_ACCOUNT)
    if expected_account is not None and expected_account not in valid_accounts:
        raise PreflightError("unexpected SQL account is not an approved existing identity")
    cur = connection.cursor()
    try:
        cur.execute("SELECT DATABASE(),@@hostname,@@server_id,CURRENT_USER(),@@version")
        row = cur.fetchone()
        if (not row or
                (row[0], row[1], int(row[2])) !=
                (TARGET, expected_hostname, expected_server_id)
                or row[3] not in valid_accounts
                or (expected_account is not None and row[3] != expected_account)):
            raise PreflightError("connected DB host, server_id or SQL account is wrong")
        _assert_target(cur)  # also strict read-only DDL/index/FK guard
        ddl = verify_audit_ddl(cur)
        _check_rain(cur)
        cur.execute("SELECT COUNT(*) FROM loucka_reconstruction.issue26_batch_events")
        events = int(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM loucka_reconstruction.issue26_field_events")
        fields = int(cur.fetchone()[0])
        return {
            "status": "ISSUE26_EXISTING_ACCOUNT_READY_NO_DATA_WRITES",
            "sql_host": row[1], "server_id": int(row[2]),
            "account": row[3], "schema": row[0],
            "audit": ddl, "batch_events": events, "field_events": fields,
            "july_2021_mm": "42.567", "db_writes": 0,
            "new_sql_users": 0,
        }
    finally:
        cur.close()


def operation(connection, *, mode: str, manifest_path: str, review_path: str,
              receipt_path: str | None = None, key_path: str | None = None,
              execute: bool = False, prompt=input,
              expected_hostname: str = EXPECTED_HOST,
              expected_server_id: int = EXPECTED_SERVER_ID,
              expected_account: str | None = None,
              now: int | None = None) -> dict:
    """Operator-facing flow: inspect, apply or rollback, with pinned evidence."""
    if mode not in {"inspect", "apply", "rollback"}:
        raise PreflightError("unknown operator action")
    if mode == "inspect" and execute:
        raise PreflightError("inspect is always read-only")
    if mode != "inspect" and not execute:
        raise PreflightError("APPLY/ROLLBACK requires --execute and fresh signed owner receipt")
    # Critical separation: wide privilege web account cannot be used for
    # mutations, even with a valid owner signature and --execute.
    if mode in ("apply", "rollback") and (
        expected_account is not None and expected_account != EXISTING_ACCOUNT
    ):
        raise PreflightError("APPLY/ROLLBACK requires the existing loucka_audit account")
    batch = _manifest(manifest_path)
    approved_report = _review(review_path, batch)
    status = live_status(connection, expected_hostname=expected_hostname,
                         expected_server_id=expected_server_id,
                         expected_account=expected_account)
    if mode in ("apply", "rollback") and status["account"] != EXISTING_ACCOUNT:
        raise PreflightError("mutations require existing loucka_audit; web_ro is read-only")
    base = {
        "batch_id": batch.batch_id,
        "payload_sha256": batch.payload_sha256,
        "before_image_sha256": approved_report["before_image_sha256"],
        "operations": [
            {"time_utc": op.target_time_utc, "variable": op.variable,
             "old": op.expected_old, "proposed": op.proposed_new}
            for op in batch.operations
        ],
        "account": status["account"],
        "schema": status["schema"],
    }
    if mode == "inspect":
        refreshed = sql_preflight(connection, batch)
        verify_fresh_snapshot(batch, approved_report, {
            (x["target_time_utc"], x["variable"]): x["old"]
            for x in refreshed["before_image"]
        })
        return {**base, "status": "INSPECT_READY_FOR_EXPLICIT_APPROVAL_NO_WRITES",
                "db_writes": 0, "owner_approval_granted": False}

    if not receipt_path or not key_path:
        raise PreflightError("signed receipt and private approval key required")
    receipt = _signed_receipt(receipt_path)
    key = _private_file(key_path).read_bytes()
    verify_exact_batch(batch, approved_report, receipt, secret_key=key, now=now)

    # Explicit human confirmation is bound to the full manifest AND before-image.
    phrase = ((APPLY_CONFIRM if mode == "apply" else APPROVE_ROLLBACK)
              + batch.batch_id + ":" + batch.payload_sha256
              + ":" + approved_report["before_image_sha256"])
    if mode == "apply":
        fresh = sql_preflight(connection, batch)
        verify_fresh_snapshot(batch, approved_report, {
            (x["target_time_utc"], x["variable"]): x["old"]
            for x in fresh["before_image"]
        })
    entered = prompt(
        "SOURCE EVIDENCE AND VALUES MUST BE OWNER-REVIEWED. "
        "Exact confirmation (not a shortcut): " + phrase + "\n> "
    )
    if entered != phrase:
        raise PreflightError("owner did not enter exact transaction confirmation")
    if mode == "apply":
        result = apply_approved_batch(
            connection, batch, approved_report, receipt, approval_key=key, now=now
        )
    else:
        result = rollback_approved_batch(
            connection, batch, approved_report, receipt, approval_key=key,
            entered_rollback_challenge=entered, now=now
        )
    return {**base, "status": "COMMITTED_" + result.action,
            "affected_fields": result.affected,
            "committed": result.committed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", nargs="?", default="status",
                        choices=("status","inspect","apply","rollback"))
    parser.add_argument("--client-file", required=True,
                        help="0600 existing-account CNF: loucka_web_ro for reads; loucka_audit for writes")
    parser.add_argument("--manifest")
    parser.add_argument("--review-evidence")
    parser.add_argument("--receipt-file")
    parser.add_argument("--key-file")
    parser.add_argument("--execute", action="store_true",
                        help="required for signed apply or rollback; never available in status")
    args = parser.parse_args()
    try:
        if args.mode in ("status","inspect") and args.execute:
            raise PreflightError("read-only commands cannot be executed as writes")
        if args.mode in ("apply","rollback") and not args.execute:
            raise PreflightError("explicit --execute required")
        if args.mode != "status" and (not args.manifest or not args.review_evidence):
            raise PreflightError("manifest and review-evidence are mandatory")
        config = _private_file(args.client_file)
        import pymysql
        connection = pymysql.connect(
            read_default_file=str(config), read_default_group="client",
            database=TARGET, autocommit=True, connect_timeout=8,
            read_timeout=30, write_timeout=30,
        )
        try:
            if args.mode == "status":
                output = live_status(connection)
            else:
                if args.execute and not sys.stdin.isatty():
                    raise PreflightError("mutations require interactive operator terminal")
                output = operation(
                    connection, mode=args.mode,
                    manifest_path=args.manifest,
                    review_path=args.review_evidence,
                    receipt_path=args.receipt_file, key_path=args.key_file,
                    execute=args.execute,
                )
        finally:
            connection.close()
        print(json.dumps(output, sort_keys=True, ensure_ascii=False))
        return 0
    except (PreflightError, OSError, ValueError, KeyError, TypeError, ImportError,
            EOFError) as error:
        print("ISSUE26_OPERATOR_NO_GO: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
