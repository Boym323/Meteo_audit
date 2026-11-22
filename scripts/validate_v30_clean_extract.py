#!/usr/bin/env python3
"""Clean-extract v30, verify manifest and run active package validators/simulators."""
import hashlib,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ARCHIVE=ROOT/'loucka_historical_audit_and_priority_corrections_v30.zip'
with zipfile.ZipFile(ARCHIVE) as z:
 names=set(z.namelist());m=json.loads(z.read('MANIFEST.json'));assert m['main_report_count']==18
 assert len(m['contents'])==m['file_count_excluding_manifest']
 assert m['active_correction_operation_count']==65 and m['active_restored_operations']==44 and m['active_estimated_operations']==21
 assert m['active_unique_timestamps']==56 and m['active_physical_rows_if_applied']==52 and m['active_update_operations']==13
 assert m['database_writes']==0 and m['actual_weather_mcp_dry_run'] is False and m['applied_operations']==0
 inventory=json.loads(z.read('reports/required-report-inventory.json'));assert inventory['required_report_count']==18
 assert all('reports/'+x['report'] in names for x in inventory['reports'])
 for item in m['contents']:
  b=z.read(item['path']);assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],item['path']
 reg=json.loads(z.read('config/active_proposal_registry.json'))
 assert reg['active_operation_count']==65 and len([x for x in reg['packages'] if x['status']=='ACTIVE'])==7
 mid=json.loads(z.read('proposals/restored_rh_2014_midpoint_pilot/source_evidence.json'))
 assert [x['timestamp'] for x in mid['bounded_alternative_screen']]==[1401534900,1401535800,1401545400,1401551400]
 assert all(x['disposition']=='REVIEW_REQUIRED' for x in mid['bounded_alternative_screen'])
 assert reg['packages'][0]['local_validation']['command']=='python3 proposals/estimated_short_temperature_gaps_v2/validate.py'
 assert next(x for x in reg['packages'] if x['package_id']=='restored-source-only-2013-july-pilot')['local_validation']['command']=='python3 proposals/restored_source_only_2013_july_pilot/validate.py'
 assert 'loucka_historical_audit_and_priority_corrections_v23.zip' not in names
 assert 'data/source_only_outtemp_2016_2017_exact_grid_screen.json' in names
 assert 'data/source_only_outtemp_zero_run_screen_2016_2017.json' in names
 assert 'data/source_only_outtemp_zero_run_field_variation_2016_2017.json' in names
 assert 'data/source_only_2016_sep19_zero_episode_context.json' in names
 assert 'data/source_only_target_row_availability_2016_2017.json' in names
 assert 'data/rh_p2_2015_exact_bracket_review.json' in names
 run_data=json.loads(z.read('data/source_only_outtemp_zero_run_screen_2016_2017.json')); assert run_data['query_execution_timestamp']=='NOT_CAPTURED_BY_WEATHER_MCP' and run_data['recorded_in_checkpoint_utc']==m['snapshot_created_utc']
 assert 'sql/readonly/source_only_outtemp_2016_2017_exact_grid_screen.sql' in names
 assert 'loucka_historical_audit_and_priority_corrections_v21.zip' not in names
 assert 'reports/2026-11-13-C3-restored-temperature-source-gate-closure.md' in names
 assert 'reports/2026-11-13-D4-humidity-epoch-and-winter-transfer-closeout.md' in names
 assert 'reports/2026-11-13-B5-selected-source-cohort-gap-overlap.md' in names
 assert 'data/b5_gap_reviewed_source_cohort_overlay.json' in names
 assert 'reports/2026-11-13-b5-gap-reviewed-source-overlap-row-evidence.csv' in names
 assert 'reports/2026-11-13-F5-secondary-restoration-eligibility-closeout.md' in names
 assert 'data/f4_migration_concordance_2019_primary_fields.json' in names
 assert 'sql/readonly/f4_migration_concordance_2020_primary_fields.sql' in names
 assert 'reports/2026-11-13-F4-primary-field-concordance-2009-2020.md' in names
 assert 'data/f4_migration_concordance_2009_primary_fields.json' in names
 assert 'data/f4_migration_concordance_2013_primary_fields.json' in names
 assert 'data/f4_migration_concordance_2015_primary_fields.json' in names
 assert 'scripts/build_f4_field_provenance_matrix.py' in names
 assert 'scripts/validate_f4_field_provenance_matrix.py' in names
 assert 'data/f4_migration_concordance_2014.json' in names
 assert 'data/f4_migration_concordance_2015_primary_fields.json' in names
 assert 'reports/2026-11-13-F4-2014-shared-field-concordance.md' in names
 assert 'reports/2026-11-13-F4-2015-primary-concordance.md' in names
 assert 'proposals/estimated_short_temperature_gaps_v2/simulate_v2_1.py' in names
 assert 'proposals/restored_source_only_2020_isolated_outtemp/per_target_archive_presence.csv' in names
 assert 'proposals/restored_rh_2014_boundary_pilot/validate.py' in names
 assert 'proposals/restored_rh_2014_midpoint_pilot/validate.py' in names
 assert 'proposals/restored_rh_2014_midpoint_pilot/source_evidence.sql' in names
 assert 'reports/2026-11-13-rh-p2-2014-midpoint-pilot.md' in names
 assert 'proposals/restored_rh_2014_midpoint_pilot/excluded_cases.csv' in names
 assert 'proposals/restored_rh_2014_midpoint_pilot/source_evidence.json' in names
 assert 'reports/2026-11-13-rh-p2-2016-two-candidate-review.md' in names
 assert 'reports/2026-11-13-rh-p2-2018-exact-bracket-review.md' in names
 assert 'reports/2026-11-13-rh-p2-2019-exact-bracket-review.md' in names
 assert 'reports/2026-11-13-rh-p2-2017-exact-bracket-review.md' in names
 assert 'reports/2026-11-13-rh-p2-2017-regional-conflict-review.md' in names
 assert 'reports/2026-11-13-stage-e-closure-review.md' in names
 assert 'reports/2026-11-13-H3-truth-validation-closure.md' in names
 assert 'reports/2026-11-13-H4-uncertainty-contract-review.md' in names
 assert 'data/rh_p2_2017_regional_conflict_review.json' in names
 assert 'data/h3_truth_scope_closure.json' in names
 assert 'data/h4_active_p3_uncertainty_contract.json' in names
 assert 'data/h4_active_p3_uncertainty_by_duration.csv' in names
 assert 'proposals/estimated_short_temperature_gaps_v2/simulate_v2_1.py' in names
 assert 'loucka_historical_audit_and_priority_corrections_v11.zip' not in names
 assert 'loucka_historical_audit_and_priority_corrections_v12.zip' not in names
 progress=json.loads(z.read('PROGRESS.json'))
 assert progress['overall']['verified_subtasks']==136 and progress['overall']['defined_subtasks']==142
 stage_c=next(x for x in progress['stages'] if x['id']=='C')
 assert stage_c['status']=='COMPLETED_WITH_LIMITATIONS'
 assert next(t for t in stage_c['subtasks'] if t['id']=='C3')['status']=='COMPLETED_WITH_LIMITATIONS'
 stage_f=next(x for x in progress['stages'] if x['id']=='F')
 assert stage_f['status']=='COMPLETED_WITH_LIMITATIONS' and stage_f['analyzed_records']['migration_concordance_selected_2009_2020_exact_timestamp_pairs']==902066
 stage_f=next(x for x in progress['stages'] if x['id']=='F')
 assert stage_f['status']=='COMPLETED_WITH_LIMITATIONS' and stage_f['analyzed_records']['migration_concordance_2014_exact_timestamp_pairs']==97228
 assert stage_f['analyzed_records']['migration_concordance_2015_exact_timestamp_pairs']==104063
 assert progress['as_of_utc']==m['snapshot_created_utc']
 stage_e=next(x for x in progress['stages'] if x['id']=='E')
 assert stage_e['status']=='BLOCKED'
 assert next(t for t in stage_e['subtasks'] if t['id']=='E5')['status']=='COMPLETED_WITH_LIMITATIONS'
 d5=next(t for t in next(x for x in progress['stages'] if x['id']=='D')['subtasks'] if t['id']=='D5')
 assert d5['additional_review_checkpoint_2017_regional']['new_unique_targets']==16
 stage_f=next(x for x in progress['stages'] if x['id']=='F')
 assert 'reports/2026-11-13-F4-historical-lineage-review-closeout.md' in names
 stage_g=next(x for x in progress['stages'] if x['id']=='G')
 assert stage_f['status']=='COMPLETED_WITH_LIMITATIONS'
 assert next(t for t in stage_f['subtasks'] if t['id']=='F4')['status']=='COMPLETED_WITH_LIMITATIONS'
 assert progress['overall']['verified_subtasks']==136
 assert stage_g['status']=='COMPLETED_WITH_LIMITATIONS'
 assert next(t for t in stage_g['subtasks'] if t['id']=='G4')['status']=='COMPLETED_WITH_LIMITATIONS'
 stage_h=next(x for x in progress['stages'] if x['id']=='H')
 assert next(t for t in stage_h['subtasks'] if t['id']=='H3')['status']=='COMPLETED_WITH_LIMITATIONS'
 assert next(t for t in stage_h['subtasks'] if t['id']=='H4')['status']=='COMPLETED_WITH_LIMITATIONS'
 assert next(t for t in stage_h['subtasks'] if t['id']=='H5')['status']=='COMPLETED_WITH_LIMITATIONS'
