#!/usr/bin/env python3
"""Generate STATUS.md A–O matrix and PROGRESS.json from explicit evidence checklists."""
from __future__ import annotations
import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

STAGES=[
 {'id':'A','title':'Inventář databází a zdrojů','tasks':[
  ('A1','Databáze/schémata/archive tables napříč 6 dostupnými archivy','COMPLETED'),
  ('A2','COLUMNS/STATISTICS metadata všech 102 tabulek; 1 410 sloupců a 113 indexů','COMPLETED'),
  ('A3','Přesné archive rows, epoch rozsahy a usUnits pro 6 archivů','COMPLETED'),
  ('A4','Úplné exact row/time/null/history stavy všech relevantních auxiliary tabulek','IN_PROGRESS'),
  ('A5','Plná source lineage, duplicity a per-variable dostupnost napříč epochami','IN_PROGRESS')],
  'records':{'database_schemas':6,'tables':102,'column_definitions':1410,'index_definitions':120,'distinct_indexes':113,'reconstruction_archive_rows':1689890,'archive_row_counts_by_database':{'loucka_reconstruction':1689890,'old_weewx':1104422,'weewx_WH1080':1112201,'pocasi-loucka.eu':1683913,'pocasi-loucka.eu_GW1000':1674765,'pocasi-loucka.eu_old':1336195}},
  'outputs':['reports/DATABASE_INVENTORY.md','reports/2026-11-13-database-schema-metadata.md','reports/2026-11-13-database-columns.csv','reports/2026-11-13-database-index-columns.csv','sql/readonly/database_schema_metadata.sql','reports/2026-11-13-historical-weewx-lineage-search.md','reports/2026-11-13-public-station-history-lineage.md','data/source-lineage/public_station_history_20261113.json'],
  'blockers':['Úplná proměnná/jednotková/epochová provenience a exact audit všech pomocných tabulek nejsou hotové.'],
  'effort':[3,8],'dependencies':[]},
 {'id':'B','title':'Časová kontinuita, intervaly a mezery','tasks':[
  ('B1','Timezone/DST a Unix epoch interpretace v dostupných archivech','COMPLETED'),
  ('B2','Roční cadence/interval screening pro celé období 2009–2026','COMPLETED'),
  ('B3','Gap pair/event katalog a reconciliace ročních součtů','COMPLETED'),
  ('B4','Historické expected-slot denominator a station-operational epochs','IN_PROGRESS'),
  ('B5','Příčina/zdrojový stav a řešitelnost každé mezery','IN_PROGRESS')],
  'records':{'reconstruction_archive_rows':1689890,'adjacent_pairs':1689889,'gap_candidate_pairs':24523,'gaps_ge_24h':44},
  'outputs':['reports/TIME_CONTINUITY_AUDIT.md','reports/2026-11-12-gap-event-catalog.csv','reports/2026-11-12-gap-event-catalog.md','reports/2026-11-12-interval-aware-gap-screening.csv','reports/2026-11-12-interval-aware-gap-annual-summary.csv'],
  'blockers':['Provozní epochy a očekávaná cadence nejsou ve všech historických obdobích doloženy; příčiny gapů vyžadují source/config evidence.'],
  'effort':[4,10],'dependencies':['A','C','D','F']},
 {'id':'C','title':'Venkovní teplota a P1/P3 návrhy','tasks':[
  ('C1','Teplotní rozsah/epizody a významné anomálie ve vybraných prioritních obdobích','COMPLETED'),
  ('C2','Inventář 8 965 společných source-copy NULL kandidátů 2009–2020','COMPLETED'),
  ('C3','Row-level provenance/unit/history/neighbors/sensor-epoch gate pro RESTORED P1','IN_PROGRESS'),
  ('C4','Rozhodovací pravidla a konzervativní P3 návrhy výpadků do 1 h v holdout-validovaném rozsahu','COMPLETED'),
  ('C5','Chronologické transfer a seasonal masked-block validace z dřívějších běhů','COMPLETED'),
  ('C6','Zimní mráz/inverze/long-gap truth a nejistota pro neznámé bloky','IN_PROGRESS'),
  ('C7','Independent review source-first pro všech 107 P3 targetů; 24 ESTIMATED/83 REVIEW_REQUIRED balíček v2','COMPLETED')],
  'records':{'source_copy_null_candidates':8965,'P3_source_archives_checked':6,'P3_exact_target_timestamps_reviewed':107,'P3_source_temperature_rows':83,'P3_source_free_estimated_targets':24,'P3_restored':0,'P3_review_required':83,'source_only_union_timestamps_2009_2020':207182,'OLS_train_exact_pairs_2015_2017':235135,'holdout_exact_pairs_2019_2020':192235,'seasonal_masked_complete_blocks':19714,'masked_24h_intervals':571,'P3_real_gap_episodes_selected_2019_2020':56,'P3_v1_superseded_estimated_timestamps':107},
  'outputs':['reports/TEMPERATURE_AUDIT.md','reports/2026-11-12-outtemp-source-copy-screening.md','reports/2026-11-12-outtemp-source-copy-annual.csv','reports/2026-11-13-temperature-transfer-2019-2020-holdout.md','reports/2026-11-13-temperature-interpolation-seasonal-blocks.md','proposals/estimated_short_temperature_gaps/corrections.json','proposals/estimated_short_temperature_gaps/corrections.csv','proposals/estimated_short_temperature_gaps/manifest.json','proposals/estimated_short_temperature_gaps/selection_metadata.json','proposals/estimated_short_temperature_gaps/source_snapshot.json','reports/2026-11-13-estimated-short-temperature-gap-proposals.md','reports/2026-11-13-p1-temperature-year-source-epoch-classification.md','proposals/restored_temperature/year_source_epoch_quality.csv','reports/P3_INDEPENDENT_REVIEW.md','proposals/estimated_short_temperature_gaps_v2/manifest.json','proposals/restored_source_only_rows_v2/manifest.json'],
  'blockers':['Legacy archive lineage/driver epoch and target unit transform are not proven per candidate; long winter/inversion truth is absent.'],
  'effort':[12,30],'dependencies':['A','B','G','H','I','K','L','M']},
 {'id':'D','title':'Relativní vlhkost a P2/P4 návrhy','tasks':[
  ('D1','RH source-pair inventory 30 391; šest velkých 2019 konfliktů odděleno','COMPLETED'),
  ('D2','Exact LuhaMet RH availability/model diagnostics a 2015–2017 holdout','COMPLETED'),
  ('D3','2022 RH monthly/daily gap and history triage (ER-31)','COMPLETED'),
  ('D4','Historical sensor/config/unit stability; winter/fog/inversion transfer truth','IN_PROGRESS'),
  ('D5','P2 source-specific RESTORED package excluding six conflicts and stale/applied rows','IN_PROGRESS'),
  ('D6','P4 2022 winter model validated on independent comparable winter periods','IN_PROGRESS'),
  ('D7','Exact-time local winter RH/reference validation 2018/19–2019/20 with sensor-epoch comparison','COMPLETED')],
  'records':{'old_archive_RH_pairs':30391,'known_RH_conflicts_2019':6,'2022_archive_rows':104142,'2022_RH_null_rows':41727,'2022_zero_RH_days':112,'2022_Feb_exact_LuhaMet_RH_values':8057,'2022_Feb_target_rows':8058,'RH_winter_local_reference_pairs_2018_19':5563,'RH_winter_local_reference_pairs_2019_20':24295,'RH_winter_exact_source_copy_matches_Q1_2019':12564,'RH_winter_transfer_epoch_shift_indicated':True,'RH_source_pair_year_cohorts':11,'RH_source_interval6_exception_rows':4},
  'outputs':['reports/HUMIDITY_AUDIT.md','reports/2026-11-12-rh-source-conflicts.md','reports/2026-11-13-rh-luhamet-exact-source-availability-2015-2017.md','reports/2026-11-13-rh-luhamet-outage-2022-source-coverage.md','reports/2026-11-13-rh-vapor-pressure-transfer-holdout.md','reports/2026-11-13-rh-winter-reference-validation.md','reports/2026-11-13-rh-winter-local-validation.csv','reports/2026-11-13-rh-winter-monthly-validation.csv','reports/2026-11-13-rh-winter-source-concordance-q1-2019.csv','sql/readonly/rh_winter_local_reference_validation_2018_2020.sql','scripts/validate_rh_winter_reference_validation.py','reports/2026-11-13-rh-source-pair-year-epoch-triage.md','reports/2026-11-13-rh-source-pair-year-epoch-triage.csv','reports/2026-11-13-rh-source-pair-interval6-cases.csv','sql/readonly/rh_source_pair_year_epoch_triage.sql','sql/readonly/rh_source_pair_interval6_cases.sql','scripts/validate_rh_source_pair_year_epoch_triage.py'],
  'blockers':['LuhaMet coordinates/licensing/sensor history remain missing; winters 2018/19 vs 2019/20 show a large transfer regime shift; no independent 2022 winter local truth.'],
  'effort':[8,20],'dependencies':['A','B','G','H','I','J','K','L','M']},
 {'id':'E','title':'Srážky/rainRate','tasks':[
  ('E1','Fyzikální range and annual archive coverage screen','COMPLETED'),
  ('E2','Phase A backup/history and selected latest-event reconciliation','COMPLETED'),
  ('E3','Selected exact-source NULL and counter epoch/reset candidate audits','COMPLETED'),
  ('E4','Complete local gauge/counter/driver semantics and interval-source truth','IN_PROGRESS'),
  ('E5','Safe per-row rain/rate source-recovery candidates/packages','IN_PROGRESS')],
  'records':{'archive_rows_screened':1586426,'years_screened_excluding_2021':17,'exact_source_null_rain_targets_2009_2020':11780,'phase_a_history_targets':360,'protected_2021_history_targets':1497},
  'outputs':['reports/RAIN_AUDIT.md','reports/2026-11-13-rain-physical-range-screen.md','reports/2026-11-13-rain-null-exact-source-coverage.md','reports/2026-11-13-rain-phaseA-history-reconciliation.md','reports/2026-11-13-rain-2013-reset-aware-counter.md'],
  'blockers':['Rain counter semantics/driver epochs and independent local gauge truth not established.'],
  'effort':[8,20],'dependencies':['A','B','G','I','K','L','M']},
 {'id':'F','title':'Další senzory a P5 návrhy','tasks':[
  ('F1','Roční i měsíční NULL availability pro 77 numeric fields (2009–2026)','COMPLETED'),
  ('F2','Přesná concordance 42 polí production/reconstruction v 2024–2026','COMPLETED'),
  ('F3','Focused lightning/soil/extra-temperature anomaly evidence and review register','COMPLETED'),
  ('F4','Historická fyzická identita/jednotky/driver epochy všech relevantních polí','IN_PROGRESS'),
  ('F5','P5 source-specific RESTORED package only for lineage-proven measurements','IN_PROGRESS'),
  ('F6','Source-only multi-variable availability across 52 common numeric columns for 2009–2020','COMPLETED')],
  'records':{'numeric_fields':77,'year_field_cells':1386,'month_field_cells':16632,'secondary_exact_source_fields':42,'secondary_exact_source_rows_2024_2026':304758,'source_only_union_timestamps_2009_2020':207182,'common_source_only_numeric_columns':52,'soil_temperature_extreme_rows_reviewed':32,'extraTemp2_high_rows_reviewed':790},
  'outputs':['reports/SECONDARY_SENSORS_AUDIT.md','reports/2026-11-13-monthly-archive-field-availability-2009-2026.csv','reports/2026-11-13-secondary-exact-cross-archive-2024-2026.md','reports/2026-11-13-lightning-field-cross-archive.md','reports/2026-11-13-soil-temperature-extremes-2026.md','data/p3_independent_review/source_only_common_numeric_fields_2009_2020.json','reports/2026-11-13-source-only-field-availability-2009-2020.csv','sql/readonly/source_only_common_numeric_fields_2009_2020.sql','runs/20261113T084454Z-922430ad/manifest.json'],
  'blockers':['Shared archive copies establish provenance concordance, not physical correctness; hardware/config lineages missing for many fields.'],
  'effort':[6,16],'dependencies':['A','B','G','K','L','M','O']},
 {'id':'G','title':'Reference data and source representativeness','tasks':[
  ('G1','Reference source/station registry and cache inventory','COMPLETED'),
  ('G2','CHMI cache/data metadata and hashes verified for available snapshots','COMPLETED'),
  ('G3','Loučka coordinates, source licenses, historical sensor continuity and matching policy','IN_PROGRESS'),
  ('G4','ERA5/ERA5-Land station/grid pairing and independent local weather reference','IN_PROGRESS')],
  'records':{'LuhaMet_observations':1157794,'unique_CHMI_cache_files_hashed':34,'reference_station_registry_rows':2},
  'outputs':['reports/REFERENCE_DATA_INVENTORY.md','data/reference-inventory/reference_stations_snapshot_20261113.json','data/reference-inventory/reference_source_catalog.json','reports/2026-11-13-reference-cache-manifest-summary.csv'],
  'blockers':['Loučka sensor coordinates unavailable; LuhaMet license/coordinates/continuity incomplete; ERA5 data catalogued but not downloaded.'],
  'effort':[5,12],'dependencies':['A','C','D','E','H']},
 {'id':'H','title':'Model validation and uncertainty','tasks':[
  ('H1','Chronological complete-case transfer models on existing holdouts','COMPLETED'),
  ('H2','Short-gap 1/6/24h seasonal masked-block validation','COMPLETED'),
  ('H3','Independent truth tests for actual missing windows, winter/freeze/inversion regimes','IN_PROGRESS'),
  ('H4','Prediction intervals/uncertainty calibration and model-specific release thresholds','IN_PROGRESS'),
  ('H5','Reanalysis model and multi-station comparison on same blind holdouts','IN_PROGRESS')],
  'records':{'temp_train_pairs':235135,'temp_holdout_pairs':192235,'temperature_masked_blocks':19714,'temperature_masked_24h_blocks':571,'RH_reference_pairs_2015_2017':38582},
  'outputs':['reports/MODEL_VALIDATION_REPORT.md','reports/2026-11-13-temperature-luhamet-harmonic-ols-block-validation.md','reports/2026-11-13-temperature-interpolation-seasonal-blocks.md','reports/2026-11-13-rh-vapor-pressure-transfer-holdout.md','reports/2026-11-13-rh-luhamet-blocked-transfer-holdout.md'],
  'blockers':['No local truth labels for long missing blocks; sparse station metadata; no calibrated predictive intervals.'],
  'effort':[10,22],'dependencies':['C','D','G']},
 {'id':'I','title':'Correction/change history and protected state','tasks':[
  ('I1','Latest applied event reconciliation for selected core variables','COMPLETED'),
  ('I2','Applied/pending/reverted/cancelled batch and proposal inventory','COMPLETED'),
  ('I3','Selected source-only/null target history cross-checks','COMPLETED'),
  ('I4','Complete per-row source/history reconciliation for all proposed candidates','IN_PROGRESS'),
  ('I5','Q1 2018 live-draft and 2021 diagnostic-only protections preserved','COMPLETED')],
  'records':{'core_variable_latest_events_reconciled':86256,'applied_RH_history_events':20712,'proposal_inventory_targets':272,'pending_batch_scope':20},
  'outputs':['reports/RECONSTRUCTION_HISTORY_AUDIT.md','reports/2026-11-13-proposal-inventory.csv','reports/2026-11-12-pending-candidate-reconciliation.md','reports/2026-11-12-latest-event-reconciliation.md'],
  'blockers':['Candidate source and event lineage is not yet reconciled row-by-row for prospective packages.'],
  'effort':[3,8],'dependencies':['A','C','D','E','L']},
 {'id':'J','title':'Derived variables and dependency cascade','tasks':[
  ('J1','Schema map of 21 GOAL derived variables across six archives','COMPLETED'),
  ('J2','Observed RH/outTemp downstream cascade diagnostics','COMPLETED'),
  ('J3','Historical formula, WeeWX package/config/producer provenance','IN_PROGRESS'),
  ('J4','Dependency-aware stale/rebuild proposal with recalculation order','IN_PROGRESS')],
  'records':{'derived_variables_mapped':21,'history_RH_targets':20712,'observed_dependency_groups':'multiple bounded periods; no DB recalculation'},
  'outputs':['reports/DERIVED_VARIABLE_AUDIT.md','reports/2026-11-13-derived-variable-schema-map.csv','reports/2026-11-13-derived-rh-cascade-all-history.md','reports/2026-11-13-derived-outtemp-cascade.md'],
  'blockers':['Historical WeeWX configuration/formula producer unavailable; exact derived values cannot be approved.'],
  'effort':[4,10],'dependencies':['A','D','I','K','O']},
 {'id':'K','title':'Quality and provenance classification','tasks':[
  ('K1','Origin/review axis and sidecar schema proposed','COMPLETED'),
  ('K2','32 issue-group expert review register plus one follow-up built and validated','COMPLETED'),
  ('K3','Per-record historical quality labels and source lineage','IN_PROGRESS'),
  ('K4','Map each expert issue to specific corrections/publication effects','IN_PROGRESS'),
  ('K5','P3 ER-32 scoped to 83 conflicts with requested evidence and non-blocking boundaries','COMPLETED')],
  'records':{'expert_review_groups':32,'separate_expert_followups':1,'classified_register_rows':33,'per_record_quality_labels_created':0},
  'outputs':['reports/QUALITY_CLASSIFICATION_AUDIT.md','reports/2026-11-13-expert-review-register.csv','config/quality-provenance-record.schema.json','EXPERT_REVIEW_REQUIRED.md','scripts/validate_expert_review_register.py','reports/P3_INDEPENDENT_REVIEW.md'],
  'blockers':['Historical expected regimes and row-level source provenance are incomplete; review dispositions need evidence.'],
  'effort':[4,8],'dependencies':['C','D','E','F','I','L']},
 {'id':'L','title':'Correction proposal inventory and packages','tasks':[
  ('L1','Historical applied/pending/source-only proposal inventory reconciled','COMPLETED'),
  ('L2','2021/Q1-2018 exclusions and six RH conflicts tracked','COMPLETED'),
  ('L3','P1/P2/P5 row-level eligibility gates and exclusions','IN_PROGRESS'),
  ('L4','Five JSON/CSV package shells, exclusions, MCP contract, and deterministic validator','COMPLETED'),
  ('L5','P3 source-first revision and bounded 2009–2020 multi-variable source-only inventory','COMPLETED')],
  'records':{'inventory_targets':272,'pending_scope_items':20,'validated_new_restored_candidates':0,'locally_validated_estimated_candidates_v1_superseded':107,'P3_v2_estimated':24,'P3_v2_review_required':83,'source_only_union_timestamps_2009_2020':207182,'priority_packages_built':6,'P1_source_copy_targets':8965,'P2_shared_RH_pairs':30391,'P3_synthetic_masked_blocks':19714,'P4_long_outage_archive_rows':8634,'P5_exact_secondary_concordance_rows':304758,'exclusion_scope_counts_non_additive':True},
  'outputs':['reports/PROPOSAL_INVENTORY.md','reports/2026-11-13-proposal-inventory.csv','reports/CONSOLIDATED_CORRECTIONS_REPORT.md','reports/MASTER_AUDIT_REPORT.md','reports/2026-11-13-priority-proposal-package-validation.json','reports/2026-11-13-priority-milestone-zip-manifest.json','proposals/restored_temperature/manifest.json','proposals/restored_humidity/manifest.json','proposals/estimated_short_temperature_gaps/manifest.json','proposals/estimated_humidity_2022/manifest.json','proposals/restored_secondary_sensors/manifest.json','reports/P3_INDEPENDENT_REVIEW.md','reports/SOURCE_ONLY_ROWS_2009_2020.md','proposals/estimated_short_temperature_gaps_v2/manifest.json','proposals/restored_source_only_rows_v2/manifest.json','scripts/validate_source_only_review_package.py'],
  'blockers':['No candidate batch yet satisfies all row-level identity/unit/history/context/uncertainty gates; this does not block other packages.'],
  'effort':[8,20],'dependencies':['C','D','E','F','I','K','M','N']},
 {'id':'M','title':'Offline package simulation','tasks':[
  ('M1','Offline simulator implementation and package contract','COMPLETED'),
  ('M2','12 synthetic fixture tests pass','COMPLETED'),
  ('M3','Local offline simulation of concrete ESTIMATED short-gap package (scope-limited)','COMPLETED'),
  ('M4','Runtime Weather MCP multi-operation behavior beyond local contract','IN_PROGRESS'),
  ('M5','P3 v2 offline simulation and dependency/batch/episode checks','COMPLETED')],
  'records':{'synthetic_simulation_tests':12,'source_first_guard_tests':7,'real_packages_simulated':2,'simulated_estimated_timestamps_v1_superseded':107,'simulated_estimated_timestamps_v2':24,'source_conflicts_blocked':83},
  'outputs':['reports/LOCAL_CORRECTION_SIMULATION.md','reports/2026-11-13-local-correction-simulation-tests.json','src/meteo_audit/simulation.py','tests/test_correction_simulation.py','scripts/simulate_estimated_short_temperature_proposals.py','proposals/estimated_short_temperature_gaps/simulation.json','scripts/simulate_p3_source_first_v2.py','scripts/validate_p3_source_first_v2.py','proposals/estimated_short_temperature_gaps_v2/simulation.json'],
  'blockers':['No eligible real candidate package exists yet; no database dry-run or write is permitted.'],
  'effort':[3,7],'dependencies':['L','N']},
 {'id':'N','title':'Audit CLI and repeatable validation framework','tasks':[
  ('N1','Allowlisted offline validator CLI and SHA-256 run manifests','COMPLETED'),
  ('N2','Same-scope validator-run comparison and repeatability check','COMPLETED'),
  ('N3','Offline validator bundles for many recent deliverables','COMPLETED'),
  ('N4','Standard read-only SQL/source extraction runner across archive ranges','IN_PROGRESS'),
  ('N5','Package schema validation, simulation and readiness/report integration','COMPLETED'),
  ('N6','Source-first policy, duplicate guard and clean-extract reproducibility for v2 ZIP','COMPLETED')],
  'records':{'cli_unit_tests':3,'repeat_validator_runs':2,'p3_v2_package_files':20,'active_proposal_operations':24,'duplicate_operations':0,'clean_extract_reproduction':'PASS; seven source-first tests in isolated ZIP extraction','manifested_runs':'many; exact count dynamic in runs/'},
  'outputs':['scripts/meteo_audit.py','reports/2026-11-13-cli-repeatability-comparison.json','README.md','runs/20261113T063732Z-76a5fcf2/manifest.json','scripts/validate_priority_proposal_shells.py','reports/2026-11-13-priority-proposal-package-validation.json','src/meteo_audit/source_first.py','tests/test_source_first_guard.py','scripts/validate_source_first_active_proposals.py','scripts/validate_source_only_review_package.py','scripts/reproduce_p3_v2_clean.py','config/active_proposal_registry.json','loucka_historical_audit_and_priority_corrections_v2.zip'],
  'blockers':['Current CLI is offline only; source extraction/SQL adapter and package orchestration are not unified.'],
  'effort':[4,10],'dependencies':['A','L','M','O']},
 {'id':'O','title':'Archive readiness','tasks':[
  ('O1','Provisional 198-cell matrix for 11 channels','COMPLETED'),
  ('O2','Annual availability for all 77 numeric fields reconciled to snapshots','COMPLETED'),
  ('O3','Monthly availability 77 × 216 buckets reconciled to annual totals','COMPLETED'),
  ('O4','Source provenance/QC/readiness status for all relevant 78+ channels','IN_PROGRESS'),
  ('O5','Final readiness sign-off and complete archive delivery','IN_PROGRESS')],
  'records':{'initial_readiness_cells':198,'annual_field_year_cells':1386,'monthly_field_month_cells':16632,'ready_cells':0},
  'outputs':['reports/FINAL_ARCHIVE_READINESS.md','reports/2026-11-13-provisional-archive-readiness.csv','reports/2026-11-13-provisional-archive-readiness.json','reports/2026-11-13-monthly-archive-field-availability-2009-2026.md','loucka_historical_audit_and_priority_corrections_v1.zip','reports/2026-11-13-priority-milestone-zip-manifest.json','loucka_historical_audit_and_priority_corrections_v2.zip','reports/2026-11-13-priority-v2-zip-manifest.json','scripts/validate_priority_milestone_zip.py'],
  'blockers':['Fact availability is complete for 77 numeric fields, but per-channel source/QC decisions for all goal variables remain unfinished.'],
  'effort':[5,12],'dependencies':['A','B','C','D','E','F','G','H','I','J','K','L','N']},
]

