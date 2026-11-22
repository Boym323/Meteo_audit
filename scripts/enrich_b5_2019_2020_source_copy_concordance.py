#!/usr/bin/env python3
"""Join aggregate exact-key legacy-copy concordance to B5 2019-20 availability."""
import csv,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
av=json.loads((R/'data/b5_2019_2020_per_gap_availability.json').read_text())
co=json.loads((R/'data/b5_2019_2020_source_copy_concordance.json').read_text())
rh=json.loads((R/'data/b5_2019_2020_rh_conflict_delta_summary.json').read_text())
unit=json.loads((R/'data/b5_2019_2020_source_unit_interval_codes.json').read_text())
episode=json.loads((R/'data/b5_2019_oct26_episode_source_context.json').read_text())
endpoints=json.loads((R/'data/b5_2019_2020_gap_endpoint_source_concordance.json').read_text())['rows']
changes=json.loads((R/'data/b5_2019_2020_gap_endpoint_change_events.json').read_text())['rows']
by={r['gap_id']:r for r in co['rows']};assert len(by)==25
rh_by=Counter(x['gap_id'] for x in rh['rows'])
unit_by={x['gap_id']:x for x in unit['rows']}
for r in av['records']:
 q=by.get(r['gap_id'])
 if not q: continue
 r['source_state']='ROW_TIMESTAMP_CONCORDANT_RH_CONFLICT_REVIEW' if int(q['outHumidity_raw_mismatch']) else 'ROW_TIMESTAMP_AND_CHECKED_FIELDS_CONCORDANT'
 if r['gap_id']=='2019:1572134100:1572138000': r['source_state']='SOURCE_COPY_CONCORDANT_TARGET_ENDPOINT_AND_RH_CONFLICT_REVIEW'
 r['source_copy_concordance']={k:q[k] for k in ('old_rows','same_timestamp_rows','old_timestamp_without_wh','outTemp_paired_nonnull','outTemp_exact_raw_match','outTemp_raw_mismatch','outHumidity_paired_nonnull','outHumidity_exact_raw_match','outHumidity_raw_mismatch','rain_paired_nonnull','rain_exact_raw_match','rain_raw_mismatch','rainRate_paired_nonnull','rainRate_exact_raw_match','rainRate_raw_mismatch','windSpeed_paired_nonnull','windSpeed_exact_raw_match','windSpeed_raw_mismatch','windGust_paired_nonnull','windGust_exact_raw_match','windGust_raw_mismatch','windDir_paired_nonnull','windDir_exact_raw_match','windDir_raw_mismatch','barometer_paired_nonnull','barometer_exact_raw_match','barometer_raw_mismatch','old_usUnits','wh_usUnits','old_intervals','wh_intervals')}
 r['source_copy_concordance']['humidity_conflict_delta_group_count']=rh_by[r['gap_id']]
 r['source_copy_concordance'].update({k:unit_by[r['gap_id']][k] for k in ('old_usUnits_min','old_usUnits_max','wh_usUnits_min','wh_usUnits_max','old_interval_min','old_interval_max','wh_interval_min','wh_interval_max')})
endpoint_by={x['gap_id']:x for x in endpoints}
for target in av['records']:
 e=endpoint_by.get(target['gap_id'])
 if not e: continue
 complete=all(e.get(f'{side}_{archive}_outTemp') is not None for side in ('left','right') for archive in ('target','old','wh'))
 if not complete: continue
 mismatched=[side for side in ('left','right') if e[f'{side}_target_outTemp']!=e[f'{side}_old_outTemp']]
 if mismatched:
  target['review_flags']=sorted(set(target.get('review_flags',[])+['TARGET_ENDPOINT_TEMPERATURE_CONFLICT_REVIEW']))
  target['target_endpoint_review']={'complete_source_and_target_endpoints':True,'legacy_outTemp_endpoints_exact_match':all(e[f'{side}_old_outTemp']==e[f'{side}_wh_outTemp'] for side in ('left','right')),'left_legacy_minus_target_outTemp_c':round(e['left_old_outTemp']-e['left_target_outTemp'],3),'right_legacy_minus_target_outTemp_c':round(e['right_old_outTemp']-e['right_target_outTemp'],3),'mismatched_endpoint_sides':mismatched,'left_target_history_events':e['left_target_history_events'],'right_target_history_events':e['right_target_history_events'],'disposition':'REVIEW_REQUIRED','reason':'Exact legacy endpoint copies differ from reconstruction at one or both boundaries; current event history does not resolve pre-audit provenance.'}
