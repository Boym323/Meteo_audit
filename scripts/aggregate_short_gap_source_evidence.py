#!/usr/bin/env python3
"""Create per-target source-first evidence from bounded short-gap MCP extracts."""
from __future__ import annotations
import csv,hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
idx=json.loads((R/'data/short_gap_source_detail_query_index.json').read_text())
fields=idx['fields']; all_rows=[]; missing=[]
for q in idx['chunks']:
 p=R/f"data/short_gap_source_detail_results_{q['chunk']:03d}.json"
 if not p.is_file(): missing.append(q['chunk']);continue
 doc=json.loads(p.read_text())
 if 'error_code' in doc: raise ValueError(f'query error in chunk {q["chunk"]}')
 all_rows.extend(doc['result'])
exact_index=json.loads((R/'data/exact_hour_source_detail_query_index.json').read_text())
exact_files=sorted((R/'data').glob('exact_hour_source_detail_results_*.json'))
if len(exact_files)!=len(exact_index['chunks']):raise ValueError('missing exact-hour detail results')
for p in exact_files:
 doc=json.loads(p.read_text())
 if 'error_code' in doc:raise ValueError(f'exact-hour query error in {p.name}')
 all_rows.extend(doc['result'])
if missing: raise ValueError(f'missing result chunks: {missing}')
source_db={'old_weewx','weewx_WH1080','pocasi-loucka.eu_old','pocasi-loucka.eu','pocasi-loucka.eu_GW1000'}
by_target=defaultdict(dict)
for r in all_rows:
 if r['source_database'] not in source_db:raise ValueError(f'unexpected source hit {r["source_database"]}')
 if int(r['gap_seconds'])>3600 or int(r['gap_seconds'])<=300:raise ValueError('out-of-scope gap duration')
 if r['protection_scope']=='PROTECTED_Q1_2018_DIAGNOSTIC' and not 1514764800<=int(r['target_time'])<1522540800:raise ValueError('bad Q1 label')
 t=int(r['target_time']);db=r['source_database']
 if db in by_target[t]:raise ValueError(f'duplicate source row {t} {db}')
 by_target[t][db]=r
if len(all_rows)!=11163:raise ValueError(f'query row count changed: {len(all_rows)}')
# P3 source-first candidate states, for exact overlap with existing v2.
p3_source={}
with (R/'proposals/estimated_short_temperature_gaps_v2/per_target_source_evidence.csv').open(newline='',encoding='utf-8') as f:
 for r in csv.DictReader(f):p3_source[int(r['timestamp'])]=r['p3_v2_status']
episodes=defaultdict(list);out=[];source_counts=Counter();field_pair=Counter();unit_counter=Counter();history=Counter();flags=Counter();abs_interp=[];abs_interp_nonzero=defaultdict(list);temp_state=Counter();episode_extrema=[]
def num(v):
 try:return None if v is None else float(v)
 except (ValueError,TypeError):return None
