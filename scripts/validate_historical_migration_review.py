#!/usr/bin/env python3
"""Offline consistency checks for the 2026-11-13 historical lineage deliverables."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
checks=[]
def ck(name, ok, detail): checks.append({'check':name,'status':'PASS' if ok else 'FAIL','detail':detail})
owner=load('source_inventory.json')['owner_attested_lineage_20261113']
ck('owner_testimony_is_not_technical_verification',owner['evidence_class']=='OWNER_ATTESTED' and owner['technically_independently_verified'] is False,owner['evidence_class'])
si=load('source_inventory.json')['historical_lineage_and_cleaning_review_20261113']['source_only_inventory']
ck('source_only_inventory_reconciles',si['timestamps']==207182 and si['on_exact_5min_grid']+si['off_grid']==si['timestamps'] and si['both_source_copies']+si['single_source_copy']==si['timestamps'],str(si))
ck('source_only_causes_not_overclaimed',si['per_row_root_cause']=='UNRESOLVED; dimensions overlap and are not additive',si['per_row_root_cause'])
proxy=load('data/source_only_root_cause_proxies_by_year.json')
ck('annual_source_only_proxies_reconcile',proxy['total_source_only']==207182 and len(proxy['years'])==12 and proxy['root_cause_assignments'].startswith('none;'),'12 UTC years; margins are non-additive and no cause assigned')
wind=load('data/historical_wind_transformation_annual.json')
wy=wind['annual']
ck('wind_yearly_ratio_screen_reconciles',len(wy)==12 and [x['utc_year'] for x in wy]==list(range(2009,2021)) and all(int(x['unit_mismatch'])==x['exact_pairs'] for x in wy) and sum(int(x['interval_mismatch']) for x in wy)==42,'12 UTC years; unit flags differ and 42 interval exceptions are explicit')
ck('wind_epoch_transitions_supported',int(next(x for x in wy if x['utc_year']==2009)['speed_ratio1'])==int(next(x for x in wy if x['utc_year']==2009)['speed_nonzero_pairs']) and int(next(x for x in wy if x['utc_year']==2014)['speed_ratio36'])==int(next(x for x in wy if x['utc_year']==2014)['speed_nonzero_pairs']) and int(next(x for x in wy if x['utc_year']==2020)['speed_nonzero_pairs'])-int(next(x for x in wy if x['utc_year']==2020)['speed_ratio36'])==2771,'2009 ratio 1; 2014 ratio 3.6; 2020 exceptions')
bounds=wind['focused_2013_epoch']
ck('wind_2013_exact_boundary_probe',any(x['field_name']=='windSpeed' and x['ratio_class']=='RATIO_1' and x['last_utc']=='2013-04-06T15:10:00.000Z' for x in bounds) and any(x['field_name']=='windSpeed' and x['ratio_class']=='RATIO_3_6' and x['first_utc']=='2013-04-12T17:55:00.000Z' for x in bounds),'observed bounds reported without interpolated cutover')
a=load('data/source_only_2010_offgrid_nearest_slot_detail.json')['nearest_slot_summary'][0]
b=load('data/source_only_2012_offgrid_review.json')['nearest_slot_occupancy']
c=load('data/source_only_2018_q2_q4_offgrid_summary.json')
ck('offgrid_target_slots_occupied',int(a['nearest_slots_without_target_row'])==0 and int(b['nearest_target_missing'])==0 and c['nearest_reconstruction_target_rows_present']==421 and c['nearest_slot_collision_count']==0,'2010/2012/2018 bounded cohorts')
h=load('data/gw1000_gw3000_historical_concordance_summary.json')
ck('gw_historical_pair_totals',sum(x['exact_timestamp_pairs'] for x in h['annual'])==1592925 and sum(x['gw3000_only_rows']+x['gw1000_only_rows'] for x in h['annual'])==0,'1,592,925 pairs')
fields={x['variable']:x for x in h['field_totals']}
ck('gw_primary_exact_concordance',all(fields[x]['different_nonnull']==0 for x in ['outTemp','outHumidity','rain','windSpeed','windGust']),'primary exact matches')
s=load('data/gw1000_gw3000_2026_field_slices.json')
ck('2026_parallel_slices_valid',len(s['rows'])==2 and [r['exact_pairs'] for r in s['rows']]==[19130,62479],'pre/post divergence pair counts')
month=load('data/gw1000_gw3000_2026_monthly_profile.json')
ck('2026_monthly_profile_reconciles',sum(x['exact_timestamp_pairs'] for x in month['monthly'][:10])==81609 and month['row_only_2026_snapshot']['gw3000_only']==9562 and month['row_only_2026_snapshot']['gw1000_only']==231,'snapshot month aggregates and row-only totals')
required=['SOURCE_LINEAGE_OWNER_STATEMENT.md','HISTORICAL_MIGRATION_AND_CLEANING_REPORT.md','SOURCE_TIMESTAMP_ALIGNMENT_REPORT.md','HISTORICAL_WIND_TRANSFORMATION_REPORT.md','GW1000_GW3000_CONCORDANCE_REPORT.md','SOURCE_ONLY_RESTORATION_ELIGIBILITY.md','HUMAN_INPUT_REQUIRED.md']
for p in required: ck('file_exists:'+p,(ROOT/p).is_file(),str((ROOT/p).stat().st_size if (ROOT/p).exists() else 0))
ck('offline_validation_scope',all(x['status']=='PASS' for x in checks if x['check']!='offline_validation_scope'),'validator reads local files only; no database connection code')
res={'validator':'validate_historical_migration_review.py','scope':'offline JSON/report consistency only','database_access':'NONE','database_writes':0,'checks':checks,'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL'}
(ROOT/'data/historical_migration_review_validation.json').write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'status':res['status'],'checks':len(checks),'failed':[x for x in checks if x['status']=='FAIL']},ensure_ascii=False))
if res['status']!='PASS': raise SystemExit(1)