# summary across complete endpoint sets
complete=[e for e in endpoints if all(e.get(f'{side}_{archive}_outTemp') is not None for side in ('left','right') for archive in ('target','old','wh'))]
endpoint_mismatches=[(e[f'{side}_old_outTemp']-e[f'{side}_target_outTemp']) for e in complete for side in ('left','right') if e[f'{side}_old_outTemp']!=e[f'{side}_target_outTemp']]
av['endpoint_source_concordance_summary']={'gaps_with_both_legacy_and_target_endpoints':len(complete),'legacy_endpoint_outTemp_exact_matches':sum(e[f'{side}_old_outTemp']==e[f'{side}_wh_outTemp'] for e in complete for side in ('left','right')),'endpoint_sides_compared':2*len(complete),'endpoint_sides_with_legacy_target_outTemp_mismatch':len(endpoint_mismatches),'legacy_minus_target_outTemp_delta_min_c':min(e[f'{side}_old_outTemp']-e[f'{side}_target_outTemp'] for e in complete for side in ('left','right')),'legacy_minus_target_outTemp_delta_max_c':max(e[f'{side}_old_outTemp']-e[f'{side}_target_outTemp'] for e in complete for side in ('left','right')),'endpoint_history_event_count':sum(e['left_target_history_events']+e['right_target_history_events'] for e in complete),'endpoint_history_variables':sorted({x['variable'] for x in changes}),'endpoint_history_detail_rows':len(changes),'gaps_without_complete_both_source_and_target_endpoint_rows':25-len(complete),'query_execution_timestamp_utc':'NOT_CAPTURED_BY_WEATHER_MCP','interpretation':'All 12 complete endpoint source-copy pairs agree with one another; at least one of the two target endpoint outTemps differs in every gap. Four current applied history events are rainRate, not outTemp. No pre-audit cause is inferred.'}
eprows=episode['rows']; inside=[x for x in eprows if x['target_time']>1572134100 and x['target_time']<1572138000]
assert len(inside)==12
for target in av['records']:
 if target['gap_id']=='2019:1572134100:1572138000':
  target['source_state']='SOURCE_COPY_CONCORDANT_TARGET_ENDPOINT_AND_RH_CONFLICT_REVIEW'
  target.setdefault('review_flags',[]).append('TARGET_ENDPOINT_TEMPERATURE_CONFLICT_REVIEW')
  target['target_episode_review']={'interior_timestamps':12,'source_outTemp_exact_matches':12,'source_units':17,'source_interval':5,'reconstruction_endpoint_outTemp_left':11.0,'legacy_endpoint_outTemp_left':11.7,'reconstruction_endpoint_outTemp_right':10.7,'legacy_endpoint_outTemp_right':11.55,'endpoint_history_events':0,'restoration_disposition':'REVIEW_REQUIRED','reason':'Current reconstruction endpoint values differ from both source copies by 0.7 and 0.85 C; no historical change events do not rule out pre-audit edits.'}
for year in (2019,2020):
 rr=[r for r in av['records'] if r['year']==year]
 av['per_year'][str(year)]['states']=dict(Counter(r['source_state'] for r in rr))
av['state_counts']=dict(Counter(r['source_state'] for r in av['records']))
metrics={}
for f in ('outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','barometer'):
 metrics[f]={'paired_nonnull':sum(int(x[f+'_paired_nonnull']) for x in by.values()),'exact_raw_match':sum(int(x[f+'_exact_raw_match']) for x in by.values()),'raw_mismatch':sum(int(x[f+'_raw_mismatch']) for x in by.values())}