for t,sources in sorted(by_target.items()):
 exemplar=next(iter(sources.values()));left=int(exemplar['gap_id'].split(':')[1]);right=int(exemplar['gap_id'].split(':')[2]);duration=int(exemplar['gap_seconds'])
 source_counts[len(sources)]+=1
 rec={'timestamp':t,'utc':datetime.fromtimestamp(t,timezone.utc).isoformat(),'utc_year':datetime.fromtimestamp(t,timezone.utc).year,'gap_id':exemplar['gap_id'],'gap_seconds':duration,'left_endpoint':left,'right_endpoint':right,'protection_scope':exemplar['protection_scope'],'target_row_state':'MISSING_FROM_RECONSTRUCTION_AT_QUERY_TIME','change_event_count':int(exemplar['change_event_count']),'change_event_counts_by_variable':{'outTemp':int(exemplar['outTemp_change_event_count']),'outHumidity':int(exemplar['outHumidity_change_event_count']),'rain':int(exemplar['rain_change_event_count'])},'p3_v2_disposition':p3_source.get(t),'source_archives':{},'disposition':'REVIEW_REQUIRED_SOURCE_LINEAGE_AND_SENSOR_EPOCH_UNPROVEN','source_copies_independent':False}
 history['target_rows_checked']+=1;history['events_found']+=rec['change_event_count']
 vals={}
 for db,r in sorted(sources.items()):
  row={'source_database':db,'usUnits':int(r['source_usUnits']) if r['source_usUnits'] is not None else None,'interval':int(r['source_interval']) if r['source_interval'] is not None else None,'fields':{f:r.get(f) for f in fields},'source_prev_time':r['source_prev_time'],'source_prev_outTemp':r['source_prev_outTemp'],'source_next_time':r['source_next_time'],'source_next_outTemp':r['source_next_outTemp'],'source_time_matches_target':True}
  rec['source_archives'][db]=row;vals[db]=row['fields']
  unit_counter[(db,row['usUnits'],row['interval'])]+=1
  tv=num(row['fields'].get('outTemp'))
  if tv is not None:
   temp_state[(rec['utc_year'],db,'zero' if tv==0 else 'nonzero')]+=1
   if not -50<=tv<=60:flags['outTemp_outside_broad_physical_range']+=1
   if tv==0:flags['outTemp_exact_zero_review']+=1
   prev=num(row['source_prev_outTemp']);nxt=num(row['source_next_outTemp'])
   if prev is not None and abs(tv-prev)>5:flags['outTemp_jump_gt_5C_vs_previous_source_row']+=1
   if nxt is not None and abs(tv-nxt)>5:flags['outTemp_jump_gt_5C_vs_next_source_row']+=1
   interp=None
   lo=num(r['left_outTemp']);hi=num(r['right_outTemp'])
   if lo is not None and hi is not None and right>left:
    interp=lo+(hi-lo)*(t-left)/(right-left)
    abs_interp.append(abs(tv-interp))
    if tv!=0:abs_interp_nonzero[rec['utc_year']].append(abs(tv-interp))
  for field,lo,hi in [('outHumidity',0,100),('rain',0,None),('rainRate',0,None),('windSpeed',0,None)]:
   v=num(row['fields'].get(field))
   if v is not None and ((lo is not None and v<lo) or (hi is not None and v>hi)):flags[f'{field}_outside_broad_physical_range']+=1
 if 'old_weewx' in vals and 'weewx_WH1080' in vals:
  for f in fields:
   a=num(vals['old_weewx'].get(f));b=num(vals['weewx_WH1080'].get(f))
   if a is None and b is None:field_pair[(f,'both_null')]+=1
   elif a is None or b is None:field_pair[(f,'one_null')]+=1
   else:field_pair[(f,'both_nonnull')]+=1;field_pair[(f,'exact_agreement' if math.isclose(a,b,rel_tol=0,abs_tol=1e-9) else 'difference')]+=1
 temp_sources=[num(v.get('outTemp')) for v in vals.values()]
 temp_sources=[v for v in temp_sources if v is not None]
 rec['outTemp_source_values_present']=bool(temp_sources)
 rec['outTemp_exact_zero_source_present']=any(v==0 for v in temp_sources)
 rec['outTemp_nonzero_source_values_count']=sum(v!=0 for v in temp_sources)
 rec['disposition']='REVIEW_REQUIRED_SOURCE_VS_ESTIMATED' if temp_sources else 'SOURCE_ROW_WITHOUT_OUTTEMP_VALUE'
 # Temp interpolation and extrema inputs from source measurement and fixed linear endpoint interpolation.
 example=next(iter(sources.values()));lo=num(example['left_outTemp']);hi=num(example['right_outTemp'])
 if lo is not None and hi is not None and right>left:
  interp=lo+(hi-lo)*(t-left)/(right-left)
  source_temp_values=[num(v['fields'].get('outTemp')) for v in rec['source_archives'].values()]
  source_temp_values=[v for v in source_temp_values if v is not None and v!=0]
  source_temp_values=[v for v in source_temp_values if v is not None]
  episodes[rec['gap_id']].append({'timestamp':t,'interp':interp,'source_temps':source_temp_values})
 rec['linear_interpolation_context_c']=None if lo is None or hi is None else lo+(hi-lo)*(t-left)/(right-left)
 rec['source_minus_interpolation_c']={db:(None if num(v['fields'].get('outTemp')) is None or rec['linear_interpolation_context_c'] is None else num(v['fields'].get('outTemp'))-rec['linear_interpolation_context_c']) for db,v in rec['source_archives'].items()}
 out.append(rec)
