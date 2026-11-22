#!/usr/bin/env python3
"""Verify deterministic replay of generated audit evidence and decisions."""
from __future__ import annotations
import hashlib, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=tuple(ROOT/p for p in (
    "MONTHLY_VALIDATION_EVIDENCE.json",
    "PROVENANCE_COUNTS_CORRECTED.json",
    "data/STATISTICAL_VARIANTS_MONTHLY.csv",
    "data/STATISTICAL_VARIANTS_ANNUAL.csv",
    "data/STATISTICAL_VARIANTS_MANIFEST.json",
    "MONTHLY_PUBLICATION_CANDIDATES.json",
    "HISTORICAL_CONFLICT_SUBTYPES_SUMMARY.json",
    "data/HISTORICAL_CONFLICT_SUBTYPES_SUMMARY.json",
    "PILOT_2026_01_VALIDATED_STATISTICS.json",
    "STATISTICAL_PUBLICATION_DECISIONS_V2.csv",
    "STATISTICAL_PUBLICATION_DECISIONS_V2.json",
    "MASTER_GOAL_PUBLICATION_PILOT_EVIDENCE.json",
    "TEMPERATURE_REFERENCE_AVAILABILITY.json",
    "MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json",
    "TEMPERATURE_CANDIDATE_EXPERT_REVIEW.json",
    "TEMPERATURE_CANDIDATE_EXPERT_REVIEW.md",
    "data/chmi-priority-temperature/manifest.json",
    "data/chmi-historical-daily-temperature/manifest.json",
    "CHMI_DAILY_TEMPERATURE_CONTEXT_REVIEW.json",
    "CHMI_DAILY_TEMPERATURE_CONTEXT_REVIEW.md",
    "INTERVAL_COVERAGE_REVIEW.json",
    "INTERVAL_ADJUSTED_MONTHLY_MEANS.json",
    "INTERVAL_TIME_METHOD_REVIEW.md",
    "MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json",
    "HUMIDITY_DAILY_REFERENCE_CONTEXT.json",
    "HUMIDITY_CANDIDATE_VALIDATION_REVIEW.json",
    "HUMIDITY_CANDIDATE_VALIDATION_REVIEW.md",
    "HUMIDITY_SENSOR_VALIDATION_REPORT.md",
    "MONTHLY_PRESSURE_REFERENCE_VALIDATION.json",
    "PRESSURE_DAILY_REFERENCE_CONTEXT.json",
    "data/chmi-daily-pressure/manifest.json",
    "data/chmi-daily-pressure/raw/dly-0-203-0-11777-P.csv",
    "data/chmi-daily-pressure/raw/dly-0-203-0-11778-P.csv",
    "data/chmi-daily-pressure/raw/dly-0-20000-0-11774-P.csv",
    "MONTHLY_WIND_REFERENCE_VALIDATION.json",
    "TEMPERATURE_MONTHLY_VALIDATION_REPORT.md",
    "data/reference-inventory/reference_source_catalog.json",
    "REFERENCE_STATION_CATALOG.json",
    "MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json",
    "MONTHLY_VALIDATION_RESULTS.json",
    "LOCAL_STATION_METADATA_SEARCH.json",
    "HUMIDITY_MONTHLY_SERIES_REVIEW.md",
    "HUMIDITY_SENSOR_VALIDATION_REPORT.md",
    "PRESSURE_CANDIDATE_SEMANTICS_REVIEW.md",
    "PRESSURE_SEMANTICS_VALIDATION_REPORT.md",
    "WIND_MONTHLY_VALIDATION_REPORT.md",
    "data/PUBLICATION_READINESS_DECISIONS.csv",
    "data/PUBLICATION_READINESS_DECISIONS.json",
    "STATISTICAL_PUBLICATION_DECISIONS_V3.csv",
    "STATISTICAL_PUBLICATION_DECISIONS_V3.json",
    "HISTORICAL_CONFLICT_EPOCH_REVIEW.json",
    "HISTORICAL_CONFLICT_EPOCH_REVIEW.md",
    "THREE_UNMATCHED_TEMPERATURE_VALUES_REVIEW.json",
    "CURRENT_GW3000_E4_VALIDATION_REPORT.md",
    "CURRENT_GW3000_E4_VALIDATION.json",
    "data/gw3000-current-readonly/capture-20261116T010749Z.json",
    "data/goal-phase-j-sync-health-20261116.json",
    "ATLAS_STATISTICS_CONTRACT.json",
    "atlas_preview/index.html",
))

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def run(script):
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')+os.pathsep+env.get('PYTHONPATH','')
    subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,env=env,check=True,stdout=subprocess.DEVNULL)