def manifest_outputs():
    found={}
    for p in (ROOT/'runs').glob('*/manifest.json'):
        try:d=json.loads(p.read_text())
        except Exception:continue
        if d.get('status')!='succeeded':continue
        for o in d.get('outputs',[]):
            path=o.get('path');f=ROOT/path if path else None
            if not f or not f.is_file():continue
            try:sha=hashlib.sha256(f.read_bytes()).hexdigest()
            except OSError:continue
            if sha==o.get('sha256') and f.stat().st_size==o.get('bytes'):
                found.setdefault(path,[]).append({'run_id':d.get('run_id'),'manifest':p.relative_to(ROOT).as_posix()})
    for p in (ROOT/'proposals').glob('*/manifest.json'):
        try: d=json.loads(p.read_text())
        except Exception: continue
        for rel,record in d.get('artifacts',{}).items():
            f=p.parent/rel
            if not f.is_file(): continue
            try: payload=f.read_bytes()
            except OSError: continue
            if len(payload)==record.get('bytes') and hashlib.sha256(payload).hexdigest()==record.get('sha256'):
                found.setdefault(f.relative_to(ROOT).as_posix(),[]).append({'run_id':'package-manifest','manifest':p.relative_to(ROOT).as_posix()})
    ext=ROOT/'reports/2026-11-13-priority-v2-zip-manifest.json'
    if ext.is_file():
        try:d=json.loads(ext.read_text());f=ROOT/d['archive']
        except (ValueError,KeyError):f=None;d={}
        if f and f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==d.get('sha256'):
            found.setdefault(f.relative_to(ROOT).as_posix(),[]).append({'run_id':'external-zip-manifest','manifest':ext.relative_to(ROOT).as_posix()})
    return found

