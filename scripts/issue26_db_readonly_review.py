#!/usr/bin/env python3
"""Issue #26: export exact read-only review from the existing MariaDB.

No SQL writer or DDL entrypoints. A privileged connection is unnecessary:
use a dedicated SELECT-only database user. No backup or PBS checks.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import stat
import sys

from meteo_audit.approval_dryrun import CandidateBatch, FieldCorrection, PreflightError
from meteo_audit.issue26_readonly_export import export_current_review
from meteo_audit.issue26_transaction import TARGET


def read_manifest(path: str) -> CandidateBatch:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {
        "schema", "target", "batch_id", "operations",
    } or not isinstance(raw["operations"], list):
        raise PreflightError("manifest must have exact approved schema and operations")
    operations = tuple(FieldCorrection(**entry) for entry in raw["operations"])
    return CandidateBatch(raw["batch_id"], operations, raw["schema"], raw["target"])


def private_mysql_config(name: str) -> Path:
    p = Path(name)
    if not p.is_absolute() or p.is_symlink():
        raise PreflightError("database client file must be absolute and not a symlink")
    info = p.stat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
            or info.st_mode & 0o077 or not info.st_mode & stat.S_IRUSR):
        raise PreflightError("database client file must be owned by operator and mode 0600")
    return p


def _write_new_json(path: Path, data: object) -> None:
    with path.open("x", encoding="utf-8") as file:
        os.fchmod(file.fileno(), 0o600)
        json.dump(data, file, sort_keys=True, indent=2,
                  allow_nan=False, ensure_ascii=False)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())


def perform_review(*, manifest: str, client_file: str,
                   expected_hostname: str, expected_server_id: int,
                   output_dir: str) -> dict:
    # Validate all CLI arguments BEFORE connecting or creating output files.
    batch = read_manifest(manifest)
    config = private_mysql_config(client_file)
    out = Path(output_dir)
    if not out.is_absolute() or out.is_symlink() or out.exists():
        raise PreflightError("output directory must be new, absolute and non-symlink")
    import pymysql  # optional operator-only dependency, never loaded on import

    conn = pymysql.connect(
        read_default_file=str(config),
        read_default_group="client",
        database=TARGET,
        autocommit=True,
        connect_timeout=8,
        read_timeout=30,
        write_timeout=30,
    )
    try:
        review = export_current_review(
            conn, batch, expected_hostname=expected_hostname,
            expected_server_id=expected_server_id,
        )
    finally:
        conn.close()

    out.mkdir(mode=0o700)
    os.chmod(out, 0o700)
    _write_new_json(out / "before-image.json", review["snapshot"]["before_image"])
    _write_new_json(out / "review-evidence.json", review)
    # Receipt last: reviewers must refuse directories lacking this exact file.
    receipt = {
        "status": "COMPLETE_READ_ONLY_REVIEW_NOT_APPROVED",
        "batch_id": batch.batch_id,
        "payload_sha256": review["snapshot"]["payload_sha256"],
        "before_image_sha256": review["snapshot"]["before_image_sha256"],
        "archive_rows": review["archive_rows"],
        "legacy_change_events": review["legacy_change_events"],
        "audit_schema": review["audit_schema"],
        "sql_identity": review["identity"],
        "db_writes": 0,
        "source_evidence_verified": False,
        "owner_approval_granted": False,
    }
    _write_new_json(out / "review-complete.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--client-file", required=True)
    parser.add_argument("--expect-host", required=True)
    parser.add_argument("--expect-server-id", type=int, required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        result = perform_review(
            manifest=args.manifest,
            client_file=args.client_file,
            expected_hostname=args.expect_host,
            expected_server_id=args.expect_server_id,
            output_dir=args.output_dir,
        )
    except (PreflightError, TypeError, ValueError, KeyError, OSError, ImportError) as error:
        print("ISSUE26_READONLY_REVIEW_NO_GO: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