for gid,pts in episodes.items():
 src=[x for p in pts for x in p['source_temps']]
 interp=[p['interp'] for p in pts]
 if src and interp:episode_extrema.append({'gap_id':gid,'covered_target_count':len(pts),'source_min':min(src),'source_max':max(src),'linear_min':min(interp),'linear_max':max(interp),'min_abs_difference':abs(min(src)-min(interp)),'max_abs_difference':abs(max(src)-max(interp))})
def quantile(v,p):
 if not v:return None
 v=sorted(v);x=(len(v)-1)*p;lo=math.floor(x);hi=math.ceil(x)
 return v[lo] if lo==hi else v[lo]+(v[hi]-v[lo])*(x-lo)
# target summaries and cross-check with aggregate archive-level counts
counts_by_year=Counter();p3_overlap=Counter();temp_source_count=Counter();pair_temp=Counter();interps=[]
for rec in out:
 counts_by_year[rec['utc_year']]+=1
 if rec['p3_v2_disposition']:p3_overlap[rec['p3_v2_disposition']]+=1
 for db,row in rec['source_archives'].items():
  if num(row['fields'].get('outTemp')) is not None:temp_source_count[db]+=1
 a=num(rec['source_archives'].get('old_weewx',{}).get('fields',{}).get('outTemp'));b=num(rec['source_archives'].get('weewx_WH1080',{}).get('fields',{}).get('outTemp'))
 if a is not None and b is not None:pair_temp['both']+=1;pair_temp['exact' if math.isclose(a,b,abs_tol=1e-9) else 'different']+=1
 elif a is not None or b is not None:pair_temp['one']+=1