with tempfile.TemporaryDirectory(prefix='loucka-v30-clean-') as td:
 with zipfile.ZipFile(ARCHIVE) as z:z.extractall(td)
 base=Path(td)
 commands=[
  ['scripts/validate_rh_p2_2015_exact_bracket_review.py'],['scripts/validate_source_only_target_row_availability_2016_2017.py'],['scripts/validate_source_only_2016_sep19_zero_episode_context.py'],['scripts/validate_source_only_outtemp_zero_run_field_variation_2016_2017.py'],['scripts/validate_source_only_outtemp_zero_run_screen_2016_2017.py'],['scripts/validate_source_only_outtemp_2016_2017_exact_grid_screen.py'],['scripts/validate_b5_gap_source_cohort_overlay.py'],['scripts/validate_rh_winter_reference_validation.py'],['scripts/validate_chmi_rh_winter_validation.py'],['scripts/validate_rh_luhamet_source_availability_2022.py'],['scripts/validate_annual_secondary_cross_archive_2024_2026.py'],['scripts/validate_extra_temperature_cross_archive.py'],['scripts/validate_soil_temperature_extremes_2026.py'],['scripts/validate_secondary_channel_followup.py'],['scripts/validate_lightning_field_semantics_2026.py'],['scripts/validate_f4_primary_concordance.py'],['scripts/validate_f4_field_provenance_matrix.py'],['scripts/validate_active_proposal_deduplication.py'],['scripts/validate_source_first_active_proposals.py'],['scripts/validate_rh_p2_2017_exact_bracket_review.py'],['scripts/validate_rh_p2_2016_two_candidate_review.py'],['scripts/validate_rh_p2_2018_exact_bracket_review.py'],['scripts/validate_rh_p2_2019_exact_bracket_review.py'],['scripts/build_active_derived_impact.py'],['scripts/validate_active_derived_impact.py'],['scripts/validate_expert_review_register.py'],['scripts/validate_rh_cross_year_bracketed_summary.py'],
  ['scripts/build_expert_review_register.py'],['scripts/enrich_expert_review_register.py'],['scripts/validate_expert_review_register.py'],
  ['scripts/build_rh_p2_2017_regional_conflict_review.py'],['scripts/validate_rh_p2_2017_regional_conflict_review.py'],
  ['scripts/validate_h3_truth_scope_closure.py'],['scripts/build_h4_uncertainty_contract.py'],['scripts/validate_h4_uncertainty_contract.py'],
  ['scripts/validate_rain_physical_range_screen.py'],['scripts/validate_rain_null_exact_source_coverage.py'],['scripts/validate_rain_phaseA_history_reconciliation.py'],['scripts/validate_rain_2013_counter_epoch.py'],['scripts/validate_rain_2013_reset_aware_counter.py'],['scripts/validate_rainrate_interval_ratio.py'],['scripts/validate_rain_audit_bundle.py'],
  ['proposals/estimated_short_temperature_gaps_v2/simulate_v2_1.py','--output','proposals/estimated_short_temperature_gaps_v2/offline_simulation_v2_1.json'],
  ['proposals/estimated_short_temperature_gaps_v2/validate.py'],['proposals/restored_source_only_2013_july_pilot/validate.py'],
  ['scripts/validate_2018_dec31_restored_update_pilot.py'],['proposals/restored_source_only_2019_may30_outtemp/validate.py'],
  ['proposals/restored_source_only_2020_isolated_outtemp/validate.py'],['proposals/restored_rh_2014_boundary_pilot/simulate.py'],['proposals/restored_rh_2014_boundary_pilot/validate.py'],['proposals/restored_rh_2014_midpoint_pilot/simulate.py'],['proposals/restored_rh_2014_midpoint_pilot/validate.py'],['proposals/restored_source_only_rows_v2/validate.py'],
  ['scripts/validate_final_report_bundle.py'],['scripts/compute_era5_candidate_grid.py'],['scripts/build_h5_same_holdout_multistation_comparison.py'],['scripts/validate_h5_same_holdout_multistation_comparison.py'],['proposals/restored_source_only_2013_july_pilot/simulate.py'],
  ['proposals/restored_source_only_2019_may30_outtemp/simulate.py'],['proposals/restored_source_only_2020_isolated_outtemp/simulate.py']]
 results=[]
 for cmd in commands:
  proc=subprocess.run([sys.executable,*cmd],cwd=base,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  results.append({'command':'python3 '+' '.join(cmd),'returncode':proc.returncode,'output':proc.stdout[-1800:]})
  if proc.returncode:print(json.dumps({'status':'FAIL','failed':results[-1]},indent=2));raise SystemExit(proc.returncode)
 for cmd in [['proposals/restored_source_only_2013_july_pilot/validate.py'],['proposals/restored_source_only_2019_may30_outtemp/validate.py'],['proposals/restored_source_only_2020_isolated_outtemp/validate.py'],['proposals/restored_rh_2014_midpoint_pilot/validate.py']]:
  proc=subprocess.run([sys.executable,*cmd],cwd=base,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);results.append({'command':'python3 '+' '.join(cmd)+' post-simulation','returncode':proc.returncode,'output':proc.stdout[-900:]})
  if proc.returncode:print(json.dumps({'status':'FAIL','failed':results[-1]},indent=2));raise SystemExit(proc.returncode)
out={'status':'PASS','archive':ARCHIVE.name,'members':len(names),'manifest_files_verified':len(m['contents']),'clean_extraction':True,'active_packages':7,'active_operations':65,'restored':44,'estimated':21,'unique_timestamps':56,'physical_inserts':52,'updates':13,'commands':results,'database_access':'NONE','mcp_dry_run':'NOT_RUN','staging':False,'application':False}
# Detached result is intentionally not part of the ZIP to avoid a self-referential hash cycle.
(ROOT/'reports/2026-11-13-v30-clean-extract-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='commands'},indent=2))
