"""Regression tests for a fail-closed read-only audit and collision guard."""
import unittest

from meteo_audit.db import _validate_select
from meteo_audit.reconstruction_guard import (
    APPLIED, BACKUPS, CANCELLED, GuardError, inspect_baseline, inspect_proposal,
)


class FakeDatabase:
    def __init__(self):
        self.queries = []
        self.audit_rows = [
            f"{batch}\t{variable}\tapplied\t{count}\t{mm if mm is not None else 0}"
            for (batch, variable), (count, mm) in sorted(APPLIED.items())
        ]
        self.canceled_rows = [
            f"{batch}\tcancelled\t{count}\t{digest}"
            for batch, (count, digest) in sorted(CANCELLED.items())
        ]
        self.backups = {name: [f"{n}\t{n}\t{mm}"]
                        for name, (n, mm) in BACKUPS.items()}
        self.archive_count = "1679802\t42.5673"
        self.prior_changes = []
        self.prior_candidates = []
        self.batch_exists = []
        self.batch_changes_exist = []
        self.current_rows = ["1301295000\t0\t0", "1740687300\t0\t0"]

    def __call__(self, sql):
        _validate_select(sql)
        self.queries.append(sql)
        if "FROM reconstruction_changes WHERE batch_key IN" in sql:
            return self.audit_rows
        if "FROM reconstruction_batches WHERE batch_id IN" in sql:
            return self.canceled_rows
        if "FROM archive a JOIN " in sql:
            return self.backups[next(key for key in self.backups if key in sql)]
        if "SUM(CASE WHEN dateTime>" in sql:
            return [self.archive_count]
        if "FROM reconstruction_batches WHERE batch_id=" in sql:
            return self.batch_exists
        if "FROM reconstruction_changes WHERE batch_key=" in sql:
            return self.batch_changes_exist
        if "FROM reconstruction_changes WHERE target_time IN" in sql:
            return self.prior_changes
        if "FROM reconstruction_candidates c" in sql:
            return self.prior_candidates
        if "SELECT dateTime,rain,rainRate FROM archive" in sql:
            return self.current_rows
        raise AssertionError("Unexpected SQL read: " + sql)


def proposal():
    return {
        "batch_id": "example-reconstruction-review-v1",
        "candidates": [{
            "target_time": 1301295000,
            "variable": "rain",
            "expected_old_value": 0,
            "proposed_value": 0.01,
            "source_database": "pocasi-loucka.eu_GW1000",
            "source_time": 1301295000,
            "reason": "Review demonstrated historical counter reset",
            "diagnosis_confidence": "HIGH",
            "replacement_confidence": "UNRESOLVED",
        }]
    }


class BaselineTests(unittest.TestCase):
    def test_verified_baseline_finds_historical_applied_and_canceled(self):
        db = FakeDatabase()
        result = inspect_baseline(db)
        self.assertTrue(result["verified"])
        self.assertEqual(len(result["applied"]), 5)
        self.assertEqual(len(result["cancelled"]), 2)
        self.assertAlmostEqual(result["july_2021_mm"], 42.5673)
        self.assertEqual(result["archive_count"], 1679802)
        self.assertEqual(len(result["backups"]), 3)
        self.assertTrue(db.queries)
        self.assertTrue(all(sql.startswith("SELECT ") for sql in db.queries))
        self.assertFalse(any("UPDATE " in sql or "INSERT " in sql for sql in db.queries))

    def test_fail_closed_when_baseline_audit_was_changed(self):
        db = FakeDatabase()
        db.audit_rows[0] = db.audit_rows[0].replace("\tapplied\t", "\tprepared\t")
        result = inspect_baseline(db)
        self.assertFalse(result["verified"])
        self.assertTrue(result["errors"])

    def test_fail_closed_when_backup_damaged(self):
        db = FakeDatabase()
        db.backups["rain_phase_a_201006_backup_20261030_v1"] = ["30\t29\t161.76"]
        self.assertFalse(inspect_baseline(db)["verified"])

    def test_fail_closed_when_july_regressed(self):
        db = FakeDatabase()
        db.archive_count = "1679802\t0"
        result = inspect_baseline(db)
        self.assertIn("July 2021 rainfall invariant changed", result["errors"])

    def test_row_count_growth_is_not_an_error(self):
        db = FakeDatabase()
        db.archive_count = "1680100\t42.5673"
        self.assertTrue(inspect_baseline(db)["verified"])