def main():
    before={p:digest(p) for p in FILES}
    run(Path("scripts/build_provenance_counts.py"))
    run(Path("scripts/build_statistical_variants.py"))
    run(Path("scripts/validate_chmi_candidate_reference_cache.py"))
    run(Path("scripts/validate_chmi_priority_temperature_cache.py"))
    run(Path("scripts/validate_chmi_pressure_candidate_reference_cache.py"))
    run(Path("scripts/build_reference_data_catalog.py"))
    run(Path("scripts/build_reference_station_catalog.py"))
    run(Path("scripts/build_temperature_reference_availability.py"))
    run(Path("scripts/validate_chmi_daily_temperature_context.py"))
    run(Path("scripts/validate_pilot_chmi_reference.py"))
    run(Path("scripts/build_publication_pilot_v2.py"))
    run(Path("scripts/validate_temperature_monthly_references.py"))
    run(Path("scripts/build_temperature_candidate_expert_review.py"))
    run(Path("scripts/validate_humidity_monthly_references.py"))
    run(Path("scripts/validate_chmi_daily_humidity_cache.py"))
    run(Path("scripts/build_humidity_daily_context_review.py"))
    run(Path("scripts/build_humidity_sensor_validation_report.py"))
    run(Path("scripts/validate_pressure_monthly_reference.py"))
    run(Path("scripts/validate_chmi_daily_pressure_cache.py"))
    run(Path("scripts/build_pressure_daily_reference_context.py"))
    run(Path("scripts/validate_wind_monthly_references.py"))
    run(Path("scripts/build_wind_monthly_validation_report.py"))
    run(Path("scripts/build_temperature_monthly_validation_report.py"))
    run(Path("scripts/build_interval_coverage_review.py"))
    run(Path("scripts/build_interval_adjusted_candidate_means.py"))
    run(Path("scripts/build_interval_time_method_report.py"))
    run(Path("scripts/build_historical_conflict_epoch_review.py"))
    run(Path("scripts/build_three_unmatched_temperature_review.py"))
    run(Path("scripts/build_current_gw3000_e4_report.py"))
    run(Path("scripts/build_monthly_candidate_series_diagnostics.py"))
    run(Path("scripts/build_pressure_candidate_semantics_review.py"))
    run(Path("scripts/build_pressure_semantics_validation_report.py"))
    run(Path("scripts/build_humidity_monthly_series_review.py"))
    run(Path("scripts/build_humidity_candidate_validation_review.py"))
    run(Path("scripts/build_humidity_sensor_validation_report.py"))
    run(Path("scripts/build_monthly_validation_evidence.py"))
    run(Path("scripts/build_epoch_registry_and_monthly_results.py"))
    run(Path("scripts/build_publication_readiness_matrix.py"))
    run(Path("scripts/build_publication_v3.py"))
    # Final V2 output must reflect evidence rebuilt after its initial pilot stage.
    run(Path("scripts/build_publication_pilot_v2.py"))
    run(Path("scripts/build_atlas_statistics_contract.py"))
    after={p:digest(p) for p in FILES}
    if before!=after:
        changed=[p.relative_to(ROOT).as_posix() for p in FILES if before[p]!=after[p]]
        raise SystemExit("Non-deterministic generated outputs: "+", ".join(changed))
    print(f"Deterministic replay verified for {len(FILES)} reference, candidate, evidence and decision artifacts.")

if __name__=="__main__": main()
