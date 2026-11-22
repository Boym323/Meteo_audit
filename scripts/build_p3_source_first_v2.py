#!/usr/bin/env python3
"""SUPERSEDED: one-time P3 v2 builder; must not rewrite the active v2.1 package."""
from __future__ import annotations

raise SystemExit('SUPERSEDED one-time P3 v2 builder; preserve v2.1 and use its package validator/simulator')
import csv, hashlib, json, math, shutil, sys
from collections import Counter, defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from meteo_audit.source_first import classify_before_estimate
V1=R/'archives/v1/estimated_short_temperature_gaps'
OUT=R/'proposals/estimated_short_temperature_gaps_v2'
SRC=json.loads((R/'data/p3_independent_review/source_availability_107.json').read_text())
META=json.loads((V1/'candidate_metadata.json').read_text())
CORR=json.loads((V1/'corrections.json').read_text())
NEIGH=json.loads((R/'data/p3_independent_review/source_neighbors_83.json').read_text())['rows']
OFFS=json.loads((R/'data/p3_independent_review/nearby_offset_probes_24.json').read_text())['results']
EVENTS=json.loads((R/'data/p3_independent_review/change_event_counts_107.json').read_text())['rows']
COND=json.loads((R/'data/p3_independent_review/conditional_holdout_2019_2020.json').read_text())
assert len(META)==len(CORR)==SRC['target_count']==107
src_by_t={x['target_time']:x for x in SRC['targets']}
corr_by_t={x['timestamp']:x for x in CORR}
events_by_t={x['target_time']:int(x['all_change_events']) for x in EVENTS}
assert len(events_by_t)==107 and sum(events_by_t.values())==0
neigh={(x['target_time'],x['source_database']):x for x in NEIGH}
offset={(db,r['target_time']):r for group in OFFS for db in [group['source']] if 'rows' in group for r in group['rows']}

# Conservative empirical bin upper bounds by gap duration.
def upper_quantile(hist,p):
    total=sum(n for _,n in hist); target=math.ceil(total*p); cum=0
    for bucket,n in sorted(hist):
        cum+=n
        if cum>=target:return round(float(bucket)+0.1,1)
    raise ValueError('empty histogram')
uncertainty={}; holdout_stats={}
for g in COND['histograms']:
    pooled=Counter()
    yearly={}
    episodes=0
    for year,y in g['years'].items():
        yearly[year]={'episodes':int(y.get('episodes',0)),'points':int(y.get('points',0))}
        episodes+=int(y.get('episodes',0))
        pooled.update({float(b):int(n) for b,n in y['histogram']})
    hist=list(pooled.items()); points=sum(pooled.values())
    uncertainty[int(g['gap_minutes'])]={
      'p50_abs_error_c_upper_bin':upper_quantile(hist,.50),
      'p90_abs_error_c_upper_bin':upper_quantile(hist,.90),
      'p95_abs_error_c_upper_bin':upper_quantile(hist,.95),
      'observed_sample_max_abs_error_c_upper_bin':round(max(pooled)+.1,1),
      'holdout_point_errors':points,'complete_masked_episodes':episodes,
      'year_counts':yearly,
      'meaning':'empirical 0.1 C histogram upper edges; not a guaranteed or calibrated predictive interval'
    }

extrema={}
for item in COND['extrema']:
    gm=int(item['gap_minutes']); rows=item.get('rows',[])
    assert len(rows)==2,(gm,rows)
    extrema[gm]={
      'episodes':sum(int(x['episode_n']) for x in rows),
      'episodes_hidden_max':sum(int(x['episodes_hidden_max']) for x in rows),
      'episodes_hidden_min':sum(int(x['episodes_hidden_min']) for x in rows),
      'max_hidden_max_error_c':max(float(x['max_hidden_max_error_c']) for x in rows),
      'max_hidden_min_error_c':max(float(x['max_hidden_min_error_c']) for x in rows),
      'yearly':rows
    }

