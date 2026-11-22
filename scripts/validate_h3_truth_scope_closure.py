#!/usr/bin/env python3
"""Validate H3 closure scope against frozen, previously reviewed evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "data/h3_truth_scope_closure.json").read_text())
assert data["status"] == "COMPLETED_WITH_LIMITATIONS"
assert data["observed_evidence"]["long_gaps_at_least_24h"] == 44
assert data["observed_evidence"]["conditional_five_minute_slots_not_observed_truth"] == 97048
assert data["observed_evidence"]["per_archive_coverage_sources"] == 6
assert data["observed_evidence"]["unqueried_archives_in_long_gap_screen"] == 0
assert data["observed_evidence"]["longest_2011_2012_gap_has_local_reference_observations_inside"] is False
assert data["observed_evidence"]["source_temperature_zero_chunks_reviewed"] == 21
assert data["observed_evidence"]["source_temperature_zero_records_reviewed"] == 42298
assert data["observed_evidence"]["temperature_masked_complete_case_blocks"] == 19714
assert data["observed_evidence"]["temperature_masked_24h_blocks"] == 571
assert data["observed_evidence"]["masked_holdout_is_actual_missing_window_truth"] is False
assert data["observed_evidence"]["direct_local_truth_records_for_actual_missing_targets"] == 0
assert data["observed_evidence"]["CHMI_role"] == "independent regional context; not Loucka local truth"
assert data["decision"]["direct_truth_test_passed"] is False
assert data["decision"]["model_released"] is False
assert data["decision"]["temperature_corrections_created"] == 0
assert data["decision"]["actual_missing_windows_certified"] == 0
for path in data["evidence_files"]:
    assert (ROOT / path).is_file(), path
report = (ROOT / "reports/2026-11-13-H3-truth-validation-closure.md").read_text()
assert "truth-validovaných skutečných missing targets **0**" in report
assert "H5" in report
assert "H4 uncertainty-contract review subsequently closed" in data["current_status_update"]
assert data["decision"]["remaining_dependencies"] == ["H5", "C3", "B5", "K3", "L3"]
print("PASS: H3 closes only the available-evidence review; 0 actual missing targets are truth-certified; H5 remains open")
