import unittest
from dataclasses import replace

from meteo_audit.approval_dryrun import (
    BatchApproval, CandidateBatch, FieldCorrection,
    PreflightError, preflight, simulate_atomic_apply, simulate_atomic_rollback,
)


def op(t=1540000000, v="outTemp", old=None, new=12.5):
    return FieldCorrection(t, v, old, new, "source:immutable-sha",
                           "epoch:verified", "rule:1", "HIGH", "LOW")


def batch(*operations):
    return CandidateBatch("batch:synthetic", tuple(operations))


def approval(b):
    return BatchApproval(b.batch_id, b.payload_sha256, "owner:synthetic-test")


class ApprovalDryRunTests(unittest.TestCase):
    def test_dry_run_does_not_modify_snapshot(self):
        b = batch(op())
        snapshot = {b.operations[0].key: None}
        original = dict(snapshot)
        report = preflight(b, snapshot)
        self.assertEqual(report["operation_count"], 1)
        self.assertEqual(report["db_writes"], 0)
        self.assertEqual(snapshot, original)
        self.assertEqual(report["before_image"][0]["old"], None)

    def test_null_and_numeric_zero_do_not_compare_equal(self):
        b = batch(op(old=None, new=0))
        with self.assertRaisesRegex(PreflightError, "CAS"):
            preflight(b, {b.operations[0].key: 0})
        self.assertEqual(preflight(b, {b.operations[0].key: None})["operation_count"], 1)

    def test_reject_missing_target(self):
        with self.assertRaisesRegex(PreflightError, "absent"):
            preflight(batch(op()), {})

    def test_old_value_changed_fails_closed(self):
        with self.assertRaisesRegex(PreflightError, "CAS"):
            preflight(batch(op(old=2, new=3)), {(1540000000, "outTemp"): 4})

    def test_collision_with_applied_history_fails(self):
        b = batch(op())
        with self.assertRaisesRegex(PreflightError, "history"):
            preflight(b, {b.operations[0].key: None}, changed_keys=frozenset({b.operations[0].key}))

    def test_duplicate_key_rejected_before_any_action(self):
        with self.assertRaisesRegex(PreflightError, "duplicate"):
            batch(op(), op(new=9))

    def test_approval_must_match_exact_payload(self):
        b = batch(op())
        altered = batch(op(new=14))
        with self.assertRaisesRegex(PreflightError, "approval"):
            simulate_atomic_apply(altered, {(1540000000, "outTemp"): None}, approval(b))

    def test_apply_then_reapply_is_rejected_and_atomic(self):
        b = batch(op())
        original = {(1540000000, "outTemp"): None}
        updated, commit = simulate_atomic_apply(b, original, approval(b))
        self.assertIsNone(original[b.operations[0].key])
        self.assertEqual(updated[b.operations[0].key], 12.5)
        with self.assertRaisesRegex(PreflightError, "CAS"):
            simulate_atomic_apply(b, updated, approval(b))
        self.assertEqual(commit.batch_id, b.batch_id)

    def test_competing_batch_old_value_conflict(self):
        a = batch(op(old=1, new=2))
        newer, _ = simulate_atomic_apply(a, {(1540000000, "outTemp"): 1}, approval(a))
        rival = batch(op(old=1, new=3))
        with self.assertRaisesRegex(PreflightError, "CAS"):
            simulate_atomic_apply(rival, newer, approval(rival))

    def test_exact_rollback_restores_before_image(self):
        b = batch(op(old=None, new=10))
        original = {(1540000000, "outTemp"): None}
        before = preflight(b, original)["before_image"]
        updated, evidence = simulate_atomic_apply(b, original, approval(b))
        restored = simulate_atomic_rollback(b, updated, evidence, before)
        self.assertEqual(restored, original)
        self.assertEqual(updated[b.operations[0].key], 10)

    def test_rollback_rejects_concurrent_change(self):
        b = batch(op(old=1, new=10))
        original = {(1540000000, "outTemp"): 1}
        before = preflight(b, original)["before_image"]
        updated, evidence = simulate_atomic_apply(b, original, approval(b))
        updated[b.operations[0].key] = 3
        with self.assertRaisesRegex(PreflightError, "CAS"):
            simulate_atomic_rollback(b, updated, evidence, before)

    def test_rollback_rejects_tampered_before_image(self):
        b = batch(op(old=1, new=10))
        before = preflight(b, {(1540000000, "outTemp"): 1})["before_image"]
        updated, evidence = simulate_atomic_apply(b, {(1540000000, "outTemp"): 1}, approval(b))
        with self.assertRaisesRegex(PreflightError, "identity"):
            simulate_atomic_rollback(b, updated, evidence, [dict(before[0], old=2)])

    def test_q1_2018_is_protected(self):
        with self.assertRaisesRegex(PreflightError, "protected"):
            op(t=1517000000)

    def test_2021_rain_and_rainrate_are_protected(self):
        for variable in ("rain", "rainRate"):
            with self.subTest(variable=variable), self.assertRaisesRegex(PreflightError, "protected"):
                op(t=1626300000, v=variable, old=0, new=1)

    def test_unauthorized_metadata_and_nonfinite_rejected(self):
        for value in (True, float("inf"), float("nan"), "1"):
            with self.subTest(value=value), self.assertRaises(PreflightError):
                op(new=value)
        with self.assertRaises(PreflightError):
            op(v="dateTime")

    def test_no_op_cannot_be_approved(self):
        with self.assertRaisesRegex(PreflightError, "no-op"):
            op(old=0, new=0)

    def test_multiple_operations_apply_atomically_in_copy_only(self):
        a, b = op(t=1540000000, old=1, new=2), op(t=1540000300, v="outHumidity", old=0, new=54)
        manifest = batch(a, b)
        snapshot = {a.key: 1, b.key: 0}
        result, receipt = simulate_atomic_apply(manifest, snapshot, approval(manifest))
        self.assertEqual(result[a.key], 2)
        self.assertEqual(result[b.key], 54)
        self.assertEqual(snapshot[a.key], 1)
        self.assertEqual(len(receipt.affected_keys), 2)


if __name__ == "__main__":
    unittest.main()
