"""Offline exact-payload owner approval receipt for reconstruction issue #26.

No database access and no execution. This module deliberately does not enable a
SQL writer. A verified receipt is authorization evidence for the exact reviewed
manifest *only*; a future writer must recheck locked SQL rows via NULL-safe CAS.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import hmac
import json
import re
import secrets
import time
from typing import Mapping

from .approval_dryrun import (
    BatchApproval, CandidateBatch, PreflightError, _digest, preflight,
)

SCHEMA = "loucka-owner-approval-v1"
TARGET = "loucka_reconstruction.archive"
MAX_AGE_SECONDS = 3600
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ACTOR_RE = re.compile(r"^[A-Za-z0-9_.:@/-]{3,120}$")


def _canonical(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _validate_key(key: bytes) -> None:
    if not isinstance(key, bytes) or len(key) < 32:
        raise PreflightError("approval MAC key must contain at least 32 private bytes")


def _check_preflight(batch: CandidateBatch, report: Mapping) -> None:
    if (report.get("status") != "READY_FOR_EXPLICIT_APPROVAL_NOT_APPLIED"
            or report.get("db_writes") != 0
            or report.get("target") != TARGET
            or report.get("batch_id") != batch.batch_id
            or report.get("payload_sha256") != batch.payload_sha256
            or report.get("operation_count") != len(batch.operations)):
        raise PreflightError("approval preflight identity or dry-run contract differs")
    before = report.get("before_image")
    if not isinstance(before, list) or len(before) != len(batch.operations):
        raise PreflightError("approval before-image count differs")
    for row, op in zip(before, batch.operations):
        if not isinstance(row, dict) or (row.get("target_time_utc"), row.get("variable")) != op.key:
            raise PreflightError("approval before-image target mismatch")
        if row.get("old") != op.expected_old or type(row.get("old")) is bool:
            raise PreflightError("approval before-image old-value mismatch")
    if (not isinstance(report.get("before_image_sha256"), str)
            or report["before_image_sha256"] != _digest(before)):
        raise PreflightError("approval before-image hash mismatch")


def challenge_for(batch: CandidateBatch, report: Mapping) -> str:
    """Exact, printable challenge operator must consciously enter."""
    _check_preflight(batch, report)
    return "SCHVALUJI-OPRAVU:" + batch.batch_id + ":" + batch.payload_sha256 + ":" + report["before_image_sha256"]


@dataclass(frozen=True)
class SignedApproval:
    schema: str
    target: str
    batch_id: str
    payload_sha256: str
    before_image_sha256: str
    operation_count: int
    approver: str
    issued_at: int
    expires_at: int
    nonce: str
    mac_sha256: str

    def payload(self) -> dict:
        result = asdict(self)
        result.pop("mac_sha256")
        return result


def sign_exact_batch(
    batch: CandidateBatch, report: Mapping, *,
    approver: str, entered_challenge: str, secret_key: bytes,
    now: int | None = None,
) -> SignedApproval:
    """Create an operator-attested receipt, never automatic via PR/CI."""
    _validate_key(secret_key)
    challenge = challenge_for(batch, report)
    if (not isinstance(entered_challenge, str)
            or not hmac.compare_digest(entered_challenge, challenge)):
        raise PreflightError("operator did not approve exact batch, payload and before-image")
    if not isinstance(approver, str) or not ACTOR_RE.fullmatch(approver):
        raise PreflightError("invalid operator identity reference")
    epoch = int(time.time()) if now is None else now
    if type(epoch) is not int or epoch <= 0:
        raise PreflightError("invalid approval timestamp")
    data = dict(
        schema=SCHEMA, target=TARGET, batch_id=batch.batch_id,
        payload_sha256=batch.payload_sha256,
        before_image_sha256=report["before_image_sha256"],
        operation_count=len(batch.operations),
        approver=approver, issued_at=epoch,
        expires_at=epoch + MAX_AGE_SECONDS,
        nonce=secrets.token_hex(16),
    )
    mac = hmac.new(secret_key, _canonical(data), sha256).hexdigest()
    return SignedApproval(**data, mac_sha256=mac)


def verify_exact_batch(
    batch: CandidateBatch, report: Mapping, receipt: SignedApproval,
    *, secret_key: bytes, now: int | None = None,
) -> BatchApproval:
    """Validate receipt and return a *simulation* approval for a pinned plan.

    Does not grant DB access. Caller must fresh-read source and the target,
    enforce per-target row locks, append-only audit, and post-image CAS.
    """
    _validate_key(secret_key)
    _check_preflight(batch, report)
    if not isinstance(receipt, SignedApproval):
        raise PreflightError("not a signed approval receipt")
    r = receipt.payload()
    if (r["schema"] != SCHEMA or r["target"] != TARGET
            or r["batch_id"] != batch.batch_id
            or r["payload_sha256"] != batch.payload_sha256
            or r["before_image_sha256"] != report["before_image_sha256"]
            or r["operation_count"] != len(batch.operations)
            or not isinstance(r["approver"], str)
            or not ACTOR_RE.fullmatch(r["approver"])
            or type(r["issued_at"]) is not int
            or type(r["expires_at"]) is not int
            or r["expires_at"] - r["issued_at"] != MAX_AGE_SECONDS
            or not isinstance(r["nonce"], str)
            or not re.fullmatch(r"[0-9a-f]{32}", r["nonce"])):
        raise PreflightError("receipt fields do not match the pinned batch")
    if not SHA256_RE.fullmatch(receipt.mac_sha256):
        raise PreflightError("invalid approval MAC encoding")
    valid_mac = hmac.new(secret_key, _canonical(r), sha256).hexdigest()
    if not hmac.compare_digest(valid_mac, receipt.mac_sha256):
        raise PreflightError("approval integrity or private key mismatch")
    epoch = int(time.time()) if now is None else now
    if type(epoch) is not int or epoch < r["issued_at"] or epoch >= r["expires_at"]:
        raise PreflightError("approval receipt expired or issued in future")
    return BatchApproval(batch.batch_id, batch.payload_sha256,
                         "owner-signed:" + receipt.mac_sha256)


def verify_fresh_snapshot(
    batch: CandidateBatch, approved_report: Mapping, fresh_snapshot: Mapping,
    *, changed_keys: frozenset[tuple[int, str]] = frozenset(),
) -> dict:
    """Revalidate candidate after approval. No writes; do not trust old snapshot."""
    refreshed = preflight(batch, fresh_snapshot, changed_keys=changed_keys)
    _check_preflight(batch, refreshed)
    if refreshed["before_image_sha256"] != approved_report["before_image_sha256"]:
        raise PreflightError("target changed after approval; new review required")
    return refreshed