av['source_copy_concordance_summary']={'gaps_with_rows':25,'exact_timestamp_rows':sum(int(x['old_rows']) for x in by.values()),'timestamps_matched_in_both_copies':sum(int(x['same_timestamp_rows']) for x in by.values()),'old_rows_without_wh1080_key':sum(int(x['old_timestamp_without_wh']) for x in by.values()),'field_metrics':metrics,'distinct_usUnits_count_pairs':sorted({(x['old_usUnits'],x['wh_usUnits']) for x in by.values()}),'distinct_interval_count_pairs':sorted({(x['old_intervals'],x['wh_intervals']) for x in by.values()}),'actual_usUnits_code_pairs':sorted({(x['old_usUnits_min'],x['old_usUnits_max'],x['wh_usUnits_min'],x['wh_usUnits_max']) for x in unit['rows']}),'actual_interval_value_pairs':sorted({(x['old_interval_min'],x['old_interval_max'],x['wh_interval_min'],x['wh_interval_max']) for x in unit['rows']}),'humidity_conflict_delta_groups':len(rh['rows']),'raw_humidity_delta_wh_minus_old_min':min(x['raw_delta_wh_minus_old'] for x in rh['rows']),'raw_humidity_delta_wh_minus_old_max':max(x['raw_delta_wh_minus_old'] for x in rh['rows']),'gaps_with_humidity_raw_mismatch':sum(int(x['outHumidity_raw_mismatch'])>0 for x in by.values()),'query_execution_timestamp_utc':'NOT_CAPTURED_BY_WEATHER_MCP','interpretation':'Exact timestamp and raw field equality in these copies is not sensor independence or measurement truth. Direct per-gap query confirms both archives report usUnits=17 and matching interval values (5 or 6); no value is selected as correct.'}
av['schema']='b5-2019-2020-gap-per-archive-source-availability-v2'
(R/'data/b5_2019_2020_per_gap_availability.json').write_text(json.dumps(av,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-B5-2019-2020-per-gap-availability.csv').open('w',newline='') as f:
 A=('reconstruction','eu','gw1000','eu_old','old_weewx','wh1080');F=('row_count','outTemp_nonnull','outTemp_zero','outHumidity_nonnull','rain_nonnull','rainRate_nonnull','windSpeed_nonnull','windGust_nonnull','windDir_nonnull','barometer_nonnull','distinct_usUnits','distinct_interval')
 C=('old_rows','same_timestamp_rows','old_timestamp_without_wh','outTemp_paired_nonnull','outTemp_exact_raw_match','outTemp_raw_mismatch','outHumidity_paired_nonnull','outHumidity_exact_raw_match','outHumidity_raw_mismatch','rain_paired_nonnull','rain_exact_raw_match','rain_raw_mismatch','rainRate_paired_nonnull','rainRate_exact_raw_match','rainRate_raw_mismatch','windSpeed_paired_nonnull','windSpeed_exact_raw_match','windSpeed_raw_mismatch','windGust_paired_nonnull','windGust_exact_raw_match','windGust_raw_mismatch','windDir_paired_nonnull','windDir_exact_raw_match','windDir_raw_mismatch','barometer_paired_nonnull','barometer_exact_raw_match','barometer_raw_mismatch','old_usUnits','wh_usUnits','old_intervals','wh_intervals','humidity_conflict_delta_group_count','old_usUnits_min','old_usUnits_max','wh_usUnits_min','wh_usUnits_max','old_interval_min','old_interval_max','wh_interval_min','wh_interval_max')
 cols=['year','gap_id','left_time','right_time','gap_seconds','source_state']+[f'{a}_{v}' for a in A for v in F]+['copy_'+x for x in C];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for r in av['records']:
  q={k:r[k] for k in cols[:6]}
  for a in A:
   for v in F:q[f'{a}_{v}']=r['per_archive'][a][v]
  for k in C:q['copy_'+k]=r.get('source_copy_concordance',{}).get(k,'')
  w.writerow(q)
summary=av['source_copy_concordance_summary']
with (R/'reports/2026-11-14-B5-2019-2020-per-gap-availability.md').open('a') as f:
 f.write('\n## Exact timestamp and field concordance for the 25 source-present gaps\n\n')
 f.write(f"Old_weewx and WH1080 have exact timestamp matches for all {summary['exact_timestamp_rows']} checked rows across all 25 gaps. Both have `usUnits=17`; interval values match between the archives and are 5 or 6. (Earlier `distinct_usUnits=1` and `distinct_interval=1/2` were counts of unique codes, not the actual codes.) Raw non-NULL values match exactly for outTemp {metrics['outTemp']['exact_raw_match']}/{metrics['outTemp']['paired_nonnull']}, rain {metrics['rain']['exact_raw_match']}/{metrics['rain']['paired_nonnull']}, rainRate {metrics['rainRate']['exact_raw_match']}/{metrics['rainRate']['paired_nonnull']}, windSpeed {metrics['windSpeed']['exact_raw_match']}/{metrics['windSpeed']['paired_nonnull']}, windGust {metrics['windGust']['exact_raw_match']}/{metrics['windGust']['paired_nonnull']}, and windDir {metrics['windDir']['exact_raw_match']}/{metrics['windDir']['paired_nonnull']}. No barometer pairs exist.\n\n")
 f.write(f"Across {av['endpoint_source_concordance_summary']['gaps_with_both_legacy_and_target_endpoints']} gaps with both source and target endpoints, the legacy endpoints agree exactly, but {av['endpoint_source_concordance_summary']['endpoint_sides_with_legacy_target_outTemp_mismatch']}/{av['endpoint_source_concordance_summary']['endpoint_sides_compared']} target endpoint sides differ from both legacy copies by {av['endpoint_source_concordance_summary']['legacy_minus_target_outTemp_delta_min_c']:.3f} to {av['endpoint_source_concordance_summary']['legacy_minus_target_outTemp_delta_max_c']:.3f} C. The 4 current endpoint-history events are all rainRate; no outTemp history event was found at those sides. The other 13 gaps lack a complete set of both-source and target endpoint rows. This pattern leaves outTemp provenance unresolved and does not authorize restoration.\n\nThe 2019-10-26/27 gap has exact source-copy agreement for its 12 interior outTemp rows (usUnits=17, interval=5), but its reconstruction endpoint outTemps differ from both copies by 0.7 and 0.85 C; no change events were found. Keep this outTemp episode REVIEW_REQUIRED despite source-copy agreement.\n\nRH is materially different: {metrics['outHumidity']['raw_mismatch']} of {metrics['outHumidity']['paired_nonnull']} paired non-NULL RH values differ, across {summary['gaps_with_humidity_raw_mismatch']} gaps. The rounded raw delta (WH1080 minus old_weewx) spans {summary['raw_humidity_delta_wh_minus_old_min']} to {summary['raw_humidity_delta_wh_minus_old_max']} percentage points. Both archives report the same `usUnits=17` and matching interval values (5 or 6); source identity, calibration, transformations, or previous editing remain unresolved. The copies cannot be treated as independent or as proof of true RH. Hold RH restoration and all ambiguous field candidates for targeted review; no correction emitted.\n\n")
 f.write('The 25 other 2020 gaps have no row in the six checked archives. This does not prove deletion or absence from an unavailable original. Raw aggregates and SQL: `data/b5_2019_2020_source_copy_concordance.json`, `data/b5_2019_2020_rh_conflict_delta_summary.json`, `data/b5_2019_oct26_episode_source_context.json`, and the bounded SQL files.\n')
print(json.dumps({'states':av['state_counts'],'summary':summary},indent=2))
