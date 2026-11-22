import math
import unittest

from meteo_audit.archive_sync import (
    ARCHIVE_FIELDS, PROTECTED_LOWER_BOUND, SyncError, apply_plan_to_memory,
    build_sync_plan, committed_watermark, map_archive_row,
)

BASE = PROTECTED_LOWER_BOUND + 100_000


def row(ts, **values):
    result = {name: None for name in ARCHIVE_FIELDS}
    result.update(dateTime=ts, usUnits=16, interval=5)
    result.update(values)
    return result


def plan(sources, targets=(), **kw):
    opts = {"watermark": BASE, "window_end": BASE + 10_000, "lookback_seconds": 2_000}
    opts.update(kw)
    return build_sync_plan(sources, targets, **opts)


class InsertOnlyPlannerTests(unittest.TestCase):
    def test_full_80_column_mapping_preserves_explicit_nulls(self):
        src = row(BASE + 100, outTemp=12.5)
        mapped = map_archive_row(src)
        self.assertEqual(set(mapped), ARCHIVE_FIELDS)
        self.assertIsNone(mapped["outHumidity"])
        p = plan([src])
        self.assertEqual(p.actions[0].kind, "INSERT_ROW")
        self.assertEqual(set(p.actions[0].values), ARCHIVE_FIELDS)

    def test_incomplete_source_row_blocks(self):
        src = row(BASE + 100, outTemp=12.5); del src["outHumidity"]
        with self.assertRaisesRegex(SyncError, "schema mismatch"):
            plan([src])

    def test_wrong_interval_blocks_cursor(self):
        p = plan([row(BASE + 100, interval=60, outTemp=2)])
        self.assertTrue(p.conflicts)
        self.assertEqual(p.proposed_watermark, BASE)

    def test_wrong_units_block_cursor(self):
        p = plan([row(BASE + 100, usUnits=17, outTemp=2)])
        self.assertTrue(p.conflicts)
        self.assertEqual(p.proposed_watermark, BASE)

    def test_nan_and_infinity_rejected(self):
        for bad in (math.nan, math.inf, -math.inf):
            with self.subTest(value=bad), self.assertRaises(SyncError):
                plan([row(BASE + 100, outTemp=bad)])

    def test_non_numeric_and_boolean_rejected(self):
        for bad in ("12.3", True):
            with self.subTest(value=bad), self.assertRaises(SyncError):
                plan([row(BASE + 100, outTemp=bad)])

    def test_schema_drift_missing_or_extra_source_or_target_column_blocks(self):
        for kw in ({"source_schema": ARCHIVE_FIELDS - {"outTemp"}},
                   {"target_schema": ARCHIVE_FIELDS | {"newField"}}):
            with self.subTest(kw=kw), self.assertRaises(SyncError):
                plan([row(BASE + 100, outTemp=1)], **kw)

    def test_all_null_row_blocks_watermark(self):
        p = plan([row(BASE + 100)])
        self.assertTrue(p.conflicts)
        self.assertEqual(p.proposed_watermark, BASE)

    def test_strict_protection_boundary_is_excluded(self):
        p = plan([row(PROTECTED_LOWER_BOUND, outTemp=1), row(PROTECTED_LOWER_BOUND + 1, outTemp=2)])
        self.assertEqual([a.timestamp for a in p.actions], [PROTECTED_LOWER_BOUND + 1])

    def test_protected_field_blocks_insert_when_timestamp_is_absent(self):
        ts = BASE + 100
        p = plan([row(ts, outTemp=1)], protected_fields={(ts, "outTemp")})
        self.assertEqual(p.actions, ())
        self.assertIn("protected fields", p.conflicts[0].reason)

    def test_target_metadata_conflict_never_updates_existing_timestamp(self):
        src = row(BASE + 100, outTemp=1)
        dst = row(BASE + 100, usUnits=17, interval=5, outTemp=1)
        p = plan([src], [dst])
        self.assertEqual(p.actions, ())
        self.assertTrue(p.conflicts)
        self.assertEqual(dst["usUnits"], 17)

    def test_missing_timestamp_inserts_only(self):
        p = plan([row(BASE + 100, outTemp=12.5)])
        self.assertEqual([a.kind for a in p.actions], ["INSERT_ROW"])

    def test_existing_timestamp_never_fills_null(self):
        source = row(BASE + 100, outTemp=12.5, outHumidity=70)
        target = row(BASE + 100, outTemp=12.5)
        p = plan([source], [target])
        self.assertEqual(p.actions, ())
        self.assertTrue(any(x.variable == "outHumidity" for x in p.conflicts))
        self.assertIsNone(target["outHumidity"])
        self.assertEqual(p.proposed_watermark, BASE)

    def test_existing_equal_row_is_idempotent(self):
        source = row(BASE + 100, outTemp=12.5)
        p = plan([source], [source])
        self.assertEqual(p.actions, ())
        self.assertEqual(p.conflicts, ())

    def test_existing_conflict_is_never_updated(self):
        src = row(BASE + 100, outTemp=12.5)
        dst = row(BASE + 100, outTemp=11.0)
        p = plan([src], [dst])
        self.assertEqual(p.actions, ())
        self.assertEqual(p.conflicts[0].variable, "outTemp")
        self.assertEqual(dst["outTemp"], 11.0)

    def test_late_arrival_after_fence_is_inserted(self):
        ts = BASE + 10
        p = plan([row(ts, outTemp=1)], watermark=BASE + 1_000)
        self.assertEqual([a.timestamp for a in p.actions], [ts])

    def test_late_arrival_before_fence_is_ignored(self):
        p = plan([row(PROTECTED_LOWER_BOUND, outTemp=1)], watermark=BASE + 1_000)
        self.assertEqual(p.actions, ())
        self.assertEqual(p.proposed_watermark, BASE + 1_000)

    def test_concurrent_target_insert_is_detected_before_writer(self):
        src = row(BASE + 100, outTemp=1)
        p = plan([src])
        with self.assertRaisesRegex(SyncError, "appeared after planning"):
            apply_plan_to_memory(p, [src])

    def test_repeated_run_is_idempotent(self):
        src = row(BASE + 100, outTemp=1)
        first = plan([src]); after = apply_plan_to_memory(first, [])
        second = plan([src], after, watermark=first.proposed_watermark)
        self.assertEqual(second.actions, ())
        self.assertEqual(second.conflicts, ())

    def test_restart_uses_committed_cursor_and_replay_overlap(self):
        src = row(BASE + 100, outTemp=1); first = plan([src])
        target = apply_plan_to_memory(first, [])
        cursor = committed_watermark(first, transaction_succeeded=True)
        restarted = plan([src], target, watermark=cursor)
        self.assertEqual(restarted.actions, ())

    def test_commit_failure_keeps_old_cursor_and_target_copy(self):
        srcs = [row(BASE + 100, outTemp=1), row(BASE + 200, outTemp=2)]
        p = plan(srcs)
        target = []
        with self.assertRaises(RuntimeError):
            apply_plan_to_memory(p, target, fail_after=1)
        self.assertEqual(target, [])
        self.assertEqual(committed_watermark(p, transaction_succeeded=False), BASE)

    def test_conflict_never_advances_cursor(self):
        p = plan([row(BASE + 100, interval=60, outTemp=1)])
        self.assertEqual(committed_watermark(p, transaction_succeeded=True), BASE)

    def test_source_outage_is_not_empty_success(self):
        with self.assertRaises(SyncError):
            plan([], source_complete=False)

    def test_inclusive_captured_max_uses_max_plus_one_exclusive_end(self):
        ts = BASE + 100
        p = plan([row(ts, outTemp=1)], window_end=ts + 1)
        self.assertEqual(p.captured_source_max, ts)
        self.assertEqual([x.timestamp for x in p.actions], [ts])

    def test_exclusive_window_end_does_not_import_future_row(self):
        ts = BASE + 100
        p = plan([row(ts, outTemp=1)], window_end=ts)
        self.assertEqual(p.actions, ())

    def test_conflicting_source_duplicates_block(self):
        p = plan([row(BASE + 100, outTemp=1), row(BASE + 100, outTemp=2)])
        self.assertTrue(p.conflicts)
        self.assertEqual(p.proposed_watermark, BASE)


if __name__ == "__main__":
    unittest.main()