class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDatabase()
        self.baseline = inspect_baseline(self.db)
        self.db.queries.clear()

    def test_valid_preflight_never_authorizes_apply(self):
        result = inspect_proposal(proposal(), self.db, self.baseline)
        self.assertTrue(result["preflight_clean"])
        self.assertFalse(result["authorized_to_apply"])
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(len(result["proposal_sha256"]), 64)
        self.assertTrue(all(sql.startswith("SELECT") for sql in self.db.queries))

    def test_canceled_phase_a_batch_may_not_be_reused(self):
        doc = proposal()
        doc["batch_id"] = next(iter(CANCELLED))
        with self.assertRaisesRegex(GuardError, "Historical batch ID"):
            inspect_proposal(doc, self.db, self.baseline)

    def test_applied_phase_a_batch_may_not_be_reused(self):
        doc = proposal()
        doc["batch_id"] = "rain-phaseA-june2010-corrected-20261030-v1"
        with self.assertRaisesRegex(GuardError, "Historical batch ID"):
            inspect_proposal(doc, self.db, self.baseline)

    def test_any_applied_target_blocks_even_different_batch_key(self):
        self.db.prior_changes = ["1301295000\train\train-phaseA-apply-20261030-v1\tapplied"]
        with self.assertRaisesRegex(GuardError, "overlaps"):
            inspect_proposal(proposal(), self.db, self.baseline)

    def test_prepared_target_also_blocks(self):
        self.db.prior_changes = ["1301295000\train\tother-batch\tprepared"]
        with self.assertRaisesRegex(GuardError, "overlaps"):
            inspect_proposal(proposal(), self.db, self.baseline)

    def test_preexisting_cancelled_candidate_blocks_reuse_by_new_batch(self):
        self.db.prior_candidates = [
            "1301295000\\train\\tloucka-rain-phaseA-confirmed-20261030-v1\\tcancelled"
        ]
        with self.assertRaisesRegex(GuardError, "historical candidate proposals"):
            inspect_proposal(proposal(), self.db, self.baseline)

    def test_preexisting_pending_candidate_blocks(self):
        self.db.prior_candidates = [
            "1301295000\\train\\tfuture-pending-review\\tpending"
        ]
        with self.assertRaisesRegex(GuardError, "historical candidate proposals"):
            inspect_proposal(proposal(), self.db, self.baseline)

    def test_malformed_json_variable_and_source_fail_closed(self):
        for field, invalid in (("variable", []), ("source_database", {})):
            with self.subTest(field=field):
                doc = proposal()
                doc["candidates"][0][field] = invalid
                with self.assertRaises(GuardError):
                    inspect_proposal(doc, self.db, self.baseline)

    def test_bad_source_time_rejected(self):
        doc = proposal()
        doc["candidates"][0]["source_time"] = -1
        with self.assertRaisesRegex(GuardError, "source_time"):
            inspect_proposal(doc, self.db, self.baseline)

    def test_unrelated_variable_does_not_conflict(self):
        self.db.prior_changes = ["1301295000\twindSpeed\tother-batch\tapplied"]
        self.assertTrue(inspect_proposal(proposal(), self.db, self.baseline)["preflight_clean"])

    def test_reused_batch_id_in_database_blocks(self):
        self.db.batch_exists = ["example-reconstruction-review-v1\tcancelled"]
        with self.assertRaisesRegex(GuardError, "already exists"):
            inspect_proposal(proposal(), self.db, self.baseline)

    def test_reused_change_batch_id_blocks(self):
        self.db.batch_changes_exist = ["example-reconstruction-review-v1\tapplied"]
        with self.assertRaisesRegex(GuardError, "already exists"):
            inspect_proposal(proposal(), self.db, self.baseline)

    def test_stale_expected_old_value_blocks(self):
        doc = proposal()
        doc["candidates"][0]["expected_old_value"] = 1
        with self.assertRaisesRegex(GuardError, "does not match"):
            inspect_proposal(doc, self.db, self.baseline)

    def test_missing_target_blocks(self):
        self.db.current_rows = []
        with self.assertRaisesRegex(GuardError, "absent"):
            inspect_proposal(proposal(), self.db, self.baseline)

    def test_null_is_not_zero(self):
        self.db.current_rows = ["1301295000\tNULL\t0"]
        with self.assertRaisesRegex(GuardError, "does not match"):
            inspect_proposal(proposal(), self.db, self.baseline)
        doc = proposal()
        doc["candidates"][0]["expected_old_value"] = None
        self.assertTrue(inspect_proposal(doc, self.db, self.baseline)["preflight_clean"])

    def test_duplicate_pair_in_manifest_blocks(self):
        doc = proposal()
        doc["candidates"].append(dict(doc["candidates"][0]))
        with self.assertRaisesRegex(GuardError, "Duplicate"):
            inspect_proposal(doc, self.db, self.baseline)

    def test_noop_blocks(self):
        doc = proposal()
        doc["candidates"][0]["proposed_value"] = 0
        with self.assertRaisesRegex(GuardError, "No-op"):
            inspect_proposal(doc, self.db, self.baseline)

    def test_missing_provenance_blocks(self):
        doc = proposal()
        doc["candidates"][0]["source_database"] = "evil_db"
        with self.assertRaisesRegex(GuardError, "allowlisted"):
            inspect_proposal(doc, self.db, self.baseline)

    def test_unknown_variable_is_not_silently_read(self):
        doc = proposal()
        doc["candidates"][0]["variable"] = "dewpoint"
        with self.assertRaisesRegex(GuardError, "Only rain"):
            inspect_proposal(doc, self.db, self.baseline)

    def test_bad_batch_id_is_not_interpolated_into_sql(self):
        doc = proposal()
        doc["batch_id"] = "batch'; DROP TABLE archive"
        with self.assertRaisesRegex(GuardError, "Invalid batch_id"):
            inspect_proposal(doc, self.db, self.baseline)

    def test_baseline_failure_blocks_preflight(self):
        with self.assertRaisesRegex(GuardError, "Baseline failed"):
            inspect_proposal(proposal(), self.db, {"verified": False})

    def test_no_value_forgery_from_read_only_preflight(self):
        doc = proposal()
        doc["candidates"][0]["replacement_confidence"] = "UNRESOLVED"
        self.assertFalse(inspect_proposal(doc, self.db, self.baseline)["authorized_to_apply"])


if __name__ == "__main__":
    unittest.main()