json_path=R/'data/short_gap_source_detail_per_target.json'
json_path.write_text(json.dumps({'metadata':{'candidate_target_timestamps_with_source':len(out),'source_archive_rows':len(all_rows),'protected_q1_2018_targets':sum(x['protection_scope']=='PROTECTED_Q1_2018_DIAGNOSTIC' for x in out),'source_role_identity':'not authenticated row-by-row; source archive copies are dependent','coverage':'delta < 1h plus exact 1h boundary; conditional 300-second interior points only'},'records':out},ensure_ascii=False,separators=(',',':'))+'\n')
csv_path=R/'reports/2026-11-13-short-gap-source-detail.csv'
cols=['timestamp','utc','utc_year','gap_id','gap_seconds','protection_scope','target_row_state','change_event_count','p3_v2_disposition','disposition','linear_interpolation_context_c','source_minus_interpolation_c','source_archives_json']
with csv_path.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for r in out:w.writerow({**{k:r.get(k) for k in cols if k not in {'source_archives_json'}},'source_archives_json':json.dumps(r['source_archives'],ensure_ascii=False,separators=(',',':'))})
summary={'query_chunks':len(idx['chunks'])+len(exact_index['chunks']),'candidate_time_slots_checked':idx['candidate_targets']+exact_index['candidate_targets'],'source_archive_rows_returned':len(all_rows),'target_timestamps_with_source':len(out),'targets_with_any_outTemp_zero':sum(r['outTemp_exact_zero_source_present'] for r in out),'targets_with_nonzero_outTemp_source':sum(r['outTemp_nonzero_source_values_count']>0 for r in out),'targets_by_year':dict(sorted(counts_by_year.items())),'targets_by_source_archive_count':dict(sorted(source_counts.items())),'source_rows_by_database':dict(Counter(r['source_database'] for r in all_rows)),'source_unit_interval_counts':{f'{db}|usUnits={u}|interval={iv}':n for (db,u,iv),n in unit_counter.items()},'outTemp_nonnull_by_database':dict(temp_source_count),'paired_outTemp_concordance':dict(pair_temp),'paired_field_concordance':{f:{k:v for (ff,k),v in field_pair.items() if ff==f} for f in fields if any(ff==f for ff,_ in field_pair)},'outTemp_zero_nonzero_by_year_archive':{f'{y}|{db}':{'zero':temp_state[(y,db,'zero')],'nonzero':temp_state[(y,db,'nonzero')]} for y,db,_ in temp_state},'history_event_counts':dict(history),'broad_physical_or_neighbor_flags':dict(flags),'p3_v2_overlap':dict(p3_overlap),'source_minus_interpolation_abs_error_c_all_including_suspect_zeros':{'n':len(abs_interp),'median':quantile(abs_interp,.5),'p90':quantile(abs_interp,.9),'p95':quantile(abs_interp,.95),'max':max(abs_interp) if abs_interp else None},'source_minus_interpolation_abs_error_c_nonzero_source_only_by_year':{str(y):{'n':len(v),'median':quantile(v,.5),'p90':quantile(v,.9),'p95':quantile(v,.95),'max':max(v)} for y,v in sorted(abs_interp_nonzero.items())},'episode_extrema_nonzero_source_subset':{'episodes':len(episode_extrema),'median_abs_max_difference_c':quantile([x['max_abs_difference'] for x in episode_extrema],.5),'p95_abs_max_difference_c':quantile([x['max_abs_difference'] for x in episode_extrema],.95),'max_abs_max_difference_c':max((x['max_abs_difference'] for x in episode_extrema),default=None),'median_abs_min_difference_c':quantile([x['min_abs_difference'] for x in episode_extrema],.5),'p95_abs_min_difference_c':quantile([x['min_abs_difference'] for x in episode_extrema],.95),'max_abs_min_difference_c':max((x['min_abs_difference'] for x in episode_extrema),default=None)},'operation_class_counts':{'RESTORED':0,'ESTIMATED':0,'REVIEW_REQUIRED':len(out),'MISSING':0,'UNCLASSIFIED_CANDIDATE_SLOTS_WITHOUT_SOURCE_EVIDENCE':idx['candidate_targets']+exact_index['candidate_targets']-len(out)},'files':{'detail_json':str(json_path.relative_to(R)),'detail_csv':str(csv_path.relative_to(R))},'interpretation':'All source rows remain REVIEW_REQUIRED until historical source role, physical sensor identity/epoch, unit mapping, target history and value plausibility are established. Repeated exact-zero series are explicitly flagged for review, not assumed invalid or restored. Source copies are dependent. Interpolation differences/extrema are descriptive comparisons to unverified source rows; they are not independent truth or prediction intervals. Q1 2018 diagnostic only; no 2021 targets.'}
(R/'data/short_gap_source_detail_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-13-short-gap-source-detail-summary.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['metric','value']);
 for k,v in summary.items():w.writerow([k,json.dumps(v,ensure_ascii=False,separators=(',',':'))])
report=['# Source-first row detail for short temperature gaps (2009–2020)','', '## Scope and classification','',f"The frozen gap-event catalog contributed {summary['candidate_time_slots_checked']:,} conditional interior targets with event duration below or equal to one hour (29,260 with delta < 3,600 s plus 671 exactly 3,600 s). They were checked by exact timestamp against all six archives in {summary['query_chunks']} bounded read-only queries. A query emitted source evidence only when the target was absent from the current reconstruction archive and an exact-time source row existed. This does not establish that every conditional slot was expected.",'',f"There are {summary['target_timestamps_with_source']:,} source-covered missing target timestamps with {summary['source_archive_rows_returned']:,} archive rows. Each target remains `REVIEW_REQUIRED`; RESTORED=0 and ESTIMATED=0 in this screening. The other {summary['operation_class_counts']['UNCLASSIFIED_CANDIDATE_SLOTS_WITHOUT_SOURCE_EVIDENCE']:,} conditional slots were not emitted as source evidence and remain unclassified here (not a conclusion that they should be filled). No `MISSING` correction operations were created. Q1 2018 is diagnostic/protected; 2021 was excluded.",'', 'Source archives `old_weewx` and `weewx_WH1080` report `usUnits=17`, `interval=5` for every returned row. Their dependency/physical sensor identity remains unproven. The two archive copies do not count as independent observations. `reconstruction_changes` had zero events across all 5,588 returned target timestamps; each current reconstruction target row was absent at query time.', '', '## Temperature source conflict and zero-series flag','',f"The WH1080 archive has a non-NULL outTemp value at all {summary['target_timestamps_with_source']:,} source-covered timestamps. At {summary['targets_with_any_outTemp_zero']:,} timestamps the available source outTemp is exactly 0 °C and no nonzero copy is available. Of these, {sum(v['zero'] for k,v in summary['outTemp_zero_nonzero_by_year_archive'].items() if k.split('|')[0] in {'2014','2015','2016','2017','2018'} and k.endswith('weewx_WH1080')):,} occur in 2014–2018. Ten additional 2017 old_weewx rows also contain zero and agree with WH1080. Repeated zeros and large neighboring jumps require sentinel/export and sensor review; an exact 0 °C can still be a real observation and is not automatically invalidated.",'',f"Only {summary['targets_with_nonzero_outTemp_source']:,} target timestamps have a nonzero temperature source: 22 in 2019 and 150 in 2020. Both archives have non-NULL temperatures at 169 matching timestamps, and all 169 are numerically identical. Thirteen further WH1080 timestamps have no corresponding old_weewx row. The 2019–2020 source-vs-linear-interpolation differences are descriptive only: {summary['source_minus_interpolation_abs_error_c_nonzero_source_only_by_year'].get('2019')} (2019) and {summary['source_minus_interpolation_abs_error_c_nonzero_source_only_by_year'].get('2020')} (2020); these source rows are not authenticated independent truth and these summaries are not prediction intervals.",'', '## Multi-variable source-copy comparison','', '| Field | Both non-NULL | Exact matches | Differences | One NULL | Both NULL |','|---|---:|---:|---:|---:|---:|']
for f in ['outTemp','outHumidity','rain','rainRate','barometer','pressure','altimeter','inTemp','inHumidity','windSpeed','windDir','windGust','windGustDir','dewpoint','windchill','heatindex']:
 v=summary['paired_field_concordance'].get(f,{})
 report.append(f"| `{f}` | {v.get('both_nonnull',0)} | {v.get('exact_agreement',0)} | {v.get('difference',0)} | {v.get('one_null',0)} | {v.get('both_null',0)} |")
report += ['', 'Rain and rainRate concordance is only a copy-integrity result; it does not resolve counter semantics, source lineage, or unit conversion. The altimeter disagreement is a distinct source conflict. Do not transfer all fields from a source row as an atomic approved record.', '', '## P3 v2 overlap and episode extrema','',f"All 83 P3 v2 source-conflict targets occur in this ≤1h source detail, including the exact one-hour boundary. They remain `REVIEW_REQUIRED_SOURCE_VS_ESTIMATED`; no P3 v2 operation changed. The 24 source-free P3 v2 ESTIMATED targets remain source-free in the prior exact six-archive P3 check. The 78 source-covered episodes with nonzero temperatures show descriptive observed-subset extrema differences versus linear interpolation: p95/max absolute maximum difference {summary['episode_extrema_nonzero_source_subset']['p95_abs_max_difference_c']:.3f}/{summary['episode_extrema_nonzero_source_subset']['max_abs_max_difference_c']:.3f} °C; p95/max absolute minimum difference {summary['episode_extrema_nonzero_source_subset']['p95_abs_min_difference_c']:.3f}/{summary['episode_extrema_nonzero_source_subset']['max_abs_min_difference_c']:.3f} °C. Each comparison uses only target slots with nonzero source temperatures, not the complete weather episode. This is not validation truth or a guaranteed uncertainty interval.",'', '## Required review and outputs','', 'The exact-zero source series and the source-vs-interpolation cases are registered under ER-33. Restore/estimate choice stays blocked only for affected timestamps; independent packages remain unaffected. Raw-source values are preserved in `data/short_gap_source_detail_per_target.json` and a flat one-row-per-target CSV with nested source details in `reports/2026-11-13-short-gap-source-detail.csv`. Aggregate metrics: `data/short_gap_source_detail_summary.json` and `reports/2026-11-13-short-gap-source-detail-summary.csv`.', '', 'Reproduction: generate sub-hour queries using `python3 scripts/build_short_gap_source_detail_sql.py`; generate exact-hour-boundary queries using `python3 scripts/build_short_gap_source_detail_sql.py --exact-hour`; execute the generated SQL files through read-only Weather MCP (`loucka_reconstruction`), save result JSON to the matching names under `data/`, then run `python3 scripts/aggregate_short_gap_source_evidence.py` and its deterministic validator. No database write, correction, staging operation, or publication occurred.','']
(R/'reports/2026-11-13-short-gap-source-detail.md').write_text('\n'.join(report),encoding='utf-8')
print(json.dumps({k:summary[k] for k in ['query_chunks','candidate_time_slots_checked','source_archive_rows_returned','target_timestamps_with_source','targets_by_source_archive_count','outTemp_nonnull_by_database','paired_outTemp_concordance','outTemp_zero_nonzero_by_year_archive','history_event_counts','p3_v2_overlap','source_minus_interpolation_abs_error_c_nonzero_source_only_by_year','episode_extrema_nonzero_source_subset']},indent=2))
