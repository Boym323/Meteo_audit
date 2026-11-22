#!/usr/bin/env python3
"""Offline validation of 2019-2020 per-gap source availability outputs."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=json.loads((R/'data/b5_2019_2020_per_gap_availability.json').read_text())
assert len(p['records'])==50 and len({r['gap_id'] for r in p['records']})==50
assert p['database_mode']=='READ_ONLY_SELECT_ONLY' and p['query_execution_timestamp_utc']=='NOT_CAPTURED_BY_WEATHER_MCP'
assert p['correction_proposals']==0 and p['source_row_sum_non_additive'] is True
assert p['state_counts']=={'ROW_TIMESTAMP_AND_CHECKED_FIELDS_CONCORDANT':12,'SOURCE_COPY_CONCORDANT_TARGET_ENDPOINT_AND_RH_CONFLICT_REVIEW':1,'ROW_TIMESTAMP_CONCORDANT_RH_CONFLICT_REVIEW':12,'NO_SOURCE_ROW_OBSERVED_IN_SIX_ARCHIVES':25}
assert (R/'data/b5_2019_2020_source_copy_concordance.json').is_file() and (R/'data/b5_2019_2020_rh_conflict_delta_summary.json').is_file()
u=json.loads((R/'data/b5_2019_2020_source_unit_interval_codes.json').read_text()); assert len(u['rows'])==25
assert all((x['old_usUnits_min'],x['old_usUnits_max'],x['wh_usUnits_min'],x['wh_usUnits_max'])==(17,17,17,17) for x in u['rows'])
assert all((x['old_interval_min'],x['old_interval_max'])==(x['wh_interval_min'],x['wh_interval_max']) for x in u['rows'])
episode=json.loads((R/'data/b5_2019_oct26_episode_source_context.json').read_text());assert len(episode['rows'])==14
assert p['per_year']['2019']['gaps']==5 and p['per_year']['2020']['gaps']==45
assert p['per_year']['2019']['per_archive_rows']['old_weewx']==325
assert p['per_year']['2020']['per_archive_rows']['old_weewx']==649
assert p['per_archive_summary']['old_weewx']['rows']==974==p['per_archive_summary']['wh1080']['rows']
c=p['source_copy_concordance_summary'];assert c['exact_timestamp_rows']==c['timestamps_matched_in_both_copies']==974 and c['old_rows_without_wh1080_key']==0
assert c['field_metrics']['outTemp']=={'paired_nonnull':972,'exact_raw_match':972,'raw_mismatch':0}
assert c['field_metrics']['outHumidity']=={'paired_nonnull':499,'exact_raw_match':249,'raw_mismatch':250}
assert c['field_metrics']['rain']=={'paired_nonnull':965,'exact_raw_match':965,'raw_mismatch':0}
assert c['gaps_with_humidity_raw_mismatch']==13 and c['raw_humidity_delta_wh_minus_old_min']==43.9 and c['raw_humidity_delta_wh_minus_old_max']==84.6
ep=p['endpoint_source_concordance_summary'];assert ep['gaps_with_both_legacy_and_target_endpoints']==12 and ep['endpoint_sides_with_legacy_target_outTemp_mismatch']==19 and ep['endpoint_history_variables']==['rainRate']
assert sum('TARGET_ENDPOINT_TEMPERATURE_CONFLICT_REVIEW' in r.get('review_flags',[]) for r in p['records'])==12
assert p['per_archive_summary']['old_weewx']['gaps_with_rows']==25==p['per_archive_summary']['wh1080']['gaps_with_rows']
e=next(r for r in p['records'] if r['gap_id']=='2019:1572134100:1572138000');assert e['target_episode_review']['restoration_disposition']=='REVIEW_REQUIRED' and e['target_episode_review']['source_outTemp_exact_matches']==12
for r in p['records']:
 assert 3600<=r['gap_seconds']<86400 and r['source_copy_identity_or_quality_proven'] is False
 if r['source_state']=='NO_SOURCE_ROW_OBSERVED_IN_SIX_ARCHIVES': assert not sum(v['row_count'] for v in r['per_archive'].values())
 else: assert r['per_archive']['old_weewx']['row_count']==r['per_archive']['wh1080']['row_count']>0 and r['source_copy_concordance']['old_rows']==r['source_copy_concordance']['same_timestamp_rows']
assert sum(len(list((R/f'data/b5_{y}_gap_per_archive_raw_chunks').glob(f'b5_{y}_*.json'))) for y in (2019,2020))==18
assert sum(len(list((R/f'sql/readonly/b5_{y}_gap_availability').glob('*.sql'))) for y in (2019,2020))==18
with (R/'reports/2026-11-14-B5-2019-2020-per-gap-availability.csv').open(newline='') as f: assert len(list(csv.DictReader(f)))==50
print('PASS: 50 gap events, source-copy field concordance, actual unit codes, endpoint conflict disposition and no-row caveats validated offline')
