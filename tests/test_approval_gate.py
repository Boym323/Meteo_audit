"""Tests for explicit owner approval gate; no database connections."""
from dataclasses import replace
import unittest

from meteo_audit.approval_dryrun import (
    CandidateBatch, FieldCorrection, PreflightError, preflight,
    simulate_atomic_apply, simulate_atomic_rollback,
)
from meteo_audit.approval_gate import (
    challenge_for, sign_exact_batch, verify_exact_batch, verify_fresh_snapshot,
)

SECRET = bytes(range(32))


def operation(t=1540000000, variable="outTemp", old=0.0, new=12.5):
    return FieldCorrection(t, variable, old, new, "source:synthetic",
                           "epoch:synthetic", "rule:test-v1", "HIGH", "LOW")


def example():
    b = CandidateBatch("qc-synthetic-only", (operation(),))
    before = {(1540000000, "outTemp"): 0.0}
    return b, before, preflight(b, before)


def approved(b, report):
    return sign_exact_batch(
        b, report, approver="owner:synthetic",
        entered_challenge=challenge_for(b, report),
        secret_key=SECRET, now=1795430000,
    )


class OwnerApprovalGateTests(unittest.TestCase):
    def test_explicit_challenge_is_mandatory(self):
        b, _, report = example()
        with self.assertRaisesRegex(PreflightError, "operator did not approve"):
            sign_exact_batch(
                b, report, approver="owner:synthetic",
                entered_challenge="SCHVALUJI-JINOU-DAVKU",
                secret_key=SECRET, now=1795430000,
            )

    def test_receipt_pins_batch_payload_and_before_image(self):
        b, snapshot, report = example()
        receipt = approved(b, report)
        verified = verify_exact_batch(b, report, receipt, secret_key=SECRET, now=1795430020)
        updated, commit = simulate_atomic_apply(b, snapshot, verified)
        self.assertEqual(updated[(1540000000, "outTemp")], 12.5)
        self.assertEqual(snapshot[(1540000000, "outTemp")], 0.0)
        restored = simulate_atomic_rollback(b, updated, commit, report["before_image"])
        self.assertEqual(restored, snapshot)

    def test_modified_value_requires_new_approval(self):
        b, _, report = example()
        receipt = approved(b, report)
        changed = CandidateBatch(b.batch_id, (operation(new=13.0),))
        with self.assertRaisesRegex(PreflightError, "preflight identity"):
            verify_exact_batch(changed, report, receipt, secret_key=SECRET, now=1795430020)

    def test_tampered_receipt_and_wrong_key_rejected(self):
        b, _, report = example()
        receipt = approved(b, report)
        with self.assertRaisesRegex(PreflightError, "integrity"):
            verify_exact_batch(b, report, replace(receipt, approver="owner:intruder"),
                               secret_key=SECRET, now=1795430020)
        with self.assertRaisesRegex(PreflightError, "integrity"):
            verify_exact_batch(b, report, receipt, secret_key=b"A"*32, now=1795430020)

    def test_expired_and_future_receipts_fail_closed(self):
        b, _, report = example()
        receipt = approved(b, report)
        with self.assertRaisesRegex(PreflightError, "expired"):
            verify_exact_batch(b, report, receipt, secret_key=SECRET, now=1795433600)
        with self.assertRaisesRegex(PreflightError, "future"):
            verify_exact_batch(b, report, receipt, secret_key=SECRET, now=1795429999)

    def test_changed_source_before_image_is_rejected(self):
        b, _, report = example()
        with self.assertRaisesRegex(PreflightError, "before-image old-value"):
            sign_exact_batch(
                b, dict(report, before_image=[{"target_time_utc":1540000000,
                                              "variable":"outTemp", "old":99.0}]),
                approver="owner:synthetic", entered_challenge="anything",
                secret_key=SECRET, now=1795430000,
            )

    def test_unsigned_plain_object_not_accepted(self):
        b, _, report = example()
        with self.assertRaisesRegex(PreflightError, "signed approval"):
            verify_exact_batch(b, report, {"approval_ref":"approved"},
                               secret_key=SECRET, now=1795430020)

    def test_fresh_snapshot_cas_and_history_collision(self):
        b, old, report = example()
        self.assertEqual(verify_fresh_snapshot(b, report, old)["operation_count"], 1)
        with self.assertRaisesRegex(PreflightError, "CAS"):
            verify_fresh_snapshot(b, report, {(1540000000, "outTemp"): 19.0})
        with self.assertRaisesRegex(PreflightError, "history"):
            verify_fresh_snapshot(b, report, old, changed_keys=frozenset({(1540000000,"outTemp")}))

    def test_zero_is_distinct_from_null(self):
        b, snapshot, report = example()
        receipt = approved(b, report)
        verify_exact_batch(b, report, receipt, secret_key=SECRET, now=1795430020)
        with self.assertRaisesRegex(PreflightError, "CAS"):
            verify_fresh_snapshot(b, report, {(1540000000, "outTemp"): None})

    def test_no_db_or_backup_dependency(self):
        b, _, report = example()
        receipt = approved(b, report)
        self.assertEqual(receipt.target, "loucka_reconstruction.archive")
        self.assertEqual(report["db_writes"], 0)
        self.assertNotIn("backup", receipt.payload())
        self.assertNotIn("pbs", receipt.payload())


if __name__ == "__main__":
    unittest.main()
