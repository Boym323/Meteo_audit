#!/usr/bin/env python3
"""Episode-level descriptive review of zero outTemp source rows in 2014–2015.
Uses the frozen short-gap source evidence only; does not access any database.
"""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'data/short_gap_source_detail_per_target.json'
OUT=ROOT/'data/b5_short_gap_zero_outtemp_2014_2015_review.json'
rows=json.loads(IN.read_text())['records']
selected=[]
for r in rows:
    if r['utc_year'] not in (2014,2015) or not r['outTemp_exact_zero_source_present']:
        continue
    wh=r['source_archives']['weewx_WH1080']
    old=r['source_archives']['old_weewx']
    c=r['linear_interpolation_context_c']
    if c is None: band='NO_ENDPOINT_CONTEXT'
    elif abs(c)<=2: band='NEAR_ZERO_INTERPOLATION_CONTEXT'
    elif abs(c)>5: band='WARM_OR_COLD_INTERPOLATION_CONTRAST_GT_5C'
    else: band='INTERMEDIATE_INTERPOLATION_CONTEXT'
    neighbors=[x for x in (wh['source_prev_outTemp'],wh['source_next_outTemp']) if x is not None]
    selected.append({
      'timestamp':r['timestamp'],'utc':r['utc'],'year':r['utc_year'],'month':r['utc'][5:7],
      'gap_id':r['gap_id'],'gap_seconds':r['gap_seconds'],'source_units':wh['usUnits'],
      'source_interval_min':wh['interval'],'old_weewx_outTemp':old['fields']['outTemp'],
      'wh1080_outTemp':wh['fields']['outTemp'],'previous_source_time':wh['source_prev_time'],
      'previous_source_outTemp':wh['source_prev_outTemp'],'next_source_time':wh['source_next_time'],
      'next_source_outTemp':wh['source_next_outTemp'],'neighbor_nonzero_count':sum(x!=0 for x in neighbors),
      'neighbor_count':len(neighbors),'interpolation_context_C':c,'context_band':band,
      'target_change_events':r['change_event_count'],'target_exact_row_absent':r['target_row_state']=='MISSING_FROM_RECONSTRUCTION_AT_QUERY_TIME',
      'interpretation':'SOURCE_SENSOR_STUCK_SUSPECTED' if band=='WARM_OR_COLD_INTERPOLATION_CONTRAST_GT_5C' else 'REVIEW_REQUIRED_POSSIBLY_VALID_ZERO_OR_SENSOR_FAULT'
    })
selected.sort(key=lambda x:(x['year'],x['timestamp']))
runs=[]
for r in selected:
    if runs and r['gap_id']==runs[-1]['gap_id'] and r['timestamp']-runs[-1]['end_timestamp']==300:
        e=runs[-1];e['end_timestamp']=r['timestamp'];e['end_utc']=r['utc'];e['n']+=1
        e['_rows'].append(r)
    else:
        runs.append({'year':r['year'],'gap_id':r['gap_id'],'start_timestamp':r['timestamp'],'end_timestamp':r['timestamp'],'start_utc':r['utc'],'end_utc':r['utc'],'n':1,'_rows':[r]})
for e in runs:
    rr=e.pop('_rows');contexts=[x['interpolation_context_C'] for x in rr if x['interpolation_context_C'] is not None]
    e['context_min_C']=min(contexts) if contexts else None;e['context_max_C']=max(contexts) if contexts else None
    e['context_bands']=dict(Counter(x['context_band'] for x in rr))
    e['neighbor_nonzero_observations']=sum(x['neighbor_nonzero_count'] for x in rr)
by_year={}
for year in (2014,2015):
    rr=[x for x in selected if x['year']==year]; yy=[x for x in rr if x['interpolation_context_C'] is not None]
    by_year[str(year)]={'zero_targets':len(rr),'months':dict(Counter(x['month'] for x in rr)),
      'old_weewx_exact_outTemp_nonnull':sum(x['old_weewx_outTemp'] is not None for x in rr),
      'unit_interval':dict(Counter(f"{x['source_units']}/{x['source_interval_min']}" for x in rr)),
      'context_band_counts':dict(Counter(x['context_band'] for x in rr)),
      'runs':sum(e['year']==year for e in runs),'run_length_counts':dict(Counter(str(e['n']) for e in runs if e['year']==year)),
      'source_neighbors_with_nonzero_value':sum(x['neighbor_nonzero_count']>0 for x in rr),
      'source_neighbors_both_zero_or_missing':sum(x['neighbor_nonzero_count']==0 for x in rr),
      'mean_abs_source_zero_vs_interpolation_C':sum(abs(x['interpolation_context_C']) for x in yy)/len(yy) if yy else None}
out={'schema':'b5-short-gap-zero-outtemp-2014-2015-episode-review-v1','input':'data/short_gap_source_detail_per_target.json','source_access':'FROZEN_LOCAL_SNAPSHOT_ONLY; no database access','method':'Exact-zero source rows grouped into runs only when adjacent 300-second timestamps share the same frozen gap_id. Linear interpolation is used only as a context flag; it is not truth.','summary':{'rows':len(selected),'episodes':len(runs),'by_year':by_year,'target_change_events':sum(x['target_change_events'] for x in selected),'proposals_created':0},'decision':'2014 warm-context zero observations are SOURCE_SENSOR_STUCK_SUSPECTED and remain REVIEW_REQUIRED; 2015 is mixed and is classified row/episode-wise for review. No source value is restored or automatically discarded. Exact copied archives are dependent; interpolation context does not prove historical removal or local truth.','records':selected,'episodes':runs}
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'output':str(OUT),'rows':len(selected),'episodes':len(runs),'by_year':by_year,'proposals':0},ensure_ascii=False,indent=2))
