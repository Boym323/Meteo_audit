#!/usr/bin/env python3
"""Reproduce the currently implemented safe validation stages locally.

This entrypoint intentionally does not claim to complete the broader audit.
It performs no database writes and does not publish or deploy any output.
"""
from __future__ import annotations
import hashlib,json,subprocess,sys
import os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(label,script,extra_env=None):
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')+os.pathsep+env.get('PYTHONPATH','')
    env.update(extra_env or {})
    subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,env=env,check=True)
    return {'stage':label,'script':str(script),'status':'PASS'}
def main():
    manifest=json.loads((ROOT/'data/STATISTICAL_VARIANTS_MANIFEST.json').read_text())
    snapshot=ROOT/'data/historical_value_concordance.sqlite'
    actual=sha(snapshot)
    if actual!=manifest['concordance_sqlite_sha256']:raise SystemExit('Concordance manifest hash mismatch')
    stages=[]
    # Derive provenance counts from the selected immutable snapshot before
    # reference/evidence decisions consume any provenance summary.
    stages.append(run('dynamic-snapshot-provenance-counts',Path('scripts/build_provenance_counts.py')))
    stages.append(run('concordance-daily-readiness',Path('scripts/build_authoritative_statistical_readiness.py'),{'METEO_AUDIT_CONCORDANCE_READONLY':str(snapshot)}))
    stages.append(run('finalize-concordance-daily-readiness',Path('scripts/finalize_authoritative_statistical_outputs.py')))
    stages.append(run('snapshot-monthly-annual-statistical-variants',Path('scripts/build_statistical_variants.py')))
    stages.append(run('all-period-interval-weighted-variants',Path('scripts/build_interval_weighted_statistical_variants.py')))
    stages.append(run('annual-representativeness-review',Path('scripts/build_annual_representativeness_review.py')))
    stages.append(run('interval-aware-annual-temperature-review',Path('scripts/build_interval_aware_annual_temperature_review.py')))
    ref=json.loads((ROOT/'PILOT_2026_01_EXTERNAL_VALIDATION.json').read_text())
    ref_file=ROOT/'data/publication-pilot-reference/chmi_11777_2026-01_10min.json'
    if sha(ref_file)!=ref['reference']['file_sha256']:raise SystemExit('CHMI reference hash mismatch')
    if ref.get('loucka_snapshot_id')!=actual:raise SystemExit('External validation is stale against concordance snapshot')
    # Recompute comparator analysis before any decisions consume it.
    stages.append(run('chmi-reference-cache-integrity',Path('scripts/validate_chmi_candidate_reference_cache.py')))
    stages.append(run('chmi-priority-temperature-cache-integrity',Path('scripts/validate_chmi_priority_temperature_cache.py')))
    stages.append(run('chmi-pressure-reference-cache-integrity',Path('scripts/validate_chmi_pressure_candidate_reference_cache.py')))
    stages.append(run('reference-data-catalog',Path('scripts/build_reference_data_catalog.py')))
    stages.append(run('reference-station-catalog',Path('scripts/build_reference_station_catalog.py')))
    stages.append(run('temperature-reference-availability',Path('scripts/build_temperature_reference_availability.py')))
    stages.append(run('chmi-daily-temperature-context',Path('scripts/validate_chmi_daily_temperature_context.py')))
    stages.append(run('external-reference-validation',Path('scripts/validate_pilot_chmi_reference.py')))
    stages.append(run('publication-pilot-and-candidate-selection',Path('scripts/build_publication_pilot_v2.py')))
    stages.append(run('monthly-temperature-reference-validation',Path('scripts/validate_temperature_monthly_references.py')))
    stages.append(run('temperature-candidate-expert-review',Path('scripts/build_temperature_candidate_expert_review.py')))
    stages.append(run('monthly-humidity-reference-validation',Path('scripts/validate_humidity_monthly_references.py')))
    stages.append(run('chmi-daily-humidity-cache-integrity',Path('scripts/validate_chmi_daily_humidity_cache.py')))
    stages.append(run('humidity-daily-regional-context',Path('scripts/build_humidity_daily_context_review.py')))
    stages.append(run('humidity-validation-report',Path('scripts/build_humidity_sensor_validation_report.py')))
    stages.append(run('monthly-pressure-reference-validation',Path('scripts/validate_pressure_monthly_reference.py')))
    stages.append(run('chmi-daily-pressure-cache-integrity',Path('scripts/validate_chmi_daily_pressure_cache.py')))
    stages.append(run('pressure-daily-regional-context',Path('scripts/build_pressure_daily_reference_context.py')))
    stages.append(run('monthly-wind-reference-validation',Path('scripts/validate_wind_monthly_references.py')))
    stages.append(run('wind-validation-report',Path('scripts/build_wind_monthly_validation_report.py')))
    stages.append(run('temperature-validation-report',Path('scripts/build_temperature_monthly_validation_report.py')))
    stages.append(run('interval-coverage-review',Path('scripts/build_interval_coverage_review.py')))
    stages.append(run('interval-adjusted-diagnostic-means',Path('scripts/build_interval_adjusted_candidate_means.py')))
    stages.append(run('interval-time-method-report',Path('scripts/build_interval_time_method_report.py')))
    stages.append(run('historical-conflict-epoch-review',Path('scripts/build_historical_conflict_epoch_review.py')))
    stages.append(run('three-unmatched-temperature-case-review',Path('scripts/build_three_unmatched_temperature_review.py')))
    stages.append(run('monthly-candidate-series-diagnostics',Path('scripts/build_monthly_candidate_series_diagnostics.py')))
    stages.append(run('pressure-candidate-semantics-review',Path('scripts/build_pressure_candidate_semantics_review.py')))
    stages.append(run('pressure-semantics-validation-report',Path('scripts/build_pressure_semantics_validation_report.py')))
    stages.append(run('humidity-candidate-series-review',Path('scripts/build_humidity_monthly_series_review.py')))
    stages.append(run('humidity-candidate-specific-validation-review',Path('scripts/build_humidity_candidate_validation_review.py')))
    stages.append(run('candidate-evidence-records',Path('scripts/build_monthly_validation_evidence.py')))
    stages.append(run('local-station-metadata-source-search',Path('scripts/audit_local_station_metadata_sources.py')))
    stages.append(run('epoch-registry-and-monthly-results',Path('scripts/build_epoch_registry_and_monthly_results.py')))
    stages.append(run('current-gw3000-e4-review',Path('scripts/build_current_gw3000_e4_report.py')))
    stages.append(run('readiness-decisions',Path('scripts/build_publication_readiness_matrix.py')))
    stages.append(run('v3-policy-decisions',Path('scripts/build_publication_v3.py')))
    # Earlier candidate/evidence phases finish after the initial V2 build.
    # Refresh the V2 exports once their final inputs are available.
    stages.append(run('final-v2-decision-export-refresh',Path('scripts/build_publication_pilot_v2.py')))
    stages.append(run('atlas-contract',Path('scripts/build_atlas_statistics_contract.py')))
    stages.append(run('priority-candidate-outcomes',Path('scripts/build_automated_validation_candidate_outcomes.py')))
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')
    subprocess.run([sys.executable,'-m','unittest','tests.test_atlas_statistics_contract','tests.test_time_bounds','tests.test_interval_period_stats','tests.test_publication_pilot_v2','tests.test_provenance_counts','tests.test_statistical_variants','tests.test_readiness_snapshot_adapter','tests.test_temperature_reference_validation','tests.test_publication_v3_exports','tests.test_historical_conflict_epoch_review','tests.test_current_gw3000_e4','tests.test_epoch_registry_and_monthly_results','tests.test_three_unmatched_temperature_review','tests.test_humidity_reference_validation','tests.test_pressure_reference_validation','tests.test_wind_reference_validation','tests.test_automated_candidate_outcomes','tests.test_atlas_preview_http','tests.test_interval_weighted_variants','-q'],cwd=ROOT,env=env,check=True)
    stages.append({'stage':'focused-contract-and-classifier-tests','status':'PASS'})
    report={'schema':'loucka-automated-validation-run-v1','run_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'snapshot_id':actual,'snapshot_rows':manifest['source_row_count'],'reference_sha256':sha(ref_file),'publication_authorized':False,'database_write_performed':False,'deployment_performed':False,'stages':stages,'scope_limit':'Implements existing pilot, monthly candidate evidence, interval diagnostics, readiness matrix, and atlas pilot contract. Does not claim completion of all 248 expert validations, all requested phases, or full E2E source regeneration.'}
    (ROOT/'AUTOMATED_VALIDATION_RUN.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    # Finalize the post-run proof and user-facing package from the just-written
    # run manifest. These delivery stages are kept in a separate manifest to
    # avoid a circular hash between the report, run manifest and ZIP bundle.
    delivery_stages=[]
    for label,script in [
        ('monthly-evidence-replay',Path('scripts/verify_monthly_evidence_replay.py')),
        ('post-run-invariants-and-regression-suite',Path('scripts/validate_automated_validation_postrun.py')),
        ('automated-validation-report',Path('scripts/build_automated_validation_report.py')),
        ('automated-validation-progress',Path('scripts/build_automated_validation_progress.py')),
        ('automated-validation-bundle',Path('scripts/build_automated_validation_bundle.py')),
        ('final-report-bundle-validation',Path('scripts/validate_final_report_bundle.py')),
    ]:
        delivery_stages.append(run(label,script))
    delivery={'schema':'loucka-automated-validation-delivery-run-v1','run_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'snapshot_id':actual,'core_run_manifest_sha256':sha(ROOT/'AUTOMATED_VALIDATION_RUN.json'),'delivery_stages':delivery_stages,'bundle_sha256':sha(ROOT/'loucka_automated_validation_completion_v1.zip'),'publication_authorized':False,'historical_database_writes':False,'deployment_performed':False}
    (ROOT/'AUTOMATED_VALIDATION_DELIVERY_RUN.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'stages_passed':len(stages),'delivery_stages_passed':len(delivery_stages),'snapshot_id':actual,'bundle_sha256':delivery['bundle_sha256'],'publication_authorized':False},indent=2))
if __name__=='__main__':main()