def build():
    hash_evidence=manifest_outputs();stage_data=[];overall_done=overall_total=0;effort_lo=effort_hi=0
    for s in STAGES:
        tasks=[{'id':i,'task':n,'status':st,'verified':st=='COMPLETED'} for i,n,st in s['tasks']]
        done=sum(x['verified'] for x in tasks);total=len(tasks);overall_done+=done;overall_total+=total
        status='COMPLETED' if done==total else ('NOT_STARTED' if done==0 and all(x['status']=='NOT_STARTED' for x in tasks) else 'IN_PROGRESS')
        if s.get('blocked'):status='BLOCKED'
        arts=[]
        for path in s['outputs']:
            f=ROOT/path;exists=f.is_file();matches=hash_evidence.get(path,[]) if exists else []
            arts.append({'path':path,'created':exists,'verified':bool(matches),'verified_by':matches[-1] if matches else None})
        lo,hi=s['effort'];effort_lo+=lo;effort_hi+=hi
        stage_data.append({'id':s['id'],'name':s['title'],'status':status,'defined_subtasks':total,'verified_subtasks':done,'subtask_completion_percent':round(100*done/total,1),
          'subtasks':tasks,'completed_subtasks':[x['task'] for x in tasks if x['verified']],
          'remaining_subtasks':[{'task':x['task'],'state':x['status']} for x in tasks if not x['verified']],
          'analyzed_records':s['records'],'tracked_output_scope':'Only explicitly named primary deliverables in this stage record; does not count every subordinate/raw/cache file. Stage counts are non-additive.',
          'created_outputs':sum(a['created'] for a in arts),'verified_outputs':sum(a['verified'] for a in arts),'tracked_outputs':arts,
          'current_blockers':s['blockers'],'remaining_analytical_effort_hours':{'min':lo,'max':hi},'dependencies':s['dependencies']})
    out={'as_of_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'project_root':str(ROOT),'status_enum':['COMPLETED','COMPLETED_WITH_LIMITATIONS','IN_PROGRESS','BLOCKED','NOT_STARTED'],
      'safety':{'database':'READ_ONLY','staging_or_apply':'prohibited','protected_2018_q1':'INTERIM_LIVE; no new proposals','protected_2021':'diagnostic only; no corrections','publication':'prohibited'},
      'progress_methodology':{'subtask_percent':'verified explicit subtasks / all explicit subtasks, equally weighted; not time- or quality-weighted and not an end-goal completeness claim','outputs':'counts use tracked primary artifact lists only; created=file exists; verified=current SHA-256 and byte count match output record in at least one succeeded checkpoint manifest','record_counts':'counts are scope-specific and non-additive; same row can appear in multiple analyses','stage_state':'no stage is marked BLOCKED unless no safe useful work remains without an external/user change'},
      'overall':{'status':'IN_PROGRESS','verified_subtasks':overall_done,'defined_subtasks':overall_total,'subtask_completion_percent':round(100*overall_done/overall_total,1),'stage_count':15,'completed_stages':sum(x['status']=='COMPLETED' for x in stage_data),'completed_with_limitations_stages':sum(x['status']=='COMPLETED_WITH_LIMITATIONS' for x in stage_data),'in_progress_stages':sum(x['status']=='IN_PROGRESS' for x in stage_data),'blocked_stages':sum(x['status']=='BLOCKED' for x in stage_data),'not_started_stages':sum(x['status']=='NOT_STARTED' for x in stage_data)},
      'estimated_remaining_effort_hours':{'min':effort_lo+3,'max':effort_hi+8,'includes':'A–O remaining tasks plus first-priority package validation and final zip preparation','excludes':'external expert response/wait and any authorized database application (not planned)'},
      'calendar_forecast':{'range':'approximately 5–12 weeks at 15–20 focused analyst hours per week','uncertainty':'high (roughly ±50%); depends on source lineage access, winter/reference evidence and number of safe candidate rows','pace_basis':'recent deterministic 18-year annual and 216-month availability passes completed in seconds to minutes; remaining package eligibility and model evidence require materially more per-row review than aggregate work'},
      'priority_work':['P1 RESTORED outTemp','P2 RESTORED humidity','P3 ESTIMATED short temperature gaps','P4 2022 humidity','P5 other RESTORED sensors'],'stages':stage_data}
    return out

