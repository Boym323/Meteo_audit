#!/usr/bin/env python3
"""Summarize existing active P3 uncertainty metadata without refitting models."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = ROOT / "data/h4_active_p3_uncertainty_contract.json"
if OUTPUT_JSON.exists():
    recorded_at = json.loads(OUTPUT_JSON.read_text()).get("recorded_at_utc")
else:
    from datetime import datetime, timezone
    recorded_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
ops = json.loads((ROOT / "proposals/estimated_short_temperature_gaps_v2/corrections.json").read_text())
metadata = json.loads((ROOT / "proposals/estimated_short_temperature_gaps_v2/candidate_metadata.json").read_text())
by_time = {row["timestamp"]: row for row in metadata}
assert len(ops) == 21 and len({row["timestamp"] for row in ops}) == 21
selected = [by_time[row["timestamp"]] for row in ops]
groups = defaultdict(list)
for row in selected:
    groups[int(row["gap_s"])].append(row)

duration_summary = []
for duration, rows in sorted(groups.items()):
    u = [row["uncertainty"] for row in rows]
    legacy = [row["uncertainty_legacy_general_validation_abs_error_c"]["p95"] for row in rows]
    contracts = [row["uncertainty_contract"] for row in rows]
    contexts = [row["contextual_input_uncertainty"]["status"] for row in rows]
    duration_summary.append({
        "gap_seconds": duration,
        "active_candidate_count": len(rows),
        "conditional_holdout_episodes_per_candidate": sorted({x["complete_masked_episodes"] for x in u}),
        "conditional_holdout_points_per_candidate": sorted({x["holdout_point_errors"] for x in u}),
        "conditional_p95_abs_error_upper_bins_c": sorted({x["p95_abs_error_c_upper_bin"] for x in u}),
        "conditional_sample_max_abs_error_upper_bins_c": sorted({x["observed_sample_max_abs_error_c_upper_bin"] for x in u}),
        "legacy_general_p95_c": sorted(set(legacy)),
        "individual_prediction_interval_guaranteed": all(x["individual_prediction_interval_guaranteed"] for x in contracts),
        "context_uncertainty_statuses": sorted(set(contexts)),
    })

timestamps = sorted(row["timestamp"] for row in ops)
episodes = 1 + sum(right - left > 300 for left, right in zip(timestamps, timestamps[1:]))
assert episodes == 13
result = {
    "schema": "h4-active-p3-uncertainty-contract-v1",
    "recorded_at_utc": recorded_at,
    "database_access": "NONE",
    "active_p3_operations": len(ops),
    "active_p3_unique_timestamps": len(timestamps),
    "active_p3_episodes": episodes,
    "duration_groups": duration_summary,
    "overall_contract": {
        "conditional_quantiles_are_calibrated_predictive_intervals": False,
        "individual_prediction_interval_guaranteed": False,
        "contextual_input_uncertainty_numerically_calibrated": False,
        "model_specific_statistical_release_threshold_established": False,
        "legacy_general_p95_c": 0.75,
        "legacy_p95_source": "Unconditioned/general 2019–2020 seasonal masked-block holdout metadata; not selected-candidate conditional result.",
        "conditional_p95_range_c": [min(x["conditional_p95_abs_error_upper_bins_c"][0] for x in duration_summary), max(x["conditional_p95_abs_error_upper_bins_c"][-1] for x in duration_summary)],
        "quantile_meaning": "0.1 C empirical histogram upper-edge summaries under selected holdout filters; not individual prediction intervals or guaranteed coverage.",
        "display_policy": "Label ESTIMATED. If shown, distinguish general and conditional holdout cohorts; state sample/episode scope and context-input uncertainty not calibrated. Do not display a guaranteed per-point interval or imply model release approval.",
        "release_state": "NOT_APPROVED; actual MCP dry-run NOT_RUN; NOT_APPLIED",
    },
    "limitations": [
        "Complete-case masked episodes are not actual missing-window truth and do not identify MNAR selection.",
        "Rare extrema, fog, inversion and winter regimes are not covered as local independent truth.",
        "Endpoint context variables, including RH, have no calibrated uncertainty distribution in this contract.",
        "No statistical release threshold or guaranteed individual coverage claim is established.",
    ],
}
OUTPUT_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
with (ROOT / "data/h4_active_p3_uncertainty_by_duration.csv").open("w", newline="", encoding="utf-8") as f:
    fields = ["gap_seconds", "active_candidate_count", "conditional_holdout_episodes_per_candidate", "conditional_holdout_points_per_candidate", "conditional_p95_abs_error_upper_bins_c", "conditional_sample_max_abs_error_upper_bins_c", "legacy_general_p95_c", "individual_prediction_interval_guaranteed", "context_uncertainty_statuses"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for row in duration_summary:
        writer.writerow({k: json.dumps(row[k], separators=(",", ":")) if isinstance(row[k], list) else row[k] for k in fields})
print(f"wrote active uncertainty contract for {len(ops)} operations / {episodes} episodes")
