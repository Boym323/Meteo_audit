#!/usr/bin/env python3
"""Check H4 summary against active P3 proposal and candidate metadata."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "data/h4_active_p3_uncertainty_contract.json").read_text())
ops = json.loads((ROOT / "proposals/estimated_short_temperature_gaps_v2/corrections.json").read_text())
meta = json.loads((ROOT / "proposals/estimated_short_temperature_gaps_v2/candidate_metadata.json").read_text())
assert len(ops) == 21 and len({x["timestamp"] for x in ops}) == 21
assert data["active_p3_operations"] == 21 and data["active_p3_unique_timestamps"] == 21
assert data["active_p3_episodes"] == 13
assert data["overall_contract"]["legacy_general_p95_c"] == 0.75
assert data["overall_contract"]["conditional_p95_range_c"] == [0.3, 0.5]
assert data["overall_contract"]["conditional_quantiles_are_calibrated_predictive_intervals"] is False
assert data["overall_contract"]["individual_prediction_interval_guaranteed"] is False
assert data["overall_contract"]["contextual_input_uncertainty_numerically_calibrated"] is False
assert data["overall_contract"]["model_specific_statistical_release_threshold_established"] is False
by_time = {x["timestamp"]: x for x in meta}
selected = [by_time[x["timestamp"]] for x in ops]
assert all(x["uncertainty_contract"]["individual_prediction_interval_guaranteed"] is False for x in selected)
assert all(x["uncertainty_contract"]["contextual_inputs"] == "NOT_NUMERICALLY_CALIBRATED" for x in selected)
assert all(x["uncertainty_legacy_general_validation_abs_error_c"]["p95"] == 0.75 for x in selected)
assert sorted(g["gap_seconds"] for g in data["duration_groups"]) == [600, 900, 1500]
assert sorted(g["active_candidate_count"] for g in data["duration_groups"]) == [4, 7, 10]
for path in ["data/h4_active_p3_uncertainty_by_duration.csv", "reports/2026-11-13-H4-uncertainty-contract-review.md"]:
    assert (ROOT / path).is_file()
print("PASS: 21 active P3 operations, conditional p95 0.3–0.5 C separated from legacy 0.75 C; no predictive-interval or release-threshold claim")