def status_md(d):
    o=d['overall'];lines=['## Aktuální matice etap A–O (automaticky sestavena z ověřených checkpointů)','',f"Snapshot: `{d['as_of_utc']}`. Definované podúkoly ověřené **{o['verified_subtasks']}/{o['defined_subtasks']} ({o['subtask_completion_percent']}%)**; jde jen o podíl výslovně vypsaných, stejně vážených checkpointů, nikoli o procento kvality nebo úplnosti celého archivu.",'', '| Etapa | Stav | Podúkoly ověřené | Záznamy / rozsah | Výstupy vytvořené / hashově ověřené | Zbývající práce | Závislosti |','|---|---|---:|---|---:|---|---|']
    for s in d['stages']:
        records='; '.join(f'{k}={v}' for k,v in s['analyzed_records'].items() if not isinstance(v,dict))
        lines.append(f"| {s['id']} — {s['name']} | `{s['status']}` | {s['verified_subtasks']}/{s['defined_subtasks']} | {records} | {s['created_outputs']}/{s['verified_outputs']} z {len(s['tracked_outputs'])} evidovaných primárních souborů | {s['remaining_analytical_effort_hours']['min']}–{s['remaining_analytical_effort_hours']['max']} h | {', '.join(s['dependencies']) or '—'} |")
    lines += ['', '### Dokončené a zbývající podúkoly po etapách','']
    for s in d['stages']:
        lines += [f"#### Etapa {s['id']} — {s['name']} (`{s['status']}`)", '', '**Dokončeno:** '+('; '.join(s['completed_subtasks']) or 'zatím nic'), '', '**Zbývá:** '+('; '.join(f"{x['task']} [{x['state']}]" for x in s['remaining_subtasks']) or 'nic'), '', '**Aktuální blokátory / omezení:** '+('; '.join(s['current_blockers']) or 'žádné známé'), '', f"**Náročnost zbývajících úkolů:** {s['remaining_analytical_effort_hours']['min']}–{s['remaining_analytical_effort_hours']['max']} analytických hodin.", '']
    lines += ['### Odhad dokončení','',f"Zbývá přibližně **{d['estimated_remaining_effort_hours']['min']}–{d['estimated_remaining_effort_hours']['max']} analytických hodin**, což odpovídá asi **{d['calendar_forecast']['range']}**. Nejistota je vysoká: {d['calendar_forecast']['uncertainty']}. Zahrnuje A–O, prioritní validované balíčky a přípravu prvního ZIP; nezahrnuje čekání na externí odborné odpovědi. Podklad a předpoklady: `{d['calendar_forecast']['pace_basis']}",'', 'Strojově čitelná evidence a primární výstupy: `PROGRESS.json`; seznam priorit a ochranné podmínky v `MASTER_PLAN.md`.','']
    return '\n'.join(lines)

def main():
    # PROGRESS.json is now the canonical live ledger. The static STAGES catalogue above
    # is retained as historical bootstrap metadata and must not overwrite newer checkpoints.
    d=json.loads((ROOT/'PROGRESS.json').read_text())
    p=ROOT/'STATUS.md';old=p.read_text();start='<!-- PROGRESS_MATRIX_START -->';end='<!-- PROGRESS_MATRIX_END -->';block=start+'\n'+status_md(d)+'\n'+end
    if start in old and end in old:
        old=old[:old.index(start)]+block+old[old.index(end)+len(end):]
        p.write_text(old)
    else:
        lines=old.splitlines();idx=1 if lines and lines[0].startswith('# ') else 0
        lines.insert(idx,block);p.write_text('\n'.join(lines)+'\n')
    print(f"PROGRESS: {d['overall']['verified_subtasks']}/{d['overall']['defined_subtasks']} = {d['overall']['subtask_completion_percent']}%; rendered STATUS.md from canonical PROGRESS.json")
if __name__=='__main__':main()