# Source-first decision across all six archives. Source rows block ESTIMATED.
records=[]; review=[]; estimates=[]; episode_classes=defaultdict(set)
source_counts={db:{'rows':0,'outTemp':0,'outHumidity':0,'rain':0,'rainRate':0,'usUnits17':0,'interval5':0} for db in SRC['source_databases']}
field_ranges=defaultdict(lambda:defaultdict(list))
for m in META:
    t=int(m['timestamp']); target=src_by_t[t]; original=corr_by_t[t]
    change_n=events_by_t[t]
    source_list=[]; row_presence={}
    for db in SRC['source_databases']:
        v=target['sources'][db]; row_presence[db]=v['source_row_exists']
        source_list.append({'source_row_exists':v['source_row_exists'],'value':v['fields']['outTemp']})
        if v['source_row_exists']:
            c=source_counts[db]; c['rows']+=1
            for f in ('outTemp','outHumidity','rain','rainRate'):
                value=v['fields'][f]
                if value is not None:
                    c[f]+=1; field_ranges[db][f].append(float(value))
            c['usUnits17']+=int(v['fields']['usUnits']==17)
            c['interval5']+=int(v['fields']['interval']==5)
    has_any_source_temp=any(v['fields']['outTemp'] is not None for v in target['sources'].values())
    decision=classify_before_estimate(source_checks_complete=True,sources=source_list,
      target_row_exists=any(row_presence.values()),change_event_count=change_n,exact_timestamp=True)
    left=int(m['left']['t']); right=int(m['right']['t']); ep=(left,right); gap=int(m['gap_s'])
    episode_classes[ep].add(has_any_source_temp)
    interp=float(original['new_value'])
    old=target['sources']['old_weewx']; wh=target['sources']['weewx_WH1080']
    old_y=old['fields']['outTemp']; wh_y=wh['fields']['outTemp']
    use_estimate=(not has_any_source_temp and decision.status=='ESTIMATED_ELIGIBLE_FOR_REVIEW'
                  and bool(m['gates'].get('no_history')) and gap//60 in uncertainty
                  and all(m['gates'].get(k) for k in ('interval5','units16','temperature_positive','temperature_max35','rh20_95','dry','wind5','abs_delta_le2')))
    status='ESTIMATED' if use_estimate else ('REVIEW_REQUIRED_SOURCE_VS_ESTIMATED_CONFLICT' if has_any_source_temp else 'REVIEW_REQUIRED_SOURCE_OR_MODEL_GATE')
    gapmin=gap//60
    u=uncertainty.get(gapmin)
    meta={
      **m,
      'source_first_status':decision.status,
      'p3_v2_status':status,
      'exact_source_rows_by_archive':row_presence,
      'source_measurement_values':{db:target['sources'][db]['fields']['outTemp'] for db in SRC['source_databases']},
      'source_lineage_status':'UNVERIFIED_ARCHIVE_ROLE_AND_PER_ROW_LINEAGE' if has_any_source_temp else 'NO_EXACT_SOURCE_ROW_IN_ALL_SIX_ARCHIVES',
      'target_archive_row_exists_any_source':any(row_presence.values()),
      'reconstruction_changes_events_all_variables':change_n,
      'interpolation_value_c':interp,
      'source_interpolation_difference_c':{
         'old_weewx_signed':None if old_y is None else round(float(old_y)-interp,10),
         'old_weewx_abs':None if old_y is None else round(abs(float(old_y)-interp),10),
         'weewx_WH1080_signed':None if wh_y is None else round(float(wh_y)-interp,10),
         'weewx_WH1080_abs':None if wh_y is None else round(abs(float(wh_y)-interp),10)},
      'source_auxiliary_availability':{db:{f:target['sources'][db]['fields'][f] for f in ('outHumidity','rain','rainRate','barometer','pressure','altimeter','inTemp','inHumidity','windSpeed','windDir','windGust','radiation','UV','extraTemp1','extraTemp2','soilTemp1','soilTemp2','soilTemp3','soilTemp4','soilMoist1')} for db in SRC['source_databases']},
      'source_temperature_neighbors':{db:neigh.get((t,db)) for db in ('old_weewx','weewx_WH1080')},
      'nearby_offset_probe':{db:offset.get((db,t)) for db in SRC['source_databases']},
      'uncertainty':u,
      'extrema_holdout':extrema.get(gapmin),
      'uncertainty_limitation':'Empirical conditional holdout summary, not a guaranteed prediction interval; deterministic masks do not represent MNAR/fog/inversion and leave rare extremes uncertain.'
    }
    records.append(meta)
    if status=='ESTIMATED':
        prop=dict(original)
        prop['reason']=(f"ESTIMATED linear interpolation after exact source-first check across six archives; no exact source row/value and no change event. See P3 v2 metadata, gap {gap}s, conditional holdout; not a prediction guarantee.")
        estimates.append(prop)
    else:
        nold=neigh.get((t,'old_weewx'),{}); nwh=neigh.get((t,'weewx_WH1080'),{})
        review.append({
          'timestamp':t,'utc_year':m.get('timestamp'),'gap_seconds':gap,'left_endpoint_utc':left,'right_endpoint_utc':right,
          'interpolation_c':interp,'old_weewx_outTemp':old_y,'weewx_WH1080_outTemp':wh_y,
          'old_weewx_abs_diff_c':meta['source_interpolation_difference_c']['old_weewx_abs'],
          'weewx_WH1080_abs_diff_c':meta['source_interpolation_difference_c']['weewx_WH1080_abs'],
          'old_weewx_outHumidity':old['fields']['outHumidity'],'weewx_WH1080_outHumidity':wh['fields']['outHumidity'],
          'old_weewx_rain':old['fields']['rain'],'weewx_WH1080_rain':wh['fields']['rain'],
          'old_weewx_rainRate':old['fields']['rainRate'],'weewx_WH1080_rainRate':wh['fields']['rainRate'],
          'old_weewx_interval':old['fields']['interval'],'wh1080_interval':wh['fields']['interval'],
          'old_weewx_usUnits':old['fields']['usUnits'],'wh1080_usUnits':wh['fields']['usUnits'],
          'old_prev_outTemp':None if not nold else nold['previous_outTemp'],'old_next_outTemp':None if not nold else nold['next_outTemp'],
          'wh_prev_outTemp':None if not nwh else nwh['previous_outTemp'],'wh_next_outTemp':None if not nwh else nwh['next_outTemp'],
          'disposition':status,'reason':'Exact source measurement exists; copies/history/units/context support screening only, but database source role and per-row lineage are not authenticated. Do not choose source value or interpolation automatically.'})

