#!/usr/bin/env python3
"""Issue #26: local offline approval receipt, no database access or writes.

This CLI cannot approve the content of a DB snapshot itself, and cannot apply
any meteorological change. The future SQL writer must independently re-read
locked target rows and verify origin evidence before applying.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import stat
import sys

from meteo_audit.approval_dryrun import CandidateBatch, FieldCorrection, PreflightError, preflight
from meteo_audit.approval_gate import challenge_for, sign_exact_batch, verify_exact_batch, SignedApproval


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_review(manifest_path, snapshot_path):
    raw = read_json(manifest_path)
    if set(raw) != {"schema", "target", "batch_id", "operations"}:
        raise PreflightError("unexpected manifest fields")
    if not isinstance(raw["operations"], list):
        raise PreflightError("operations must be a list")
    ops = tuple(FieldCorrection(**x) for x in raw["operations"])
    batch = CandidateBatch(raw["batch_id"], ops, raw["schema"], raw["target"])
    original = read_json(snapshot_path)
    if not isinstance(original, list):
        raise PreflightError("before-image must be a list of target-value rows")
    snapshot = {}
    for item in original:
        if not isinstance(item, dict) or set(item) != {"target_time_utc", "variable", "old"}:
            raise PreflightError("unexpected before-image row format")
        key = (item["target_time_utc"], item["variable"])
        if key in snapshot:
            raise PreflightError("duplicate before-image key")
        snapshot[key] = item["old"]
    if len(snapshot) != len(ops):
        raise PreflightError("before-image and proposal must be exactly aligned")
    report = preflight(batch, snapshot)
    return batch, report


def private_key(path_name):
    path = Path(path_name)
    if not path.is_absolute() or path.is_symlink():
        raise PreflightError("private approval key must be absolute and non-symlink")
    meta = path.stat()
    if (not stat.S_ISREG(meta.st_mode) or meta.st_uid != os.geteuid()
            or meta.st_mode & 0o077):
        raise PreflightError("private approval key must be owned by operator and mode 0600")
    value = path.read_bytes()
    if len(value) < 32:
        raise PreflightError("private approval key must contain at least 32 bytes")
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("challenge", "sign", "verify"))
    p.add_argument("--manifest", required=True, help="immutable proposed batch JSON")
    p.add_argument("--before-image", required=True, help="read-only review snapshot JSON")
    p.add_argument("--key-file", help="private binary HMAC key; required for sign/verify")
    p.add_argument("--operator", help="operator identity for sign")
    p.add_argument("--receipt-file", help="new receipt file for sign, existing for verify")
    args = p.parse_args()
    try:
        batch, report = read_review(args.manifest, args.before_image)
        if args.action == "challenge":
            print(json.dumps({
                "status": "REVIEW_ONLY_NO_DB_WRITES",
                "batch_id": batch.batch_id,
                "payload_sha256": batch.payload_sha256,
                "before_image_sha256": report["before_image_sha256"],
                "exact_phrase": challenge_for(batch, report),
            }, sort_keys=True))
            return 0
        if not args.key_file or not args.receipt_file:
            raise PreflightError("sign and verify require private key and receipt file")
        secret = private_key(args.key_file)
        if args.action == "sign":
            if not args.operator:
                raise PreflightError("operator identity missing")
            # stdin, never CLI arguments (to avoid leaking the phrase via ps/history).
            entered = input("Enter the exact challenge printed by 'challenge': ")
            receipt = sign_exact_batch(
                batch, report, approver=args.operator,
                entered_challenge=entered, secret_key=secret,
            )
            with Path(args.receipt_file).open("x", encoding="utf-8") as output:
                os.fchmod(output.fileno(), 0o600)
                json.dump(asdict(receipt), output, sort_keys=True, indent=2)
                output.write("\n")
            print("APPROVAL_RECEIPT_SAVED_NOT_APPLIED")
            return 0
        receipt = SignedApproval(**read_json(args.receipt_file))
        verify_exact_batch(batch, report, receipt, secret_key=secret)
        print("VALID_SIGNED_APPROVAL_NOT_APPLIED")
        return 0
    except (PreflightError, ValueError, TypeError, KeyError, OSError, EOFError) as e:
        print("ISSUE26_APPROVAL_NO_GO: " + str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
