"""Offline tests for the frozen sync guard; no production payload or DB required."""
import unittest

from meteo_audit.archive_sync import ARCHIVE_FIELDS, SyncError
from meteo_audit.archive_sync_frozen import (
    LOWER_EXCLUSIVE,
    UPPER_EXCLUSIVE,
    compare_source_rows,
    frozen_plan,
)


def row(timestamp: int) -> dict:
    result = {name: None for name in ARCHIVE_FIELDS}
    result.update({"dateTime": timestamp, "usUnits": 16, "interval": 5, "outTemp": 12.5})
    return result


class FrozenSyncGuardTests(unittest.TestCase):
    def setUp(self):
        self.rows = [row(LOWER_EXCLUSIVE + 300), row(LOWER_EXCLUSIVE + 600)]

    def test_plan_selects_only_exact_approved_payload_timestamps(self):
        plan = frozen_plan(
            self.rows,
            [],
            watermark=LOWER_EXCLUSIVE,
            timestamps={self.rows[1]["dateTime"]},
        )
        self.assertEqual([action.timestamp for action in plan.actions], [self.rows[1]["dateTime"]])
        self.assertEqual(plan.window_start, LOWER_EXCLUSIVE)
        self.assertEqual(plan.window_end_exclusive, UPPER_EXCLUSIVE)

    def test_plan_rejects_timestamp_not_in_payload(self):
        with self.assertRaisesRegex(SyncError, "not all present"):
            frozen_plan(
                self.rows,
                [],
                watermark=LOWER_EXCLUSIVE,
                timestamps={LOWER_EXCLUSIVE + 900},
            )

    def test_identical_target_row_is_idempotent_but_different_row_conflicts(self):
        identical = frozen_plan(self.rows, [dict(self.rows[0])], watermark=LOWER_EXCLUSIVE)
        self.assertEqual([a.timestamp for a in identical.actions], [self.rows[1]["dateTime"]])
        changed = dict(self.rows[0], outTemp=13.0)
        with self.assertRaisesRegex(SyncError, "target conflict"):
            frozen_plan(self.rows, [changed], watermark=LOWER_EXCLUSIVE)

    def test_source_comparison_requires_complete_unique_timestamp_set(self):
        compare_source_rows(self.rows, [dict(r) for r in self.rows])
        with self.assertRaisesRegex(SyncError, "timestamp set"):
            compare_source_rows(self.rows, [dict(self.rows[0])])
        changed = [dict(r) for r in self.rows]
        changed[1]["outTemp"] = 12.6
        with self.assertRaisesRegex(SyncError, r"\.outTemp"):
            compare_source_rows(self.rows, changed)

    def test_source_comparison_rejects_incomplete_80_column_row(self):
        incomplete = [dict(r) for r in self.rows]
        incomplete[0].pop("pressure")
        with self.assertRaisesRegex(SyncError, "schema differs"):
            compare_source_rows(self.rows, incomplete)


if __name__ == "__main__":
    unittest.main()