assert len(records)==107 and len(estimates)==24 and len(review)==83
assert all(len(v)==1 for v in episode_classes.values()),'source-present and source-free targets mixed in a gap episode'
assert len(episode_classes)==56 and sum(not next(iter(v)) for v in episode_classes.values())==14
assert sum(source_counts[d]['outTemp'] for d in SRC['source_databases'])==165
assert all(source_counts[d]['usUnits17']==source_counts[d]['rows'] and source_counts[d]['interval5']==source_counts[d]['rows'] for d in ('old_weewx','weewx_WH1080'))

# Aggregate direct-copy and source-vs-interpolation diagnostics.
common=[r for r in records if r['source_measurement_values']['old_weewx'] is not None and r['source_measurement_values']['weewx_WH1080'] is not None]
assert len(common)==82 and all(r['source_measurement_values']['old_weewx']==r['source_measurement_values']['weewx_WH1080'] for r in common)
whrows=[r for r in records if r['source_measurement_values']['weewx_WH1080'] is not None]
abs_diffs=[r['source_interpolation_difference_c']['weewx_WH1080_abs'] for r in whrows]
mean_abs=sum(abs_diffs)/len(abs_diffs); maxrow=max(whrows,key=lambda r:r['source_interpolation_difference_c']['weewx_WH1080_abs'])
assert abs(mean_abs-0.5879518072)<1e-8
assert maxrow['timestamp']==1561907700 and abs(maxrow['source_interpolation_difference_c']['weewx_WH1080_abs']-3.8)<1e-9

# Build package files without touching the historical v1 archive.
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
for name in ('source_availability_107.json','source_neighbors_83.json','nearby_offset_probes_24.json','change_event_counts_107.json'):
    shutil.copy2(R/'data/p3_independent_review'/name,OUT/name)
