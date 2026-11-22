#!/usr/bin/env python3
"""Build candidate-only monthly mean outcome counts from current evidence."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def main():
    candidates = load("MONTHLY_PUBLICATION_CANDIDATES.json")["candidates"]
    evidence = load("MONTHLY_VALIDATION_EVIDENCE.json")["records"]
    run = load("AUTOMATED_VALIDATION_RUN.json")
    evidence_keys = {(r["period"], r["variable"]) for r in evidence}
    candidate_keys = {(r["period"], r["variable"]) for r in candidates}
    if len(candidate_keys) != len(candidates) or evidence_keys != candidate_keys:
        raise SystemExit("Candidate/evidence keys are not one-to-one")

    decisions = list(csv.DictReader((ROOT / "data/PUBLICATION_READINESS_DECISIONS.csv").open(encoding="utf-8", newline="")))
    rows = [r for r in decisions if r.get("scope") == "MONTHLY" and r.get("statistic") == "MEAN" and (r["period"], r["variable"]) in candidate_keys]
    decision_keys = {(r["period"], r["variable"]) for r in rows}
    if decision_keys != candidate_keys or len(rows) != len(candidate_keys):
        raise SystemExit("Candidate decision rows are not one-to-one")

    by_status = Counter(r["publication_readiness"] for r in rows)
    by_variable = defaultdict(Counter)
    by_year_variable = defaultdict(Counter)
    for row in rows:
        by_variable[row["variable"]][row["publication_readiness"]] += 1
        by_year_variable[(row["period"][:4], row["variable"])][row["publication_readiness"]] += 1
    evidence_status = Counter(r["evidence_status"] for r in evidence)

    temp_expert = load("TEMPERATURE_CANDIDATE_EXPERT_REVIEW.json")["results"]
    temp_refs = load("MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json")["station_month_results"]
    daily_refs = load("CHMI_DAILY_TEMPERATURE_CONTEXT_REVIEW.json")["results"]
    humidity_refs = load("MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json")["station_month_results"]
    humidity_candidate_review = load("HUMIDITY_CANDIDATE_VALIDATION_REVIEW.json")
    pressure_refs = load("MONTHLY_PRESSURE_REFERENCE_VALIDATION.json")["station_month_results"]
    pressure_daily = load("PRESSURE_DAILY_REFERENCE_CONTEXT.json")
    wind_refs = load("MONTHLY_WIND_REFERENCE_VALIDATION.json")["station_month_results"]
    cand_by_variable = Counter(r["variable"] for r in candidates)
    specialist = {
        "outTemp": {
            "candidates": cand_by_variable["outTemp"],
            "candidate_specific_expert_reviews": len(temp_expert),
            "subdaily_reference_months": len({r["period"] for r in temp_refs}),
            "daily_context_only_months": len({r["period"] for r in daily_refs}),
            "sensor_accuracy_validated": 0,
        },
        "outHumidity": {
            "candidates": cand_by_variable["outHumidity"],
            "monthly_series_screened": cand_by_variable["outHumidity"],
            "candidate_months_with_exact_chmi_reference": len({r["period"] for r in humidity_refs}),
            "candidate_specific_evidence_dispositions": humidity_candidate_review["candidate_count"],
            "daily_context_only_months": humidity_candidate_review["daily_context_only_candidates"],
            "sensor_accuracy_validated": 0,
        },
        "barometer": {
            "candidates": cand_by_variable["barometer"],
            "monthly_semantics_screened": cand_by_variable["barometer"],
            "candidate_months_with_chmi_pressure_reference": len({r["period"] for r in pressure_refs}),
            "candidate_months_with_daily_chmi_p_context": pressure_daily["candidate_periods_with_quality_zero_daily_avg"],
            "sensor_accuracy_validated": 0,
        },
    }
    for variable in ("windSpeed", "windGust", "windDir"):
        specialist[variable] = {
            "candidates": cand_by_variable[variable],
            "station_month_reference_records": sum(r["variable"] == variable for r in wind_refs),
            "sensor_accuracy_validated": 0,
        }

    controlled = {"READY_FOR_PUBLICATION", "READY_WITH_DISCLOSED_LIMITATIONS", "REVIEW_REQUIRED_SENSOR_VALIDATION", "REVIEW_REQUIRED_CONFLICTS", "REVIEW_REQUIRED_ESTIMATES"}
    out = {
        "schema": "loucka-priority-candidate-outcomes-v1",
        "snapshot_id": run["snapshot_id"],
        "candidate_count": len(rows),
        "recommendations": {
            "READY_FOR_PUBLICATION": by_status["READY_FOR_PUBLICATION"],
            "READY_WITH_DISCLOSED_LIMITATIONS": by_status["READY_WITH_DISCLOSED_LIMITATIONS"],
            "awaiting_physical_or_sensor_validation": by_status["REVIEW_REQUIRED_SENSOR_VALIDATION"],
            "awaiting_conflict_resolution": by_status["REVIEW_REQUIRED_CONFLICTS"],
            "awaiting_estimate_review": by_status["REVIEW_REQUIRED_ESTIMATES"],
            "other_review_states": sum(n for status, n in by_status.items() if status not in controlled),
            "explicitly_rejected": 0,
        },
        "decision_counts_by_variable": {v: dict(sorted(c.items())) for v, c in sorted(by_variable.items())},
        "decision_counts_by_year_variable": {
            year: {variable: dict(sorted(counts.items())) for (y, variable), counts in sorted(by_year_variable.items()) if y == year}
            for year in sorted({year for year, _ in by_year_variable})
        },
        "evidence_status_counts": dict(sorted(evidence_status.items())),
        "specialist_analysis_coverage_by_variable": specialist,
        "interpretation": "Regional comparison or series screening means analyzed, not thereby sensor-validated. Review states are pending evidence, not rejection; readiness does not authorize publication.",
    }
    path = ROOT / "MASTER_GOAL_AUTOMATED_VALIDATION_CANDIDATE_OUTCOMES.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": len(rows), "recommendations": out["recommendations"], "output": str(path)}, indent=2))


if __name__ == "__main__":
    main()
