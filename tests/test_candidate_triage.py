import unittest

from meteo_audit.candidate_triage import (
    PendingCandidateState, UnsafePendingCandidate, disposition, summary,
)


def candidate(**changes):
    base = dict(variable="rain", target_time_utc=1663246500,
                proposed_value=0.335279992, target_exists=False,
                current_value=None, matching_applied_change_count=0)
    base.update(changes)
    return PendingCandidateState(**base)


class PendingCandidateTriageTests(unittest.TestCase):
    def test_review_only_264_without_numeric_replacement(self):
        states = [candidate(proposed_value=None) for _ in range(264)]
        self.assertEqual(summary(states), {"REVIEW_FLAG_NO_NUMERIC_PROPOSAL": 264})

    def test_2022_missing_rain_slot_not_automatically_inserted(self):
        self.assertEqual(disposition(candidate()),
                         "HOLD_MISSING_TARGET_UNVERIFIED")
        self.assertEqual(disposition(candidate(physical_source_conflict=True)),
                         "HOLD_SOURCE_CONFLICT")

    def test_seven_applied_proposals_not_replayed(self):
        states = [candidate(target_exists=True,current_value=0,
                            proposed_value=0,matching_applied_change_count=1)
                  for _ in range(7)]
        self.assertEqual(summary(states), {"ALREADY_APPLIED_NO_REPEAT": 7})

    def test_numeric_zero_distinguished_from_missing(self):
        self.assertEqual(disposition(candidate(
            target_exists=True,current_value=None,proposed_value=0,
            matching_applied_change_count=0)),
            "HOLD_SOURCE_NOT_INDEPENDENTLY_VERIFIED")

    def test_applied_value_mismatch_is_not_silently_approved(self):
        self.assertEqual(disposition(candidate(target_exists=True,
            current_value=1, matching_applied_change_count=1)),
            "HOLD_EXISTING_AUDIT_CONFLICT")

    def test_mutating_candidate_needs_proof_backup_and_approval(self):
        base = dict(target_exists=True,current_value=0,
                    matching_applied_change_count=0)
        self.assertEqual(disposition(candidate(**base)),
                         "HOLD_SOURCE_NOT_INDEPENDENTLY_VERIFIED")
        self.assertEqual(disposition(candidate(**base,
                         independent_source_validated=True)),
                         "HOLD_BACKUP_RESTORE_NOT_VERIFIED")
        self.assertEqual(disposition(candidate(**base,
                         independent_source_validated=True,
                         backup_restore_verified=True)),
                         "HOLD_BATCH_NOT_EXPLICITLY_APPROVED")
        self.assertEqual(disposition(candidate(**base,
                         independent_source_validated=True,
                         backup_restore_verified=True,
                         explicit_batch_approval=True)),
                         "REVIEW_READY_FOR_SEPARATE_TRANSACTIONAL_PREFLIGHT")

    def test_provenance_conflict_has_priority_before_approval(self):
        self.assertEqual(disposition(candidate(
            target_exists=True,current_value=0,
            independent_source_validated=True,
            backup_restore_verified=True,
            explicit_batch_approval=True,
            physical_source_conflict=True)), "HOLD_SOURCE_CONFLICT")

    def test_malformed_values_and_metadata_are_rejected(self):
        for changes in (
            {"target_time_utc": True}, {"target_time_utc": -1},
            {"proposed_value": float("nan")},
            {"current_value": float("inf")}, {"proposed_value": "0"},
            {"matching_applied_change_count": -1},
            {"explicit_batch_approval": 1},
            {"target_exists": False, "current_value": 0},
        ):
            with self.subTest(changes=changes), self.assertRaises(UnsafePendingCandidate):
                candidate(**changes)

    def test_all_pending_proposals_are_review_or_no_repeat_not_apply(self):
        statuses = summary(
            [candidate(proposed_value=None) for _ in range(264)] +
            [candidate(target_exists=True,current_value=0,
                       proposed_value=0,matching_applied_change_count=1) for _ in range(7)] +
            [candidate(physical_source_conflict=True)]
        )
        self.assertEqual(sum(statuses.values()), 272)
        self.assertEqual(statuses["REVIEW_FLAG_NO_NUMERIC_PROPOSAL"], 264)
        self.assertEqual(statuses["ALREADY_APPLIED_NO_REPEAT"], 7)
        self.assertEqual(statuses["HOLD_SOURCE_CONFLICT"], 1)
        self.assertFalse(any(key in ("APPLY", "APPROVED", "EXECUTE") for key in statuses))


if __name__ == "__main__":
    unittest.main()