shutil.copy2(R/'data/p3_independent_review/conditional_holdout_2019_2020.json',OUT/'conditional_holdout_2019_2020.json')
(OUT/'candidate_metadata.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
(OUT/'corrections.json').write_text(json.dumps(estimates,ensure_ascii=False,indent=2)+'\n')
with (OUT/'corrections.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['operation','timestamp','variable','new_value','expected_old_value','source_database','source_time','source_value','reason','us_units','interval_minutes']);w.writeheader();w.writerows(estimates)
with (OUT/'review_required.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(review[0]));w.writeheader();w.writerows(review)
with (OUT/'per_target_source_evidence.csv').open('w',newline='') as f:
    cols=['timestamp','p3_v2_status','gap_s','interpolation_value_c','source_rows_present','old_weewx_outTemp','weewx_WH1080_outTemp','old_weewx_RH','weewx_WH1080_RH','old_weewx_rain','weewx_WH1080_rain','old_weewx_rainRate','weewx_WH1080_rainRate','old_weewx_abs_diff_c','weewx_WH1080_abs_diff_c','reconstruction_changes_events_all_variables','source_fields_json']
    w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
    for r in records:
      s=src_by_t[r['timestamp']]
      w.writerow({'timestamp':r['timestamp'],'p3_v2_status':r['p3_v2_status'],'gap_s':r['gap_s'],'interpolation_value_c':r['interpolation_value_c'],
       'source_rows_present':sum(bool(x['source_row_exists']) for x in s['sources'].values()),
       'old_weewx_outTemp':s['sources']['old_weewx']['fields']['outTemp'],'weewx_WH1080_outTemp':s['sources']['weewx_WH1080']['fields']['outTemp'],
       'old_weewx_RH':s['sources']['old_weewx']['fields']['outHumidity'],'weewx_WH1080_RH':s['sources']['weewx_WH1080']['fields']['outHumidity'],
       'old_weewx_rain':s['sources']['old_weewx']['fields']['rain'],'weewx_WH1080_rain':s['sources']['weewx_WH1080']['fields']['rain'],
       'old_weewx_rainRate':s['sources']['old_weewx']['fields']['rainRate'],'weewx_WH1080_rainRate':s['sources']['weewx_WH1080']['fields']['rainRate'],
       'old_weewx_abs_diff_c':r['source_interpolation_difference_c']['old_weewx_abs'],'weewx_WH1080_abs_diff_c':r['source_interpolation_difference_c']['weewx_WH1080_abs'],
       'reconstruction_changes_events_all_variables':r['reconstruction_changes_events_all_variables'],'source_fields_json':json.dumps(s['sources'],ensure_ascii=False,separators=(',',':'))})
with (OUT/'excluded_cases.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['scope','candidate_count','disposition','reason'])
    w.writerow(['Exact source outTemp present at timestamp in one or both historical archives',83,'REVIEW_REQUIRED_SOURCE_VS_ESTIMATED_CONFLICT','Do not select restoration or interpolation until original archive role, per-row lineage and unit/time transformation are verified.'])
    w.writerow(['Exact source row absent from all six archives; same short-gap endpoint gates and conditional validation available',24,'ESTIMATED','Eligible for reviewed ESTIMATED suggestions only; empirical masked-block summaries are not guaranteed intervals and extremes remain sensitive.'])
    w.writerow(['RESTORED proposals emitted',0,'NONE','Lineage and source role remain unverified.'])
(OUT/'weather_mcp_batches.json').write_text(json.dumps({'contract':'Weather MCP insert-only proposal batches; do not submit/apply','max_batch_size':50,'batch_count':1,'batches':[{'batch_id':'p3-v2-estimated-01','size':24,'timestamps':[x['timestamp'] for x in estimates],'episodes':len({(x['source_time'],next(r['right']['t'] for r in META if r['timestamp']==x['timestamp'])) for x in estimates}),'episode_split':False,'dependency_order':'No other variable operations in this batch; any future whole-row/source-restoration operation must be decided before these estimated outTemp inserts.'}]},ensure_ascii=False,indent=2)+'\n')
summary={'target_count':107,'restored':0,'estimated':24,'review_required':83,'missing':0,'source_rows_by_archive':source_counts,'source_outTemp_rows':{'old_weewx':82,'weewx_WH1080':83,'shared_exact_equal':82,'WH1080_only':1},'source_field_ranges':{db:{f:{'min':min(vals),'max':max(vals)} for f,vals in fields.items() if vals} for db,fields in field_ranges.items()},'source_vs_interpolation':{'WH1080_n':83,'WH1080_mean_absolute_difference_c':mean_abs,'WH1080_max_absolute_difference_c':maxrow['source_interpolation_difference_c']['weewx_WH1080_abs'],'max_difference_timestamp':maxrow['timestamp'],'old_WH_shared_exact_match_n':82},'source_neighbor_screen':{'source_rows_with_neighbor_context':len(NEIGH),'zero_current_or_neighbor_outTemp':sum(1 for n in NEIGH if any(n.get(k)==0 for k in ('current_outTemp','previous_outTemp','next_outTemp'))),'max_adjacent_outTemp_step_c':max(abs(float(n['current_outTemp'])-float(n[k])) for n in NEIGH for k in ('previous_outTemp','next_outTemp') if n.get(k) is not None)},'episodes':{'all':len(episode_classes),'source_conflict':sum(next(iter(v)) for v in episode_classes.values()),'source_free_estimated':sum(not next(iter(v)) for v in episode_classes.values()),'mixed_source_presence':0},'uncertainty_by_gap_minutes':uncertainty,'extrema_holdout_by_gap_minutes':extrema,'database_writes':0}
(OUT/'source_availability_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')

(OUT/'README.md').write_text('''# P3 v2 — source-first temperature gap package\n\n**Status:** revised active review package. It supersedes P3 v1 for recommendation purposes; the 107-value v1 remains preserved in the original v1 ZIP and `archives/v1/estimated_short_temperature_gaps/`. Nothing here was applied or staged.\n\nThe exact-time READ-ONLY check covers all 107 target timestamps across six archives and all listed common primary/diagnostic fields. 83 timestamps have an exact original-source `outTemp` row (82 matching old/WH1080 copies, one WH1080-only). Those 83 are `REVIEW_REQUIRED_SOURCE_VS_ESTIMATED_CONFLICT`; no RESTORED values are emitted because database-export role and per-row lineage/unit mapping are not authenticated. Source values differ from linear interpolation by mean absolute 0.588 C across 83 WH1080 observations; the largest discrepancy is 3.8 C at 2019-06-30 15:15 UTC (source 33.4 C, interpolation 29.6 C). Exact shared copies are integrity evidence, not independent truth.\n\nThe remaining 24 targets have no exact archive row in any of the six sources and no reconstruction change event. They form 14 complete episodes with no episode mixing between source-present and source-free targets. After same-endpoint rule checks, only these 24 retain reviewed `ESTIMATED` proposals. Gap durations are 10, 15, 20 or 25 minutes. Conditional 2019–2020 hourly masked holdouts use the same endpoint filters and report conservative upper edges of 0.1 C histogram bins. These are empirical summaries, **not guaranteed prediction intervals**. Holdout samples also show hidden local maxima/minima up to 1.5 C for 15–25 minute masks; do not use these suggestions to assert daily extrema. Fog/inversion and missingness mechanism are not separately validated.\n\nAll 24 operations fit in one Weather MCP batch (max 50) and all 14 episodes remain whole. Batch is a prepared contract only; do not send or apply it. Each insert contains only `outTemp`; other fields stay NULL. Before any later multi-variable operation, source-first review and current-state validation must run again.\n\nCounts for this 107-target scope: **RESTORED 0, ESTIMATED 24, REVIEW_REQUIRED 83, MISSING 0**. Full six-archive values are in `source_availability_107.json` and `per_target_source_evidence.csv`; exact neighboring and offset checks, event history, conditional histograms and uncertainty are included.\n''')

# Package-level validation and metadata accompany the root audit validators.
(OUT/'source_metadata.json').write_text(json.dumps({'query_source':'Weather MCP READ_ONLY SELECT','snapshot_date':'2026-11-13','archives_checked':SRC['source_databases'],'target_timestamps':107,'source_rows_by_archive':source_counts,'public_station_hardware_lineage':'Watson W-8681 station-level history is available; SQL export-to-instrument identity is not established','source_copy_rule':'Exact copy agreement supports integrity, not independent measurement truth'},ensure_ascii=False,indent=2)+'\n')
(OUT/'validation.json').write_text(json.dumps({'source_first_exact_time_review':'PASS','target_state_and_all_variable_change_history':'checked; zero events','neighbor_screen':'165 source rows; no zero current/adjacent outTemp; max adjacent step 1.3 C','source_temperature_plausibility':'4.7..33.4 C; no zero or outside broad -40..50 C screen','conditional_holdout':'2019-2020 same endpoint selection filters; 10/15/20/25 minute complete masks','limitation':'synthetic conditional validation; not independent truth or guarantee for an individual target; rare extremes, fog, inversion and missingness mechanism remain uncertain','extrema':'hidden extrema and errors quantified in conditional_holdout_2019_2020.json; not suitable for daily extrema claims'},ensure_ascii=False,indent=2)+'\n')
(OUT/'uncertainty.json').write_text(json.dumps({'conditional_by_gap_minutes':uncertainty,'extrema_holdout_by_gap_minutes':extrema,'interpretation':'Empirical bin-edge quantiles only; not calibrated or guaranteed prediction intervals for individual proposed values.'},ensure_ascii=False,indent=2)+'\n')
(OUT/'dependency_metadata.json').write_text(json.dumps({'proposal_operations':24,'variables':['outTemp'],'whole_row_inserts':0,'source_restoration_conflicts':83,'ordering':'No whole-row operation or downstream field operation in this package; any future whole-row insert must precede field fills and be rechecked against current target state.','batch_limit':50,'batch_count':1,'episodes':14,'episodes_split':False,'duplicate_scan':'active package registry; zero timestamp duplicates'},ensure_ascii=False,indent=2)+'\n')
(OUT/'validate.py').write_text('''#!/usr/bin/env python3
import csv,json
from pathlib import Path
p=Path(__file__).resolve().parent
m=json.loads((p/'manifest.json').read_text());meta=json.loads((p/'candidate_metadata.json').read_text());ops=json.loads((p/'corrections.json').read_text());review=list(csv.DictReader((p/'review_required.csv').open()))
assert len(meta)==107 and len(ops)==24 and len(review)==83
assert (m['restored_count'],m['estimated_count'],m['review_required_count'],m['missing_count'])==(0,24,83,0)
assert all(x['p3_v2_status']=='ESTIMATED' for x in meta if int(x['timestamp']) in {int(o['timestamp']) for o in ops})
assert all(not any(x['exact_source_rows_by_archive'].values()) for x in meta if x['p3_v2_status']=='ESTIMATED')
assert json.loads((p/'weather_mcp_batches.json').read_text())['batch_count']==1
print('PASS: P3 v2 package counts and source-first gates')
''')
# Deterministic manifest covers every package artifact except itself.
manifest={'package':'estimated_short_temperature_gaps_v2','revision':'v2','priority':'P3','classification':'MIXED_REVIEW_AND_ESTIMATED','target_count':107,'restored_count':0,'estimated_count':24,'review_required_count':83,'missing_count':0,'decision':'V1 107-estimate output superseded; exact source-first results resolve 83 to REVIEW_REQUIRED and retain 24 source-free ESTIMATED proposals pending review.','source_archives':SRC['source_databases'],'batch_limit':50,'batch_count':1,'episode_split':False,'database_access':'READ_ONLY_SELECT_ONLY','writes_or_staging':False,'q1_2018':'excluded','year_2021':'diagnostic_only','artifacts':{}}
for p in sorted(OUT.iterdir()):
    if p.is_file() and p.name!='manifest.json':
        b=p.read_bytes();manifest['artifacts'][p.name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'target_count':107,'restored':0,'estimated':24,'review_required':83,'missing':0,'source_mae_vs_interpolation':round(mean_abs,10),'max_diff_timestamp':maxrow['timestamp'],'episodes':len(episode_classes),'source_free_episodes':14,'source_present_episodes':42},ensure_ascii=False))
