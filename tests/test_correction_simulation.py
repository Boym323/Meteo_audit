"""Offline tests for local correction-package simulation; no DB or API calls."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from meteo_audit.simulation import (
    ArchiveRow,
    Correction,
    SimulationConflict,
    order_batches,
    simulate_batch,
)


SCHEMA = ("outTemp", "outHumidity", "rain", "windSpeed")
T0 = 1_700_000_000
SOURCE = {("source_archive", T0, "outTemp"): 12.5,
          ("source_archive", T0, "outHumidity"): 65.0,
          ("source_archive", T0 + 300, "outTemp"): -2.0}


def existing_rows():
    return {
        T0: ArchiveRow(16, 5, {"outTemp": 10.0, "outHumidity": 60.0, "rain": 0.0, "windSpeed": 2.0}),
    }


def correction(variable="outTemp", *, old=10.0, new=12.5, timestamp=T0, source_time=T0,
               operation="update", us_units=None, interval=None):
    return Correction(operation, timestamp, variable, new, old, "source_archive", source_time,
                      SOURCE[("source_archive", source_time, variable)], "offline fixture",
                      us_units, interval)


class CorrectionSimulationTests(unittest.TestCase):
    def test_local_cli_executes_dependency_order_without_database_access(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            package_path = temp / "package.json"
            output_path = temp / "result.json"
            payload = {
                "schema_version": "1.0",
                "schema_columns": list(SCHEMA),
                "archive_rows": [{
                    "timestamp": T0,
                    "us_units": 16,
                    "interval_minutes": 5,
                    "fields": {"outTemp": 10.0, "outHumidity": 60.0, "rain": 0.0, "windSpeed": 2.0},
                }],
                "source_observations": [
                    {"database": "source_archive", "timestamp": T0 + 300, "variable": "outTemp", "value": -2.0},
                    {"database": "source_archive", "timestamp": T0, "variable": "outHumidity", "value": 65.0},
                ],
                "batches": [
                    {"batch_id": "b-dependent", "depends_on": ["a-insert"], "corrections": [{
                        "operation": "update", "timestamp": T0 + 300, "variable": "outHumidity",
                        "new_value": 65.0, "expected_old_value": None,
                        "source_database": "source_archive", "source_time": T0, "source_value": 65.0,
                        "reason": "synthetic fixture",
                    }]},
                    {"batch_id": "a-insert", "depends_on": [], "corrections": [{
                        "operation": "insert", "timestamp": T0 + 300, "variable": "outTemp",
                        "new_value": -2.0, "expected_old_value": None,
                        "source_database": "source_archive", "source_time": T0 + 300, "source_value": -2.0,
                        "reason": "synthetic fixture", "us_units": 16, "interval_minutes": 5,
                    }]},
                ],
            }
            package_path.write_text(json.dumps(payload), encoding="utf-8")
            subprocess.run([
                sys.executable, str(root / "scripts/simulate_local_correction_package.py"),
                str(package_path), "--output", str(output_path),
            ], cwd=root, check=True, capture_output=True, text=True)
            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(result["simulation_scope"], "LOCAL_ONLY_NOT_DATABASE_DRY_RUN")
            self.assertEqual(result["batch_order"], ["a-insert", "b-dependent"])
            new_row = result["final_rows"][str(T0 + 300)]
            self.assertEqual(new_row["fields"]["outTemp"], -2.0)
            self.assertEqual(new_row["fields"]["outHumidity"], 65.0)
            self.assertEqual((new_row["us_units"], new_row["interval_minutes"]), (16, 5))

    def test_update_preserves_other_fields_and_record_metadata(self):
        before = existing_rows()
        result, _ = simulate_batch(before, [correction()], SOURCE, SCHEMA, batch_id="batch-a")
        self.assertEqual(before[T0].fields["outTemp"], 10.0)
        self.assertEqual(result.output_rows[T0].fields["outTemp"], 12.5)
        self.assertEqual(result.output_rows[T0].fields["outHumidity"], 60.0)
        self.assertEqual(result.output_rows[T0].fields["rain"], 0.0)
        self.assertEqual(result.output_rows[T0].us_units, 16)
        self.assertEqual(result.output_rows[T0].interval_minutes, 5)
        self.assertEqual(result.before_stats["outTemp"]["sum"], 10.0)
        self.assertEqual(result.after_stats["outTemp"]["sum"], 12.5)

    def test_insert_then_update_same_new_record_is_composed_locally(self):
        timestamp = T0 + 300
        insert = correction("outTemp", old=None, new=-2.0, timestamp=timestamp,
                            source_time=timestamp, operation="insert", us_units=16, interval=5)
        update = correction("outHumidity", old=None, new=65.0, timestamp=timestamp,
                            source_time=T0, operation="update")
        # The humidity source timestamp differs from the new target timestamp.
        rows = existing_rows()
        batch, ledger = simulate_batch(rows, [insert, update], SOURCE, SCHEMA, batch_id="new-row")
        new_row = batch.output_rows[timestamp]
        self.assertEqual(new_row.fields["outTemp"], -2.0)
        self.assertEqual(new_row.fields["outHumidity"], 65.0)
        self.assertIsNone(new_row.fields["rain"])
        self.assertEqual((new_row.us_units, new_row.interval_minutes), (16, 5))
        self.assertIn("new-row", ledger)

    def test_null_expected_state_for_insert_is_distinct_from_missing_source(self):
        timestamp = T0 + 300
        insert = correction("outTemp", old=None, new=-2.0, timestamp=timestamp,
                            source_time=timestamp, operation="insert", us_units=16, interval=5)
        result, _ = simulate_batch(existing_rows(), [insert], SOURCE, SCHEMA, batch_id="insert-null")
        self.assertIn(timestamp, result.output_rows)
        self.assertEqual(result.before_stats["outTemp"]["nonnull_count"], 1)
        self.assertEqual(result.after_stats["outTemp"]["nonnull_count"], 2)

    def test_update_can_clear_a_field_only_when_expected_value_matches(self):
        clear = correction("outHumidity", old=60.0, new=None)
        result, _ = simulate_batch(existing_rows(), [clear], SOURCE, SCHEMA, batch_id="clear-field")
        self.assertIsNone(result.output_rows[T0].fields["outHumidity"])
        self.assertEqual(result.before_stats["outHumidity"]["nonnull_count"], 1)
        self.assertEqual(result.after_stats["outHumidity"]["nonnull_count"], 0)
        self.assertEqual(result.after_stats["outHumidity"]["null_count"], 1)

    def test_expected_old_conflict_discards_prior_operations_in_batch(self):
        before = existing_rows()
        first = correction("outTemp", new=12.5)
        second = correction("outHumidity", old=999.0, new=65.0)
        with self.assertRaises(SimulationConflict):
            simulate_batch(before, [first, second], SOURCE, SCHEMA, batch_id="conflict")
        self.assertEqual(before, existing_rows())

    def test_injected_mid_batch_error_discards_all_local_changes(self):
        before = existing_rows()
        package = [correction("outTemp", new=12.5), correction("outHumidity", old=60.0, new=65.0)]
        with self.assertRaisesRegex(RuntimeError, "injected local mid-batch"):
            simulate_batch(before, package, SOURCE, SCHEMA, batch_id="fault", fail_after=1)
        self.assertEqual(before, existing_rows())

    def test_duplicate_target_in_package_is_rejected(self):
        with self.assertRaisesRegex(SimulationConflict, "duplicate target"):
            simulate_batch(existing_rows(), [correction(), correction(new=13.0)], SOURCE, SCHEMA,
                           batch_id="duplicate")

    def test_existing_timestamp_blocks_insert(self):
        insert = correction("outTemp", operation="insert", old=None, new=12.5,
                            us_units=16, interval=5)
        with self.assertRaisesRegex(SimulationConflict, "already exists"):
            simulate_batch(existing_rows(), [insert], SOURCE, SCHEMA, batch_id="existing")

    def test_missing_or_changed_source_value_is_rejected(self):
        bad = correction(new=12.5)
        bad = Correction(**{**bad.__dict__, "source_value": 13.0})
        with self.assertRaisesRegex(SimulationConflict, "source_value differs"):
            simulate_batch(existing_rows(), [bad], SOURCE, SCHEMA, batch_id="source-conflict")

    def test_same_batch_content_is_idempotent_but_changed_content_conflicts(self):
        package = [correction()]
        first, ledger = simulate_batch(existing_rows(), package, SOURCE, SCHEMA, batch_id="stable")
        second, _ = simulate_batch(first.output_rows, package, SOURCE, SCHEMA,
                                   batch_id="stable", prior_batches=ledger)
        self.assertEqual(second.status, "idempotent_noop")
        self.assertEqual(second.applied_operations, 0)
        changed = [correction(new=13.0)]
        with self.assertRaisesRegex(SimulationConflict, "different content"):
            simulate_batch(first.output_rows, changed, SOURCE, SCHEMA,
                           batch_id="stable", prior_batches=ledger)

    def test_dependency_order_is_stable_and_cycles_are_rejected(self):
        batches = [
            {"batch_id": "derived", "depends_on": ["primary"]},
            {"batch_id": "primary", "depends_on": []},
        ]
        self.assertEqual(order_batches(batches), ["primary", "derived"])
        with self.assertRaisesRegex(SimulationConflict, "cycle"):
            order_batches([{"batch_id": "a", "depends_on": ["b"]},
                           {"batch_id": "b", "depends_on": ["a"]}])
        with self.assertRaisesRegex(SimulationConflict, "unknown batch"):
            order_batches([{"batch_id": "a", "depends_on": ["missing"]}])


if __name__ == "__main__":
    unittest.main()
