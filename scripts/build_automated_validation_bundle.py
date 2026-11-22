#!/usr/bin/env python3
"""Create a compact deterministic bundle of current validation results and code."""
import hashlib, json, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "loucka_automated_validation_completion_v1.zip"
FILES = [
    "MASTER_GOAL_AUTOMATED_VALIDATION_REPORT.md", "MASTER_GOAL_AUTOMATED_VALIDATION_EVIDENCE.json",
    "MASTER_GOAL_AUTOMATED_VALIDATION_PROGRESS.json", "MASTER_GOAL_AUTOMATED_VALIDATION_CANDIDATE_OUTCOMES.json", "AUTOMATED_VALIDATION_RUN.json",
    "MONTHLY_EVIDENCE_REPLAY_RESULT.json",
    "HUMIDITY_PLATEAU_CONTEXT_REPLAY_RESULT.json",
    "ANNUAL_INTERVAL_AWARE_TEMPERATURE_REVIEW.json", "ANNUAL_REPRESENTATIVENESS_REVIEW.json",
    "MONTHLY_VALIDATION_RESULTS.json", "MONTHLY_VALIDATION_EVIDENCE.json", "MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json",
    "STATION_SENSOR_EPOCH_REGISTRY.json", "LOCAL_STATION_METADATA_SEARCH.json", "POST_PIPELINE_VALIDATION_AUDIT.json", "data/source-lineage/public_station_history_20261113.json", "REFERENCE_STATION_CATALOG.json",
    "MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json", "TEMPERATURE_CANDIDATE_EXPERT_REVIEW.json", "TEMPERATURE_CANDIDATE_EXPERT_REVIEW.md", "MONTHLY_HUMIDITY_REFERENCE_VALIDATION.json", "MONTHLY_PRESSURE_REFERENCE_VALIDATION.json", "MONTHLY_WIND_REFERENCE_VALIDATION.json", "TEMPERATURE_REFERENCE_AVAILABILITY.json",
    "HUMIDITY_DAILY_REFERENCE_CONTEXT.json", "data/chmi-daily-humidity/manifest.json", "data/chmi-daily-humidity/raw/dly-0-203-0-11777-H.csv", "data/chmi-daily-humidity/raw/dly-0-203-0-11778-H.csv",
    "HUMIDITY_CANDIDATE_VALIDATION_REVIEW.json", "HUMIDITY_CANDIDATE_VALIDATION_REVIEW.md",
    "PRESSURE_DAILY_REFERENCE_CONTEXT.json", "data/chmi-daily-pressure/manifest.json",
    "data/chmi-daily-pressure/raw/dly-0-203-0-11777-P.csv", "data/chmi-daily-pressure/raw/dly-0-203-0-11778-P.csv", "data/chmi-daily-pressure/raw/dly-0-20000-0-11774-P.csv",
    "TEMPERATURE_MONTHLY_VALIDATION_REPORT.md", "HUMIDITY_SENSOR_VALIDATION_REPORT.md",
    "PRESSURE_SEMANTICS_VALIDATION_REPORT.md", "PRESSURE_CANDIDATE_SEMANTICS_REVIEW.md", "WIND_MONTHLY_VALIDATION_REPORT.md",
    "data/chmi-2026-synop-pressure/manifest.json", "data/chmi-2026-synop-pressure/raw/1h-0-20000-0-11774-202601.json",
    "data/chmi-2026-synop-pressure/raw/1h-0-20000-0-11774-202602.json", "HUMIDITY_MONTHLY_SERIES_REVIEW.md", "HISTORICAL_CONFLICT_EPOCH_REVIEW.json", "HISTORICAL_CONFLICT_EPOCH_REVIEW.md",
    "THREE_UNMATCHED_TEMPERATURE_VALUES_REVIEW.json", "CURRENT_GW3000_E4_VALIDATION_REPORT.md",
    "CURRENT_GW3000_E4_VALIDATION.json", "data/gw3000-current-readonly/capture-20261116T010749Z.json",
    "scripts/capture_gw3000_live_e4_readonly_evidence.py", "data/goal-phase-j-sync-health-20261116.json", "STATISTICAL_PUBLICATION_POLICY_V3.md",
    "STATISTICAL_PUBLICATION_DECISIONS_V3.csv", "STATISTICAL_PUBLICATION_DECISIONS_V3.json", "data/PUBLICATION_READINESS_DECISIONS.csv", "data/PUBLICATION_READINESS_DECISIONS.json",
    "ATLAS_STATISTICS_CONTRACT.json", "ATLAS_LOCAL_PREVIEW_REPORT.md", "atlas_preview/index.html",
    "INTERVAL_COVERAGE_REVIEW.json", "INTERVAL_ADJUSTED_MONTHLY_MEANS.json", "INTERVAL_TIME_METHOD_REVIEW.md",
    "data/STATISTICAL_VARIANTS_MANIFEST.json", "data/historical_value_concordance.manifest.json",
    "data/INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MONTHLY.csv", "data/INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_ANNUAL.csv", "data/INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MANIFEST.json",
    "MONTHLY_PUBLICATION_CANDIDATES.json", "data/STATISTICAL_VARIANTS_MONTHLY.csv", "data/STATISTICAL_VARIANTS_ANNUAL.csv",
    "data/STATISTICAL_READINESS_CURRENT.json",
    "data/STATISTICAL_READINESS_VALIDATION.json",
    "PROVENANCE_COUNTS_CORRECTED.json",
    "data/reference-inventory/reference_source_catalog.json",
    "data/chmi-2026-recent/manifest.json",
    "data/chmi-priority-temperature/manifest.json",
    "data/chmi-priority-temperature/raw/10m-0-203-0-11777-202212.json",
    "data/chmi-priority-temperature/raw/10m-0-203-0-11778-202212.json",
    "data/chmi-historical-daily-temperature/manifest.json",
    "data/chmi-historical-daily-temperature/raw/dly-0-203-0-11777-T.csv",
    "data/chmi-historical-daily-temperature/raw/dly-0-203-0-11778-T.csv",
    "CHMI_DAILY_TEMPERATURE_CONTEXT_REVIEW.json", "CHMI_DAILY_TEMPERATURE_CONTEXT_REVIEW.md",
    "data/reference-inventory/license_provenance_review_20261113.json",
    "data/publication-pilot-reference/chmi_11777_2026-01_10min.json",
    "scripts/run_automated_validation_pipeline.py", "scripts/build_authoritative_statistical_readiness.py", "scripts/finalize_authoritative_statistical_outputs.py", "src/meteo_audit/readiness_snapshot_adapter.py", "tests/test_readiness_snapshot_adapter.py", "scripts/build_provenance_counts.py", "scripts/build_statistical_variants.py", "scripts/build_monthly_validation_evidence.py",
    "scripts/build_annual_representativeness_review.py", "scripts/build_interval_aware_annual_temperature_review.py",
    "src/meteo_audit/interval_period_stats.py", "tests/test_interval_period_stats.py",
    "scripts/build_publication_pilot_v2.py",
    "scripts/fetch_chmi_candidate_reference_cache.py", "scripts/validate_chmi_candidate_reference_cache.py",
    "scripts/fetch_chmi_priority_temperature_cache.py", "scripts/validate_chmi_priority_temperature_cache.py",
    "scripts/build_temperature_reference_availability.py", "scripts/validate_temperature_monthly_references.py",
    "scripts/validate_humidity_monthly_references.py", "scripts/fetch_chmi_daily_humidity_context.py", "scripts/validate_chmi_daily_humidity_cache.py", "scripts/build_humidity_daily_context_review.py", "scripts/build_humidity_candidate_validation_review.py", "scripts/build_humidity_sensor_validation_report.py",
    "scripts/fetch_chmi_pressure_candidate_reference_cache.py", "scripts/validate_chmi_pressure_candidate_reference_cache.py",
    "scripts/validate_pressure_monthly_reference.py", "scripts/build_pressure_semantics_validation_report.py",
    "scripts/fetch_chmi_daily_pressure_context.py", "scripts/validate_chmi_daily_pressure_cache.py", "scripts/build_pressure_daily_reference_context.py",
    "scripts/validate_wind_monthly_references.py", "scripts/build_wind_monthly_validation_report.py",
    "scripts/validate_pilot_chmi_reference.py", "scripts/build_reference_data_catalog.py",
    "scripts/build_reference_station_catalog.py", "scripts/build_temperature_monthly_validation_report.py", "scripts/build_temperature_candidate_expert_review.py",
    "scripts/fetch_chmi_historical_daily_temperature_context.py", "scripts/validate_chmi_daily_temperature_context.py",
    "scripts/build_epoch_registry_and_monthly_results.py", "scripts/audit_local_station_metadata_sources.py", "scripts/validate_automated_validation_postrun.py", "scripts/validate_final_report_bundle.py", "scripts/build_monthly_candidate_series_diagnostics.py", "scripts/build_humidity_monthly_series_review.py", "scripts/build_pressure_candidate_semantics_review.py", "scripts/build_publication_readiness_matrix.py",
    "scripts/build_publication_v3.py", "scripts/build_atlas_statistics_contract.py",
    "scripts/build_interval_weighted_statistical_variants.py", "tests/test_interval_weighted_variants.py",
    "scripts/build_interval_coverage_review.py", "scripts/build_interval_adjusted_candidate_means.py", "scripts/build_interval_time_method_report.py",
    "scripts/build_historical_conflict_epoch_review.py", "scripts/build_three_unmatched_temperature_review.py", "scripts/build_current_gw3000_e4_report.py",
    "scripts/verify_monthly_evidence_replay.py", "tests/test_atlas_preview_http.py", "scripts/build_automated_validation_candidate_outcomes.py", "scripts/build_automated_validation_report.py", "tests/test_automated_candidate_outcomes.py",
    "scripts/build_automated_validation_progress.py", "scripts/build_automated_validation_bundle.py",
    "src/meteo_audit/publication_classifier.py", "src/meteo_audit/provenance_counts.py", "src/meteo_audit/time_bounds.py",
    "tests/test_atlas_statistics_contract.py", "tests/test_time_bounds.py",
    "tests/test_publication_pilot_v2.py", "tests/test_provenance_counts.py", "tests/test_statistical_variants.py", "tests/test_temperature_reference_validation.py",
    "tests/test_publication_v3_exports.py", "tests/test_historical_conflict_epoch_review.py",
    "tests/test_current_gw3000_e4.py", "tests/test_epoch_registry_and_monthly_results.py",
    "tests/test_three_unmatched_temperature_review.py", "tests/test_humidity_reference_validation.py",
    "tests/test_pressure_reference_validation.py",
    "tests/test_wind_reference_validation.py",
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    contents = {}
    for rel in FILES:
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"Required bundle input is missing: {rel}")
        contents[rel] = path.read_bytes()
    snapshot = json.loads((ROOT / "AUTOMATED_VALIDATION_RUN.json").read_text())["snapshot_id"]
    instructions = (
        "# Automated validation completion bundle\n\n"
        "The public CHMI temperature/RH cache can be recreated with `python3 scripts/fetch_chmi_candidate_reference_cache.py`; verify it with `python3 scripts/validate_chmi_candidate_reference_cache.py`. The priority-month historical temperature cache can be recreated from official CHMI monthly URLs with `python3 scripts/fetch_chmi_priority_temperature_cache.py`; verify cached bytes with `python3 scripts/validate_chmi_priority_temperature_cache.py`. Its manifest records HTTP 404 periods as unavailable. The December 2022 raw files for Vizovice and Kladna-Zilin are included because the three-value review uses their exact UTC observations as regional context. Other priority-cache bytes remain local and are identified by the included manifest. CHMI daily mean temperature context is cached and reviewed with `python3 scripts/fetch_chmi_historical_daily_temperature_context.py` and `python3 scripts/validate_chmi_daily_temperature_context.py`; its day-boundary mismatch remains explicit. The two Holešov hourly P_hm files are included in the bundle and can be recreated with `python3 scripts/fetch_chmi_pressure_candidate_reference_cache.py`; verify with `python3 scripts/validate_chmi_pressure_candidate_reference_cache.py`.\n\n"
        f"Snapshot SHA-256: `{snapshot}` (the full concordance SQLite is intentionally not bundled).\n\n"
        "On the source host, from `/opt/meteo-audit`, reproduce with:\n\n"
        "```sh\npython3 scripts/run_automated_validation_pipeline.py\n"
        "python3 scripts/build_automated_validation_report.py\n"
        "python3 scripts/build_automated_validation_progress.py\n"
        "python3 scripts/build_automated_validation_bundle.py\n"
        "python3 scripts/verify_monthly_evidence_replay.py\n```\n\n"
        "The single orchestration command runs the host metadata search, immutable-snapshot validations, all specialist stages, regression tests, post-run checks, report/progress generation, ZIP packaging and final validations. The reports state remaining incomplete phases and evidence blockers. This bundle is local audit output; it does not authorize publication or historical database writes.\n"
    ).encode()
    contents["BUNDLE_README.md"] = instructions
    manifest = {"schema": "loucka-validation-bundle-manifest-v1", "snapshot_id": snapshot,
                "files": {k: {"sha256": sha(v), "bytes": len(v)} for k, v in sorted(contents.items())}}
    contents["BUNDLE_MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(json.dumps({"output": str(OUTPUT), "files": len(contents), "bytes": OUTPUT.stat().st_size,
                      "snapshot_id": snapshot, "sha256": sha(OUTPUT.read_bytes())}, indent=2))

if __name__ == "__main__":
    main()
