#!/usr/bin/env python3
"""Offline episode review of WH1080 zero outTemp rows in 2016–2017 short gaps."""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/'data/short_gap_source_detail_per_target.json').read_text())['records']
selected=[]
for r in rows:
    if r['utc_year'] not in (2016,2017) or not r['outTemp_exact_zero_source_present']:
        continue
    wh=r['source_archives']['weewx_WH1080'];old=r['source_archives']['old_weewx'];c=r['linear_interpolation_context_c']
    band='NO_ENDPOINT_CONTEXT' if c is None else 'NEAR_ZERO_CONTEXT' if abs(c)<=2 else 'CONTEXT_CONTRAST_GT_5C' if abs(c)>5 else 'INTERMEDIATE_CONTEXT'
    nbs=[v for v in (wh['source_prev_outTemp'],wh['source_next_outTemp']) if v is not None]
    selected.append({'timestamp':r['timestamp'],'utc':r['utc'],'year':r['utc_year'],'month':r['utc'][5:7],
      'gap_id':r['gap_id'],'source_usUnits':wh['usUnits'],'source_interval_min':wh['interval'],
      'old_weewx_outTemp':old['fields']['outTemp'],'wh1080_outTemp':wh['fields']['outTemp'],
      'prev_source_temp':wh['source_prev_outTemp'],'next_source_temp':wh['source_next_outTemp'],
      'nonzero_neighbor_count':sum(v!=0 for v in nbs),'linear_interpolation_context_C':c,'context_band':band,
      'source_pressure':wh['fields']['pressure'],'source_rain':wh['fields']['rain'],'source_rainRate':wh['fields']['rainRate'],
      'source_windSpeed':wh['fields']['windSpeed'],'source_windGust':wh['fields']['windGust'],
      'target_change_events':r['change_event_count'],'disposition':'REVIEW_REQUIRED_SOURCE_SENSOR_STUCK_SUSPECTED' if band=='CONTEXT_CONTRAST_GT_5C' else 'REVIEW_REQUIRED_ZERO_MAY_BE_VALID_OR_SENSOR_FAULT'})
selected.sort(key=lambda x:(x['year'],x['timestamp']))
runs=[]
for r in selected:
    if runs and runs[-1]['gap_id']==r['gap_id'] and r['timestamp']-runs[-1]['end_timestamp']==300:
        e=runs[-1];e['end_timestamp']=r['timestamp'];e['end_utc']=r['utc'];e['n']+=1;e['_rows'].append(r)
    else:runs.append({'year':r['year'],'gap_id':r['gap_id'],'start_timestamp':r['timestamp'],'end_timestamp':r['timestamp'],'start_utc':r['utc'],'end_utc':r['utc'],'n':1,'_rows':[r]})
fields=('rain','rainRate','windSpeed','windGust','pressure')
for e in runs:
 rr=e.pop('_rows');contexts=[x['linear_interpolation_context_C'] for x in rr if x['linear_interpolation_context_C'] is not None]
 e['context_bands']=dict(Counter(x['context_band'] for x in rr));e['context_min_C']=min(contexts) if contexts else None;e['context_max_C']=max(contexts) if contexts else None
 e['other_source_field_variation']={field:len({x['source_'+field] for x in rr if x['source_'+field] is not None})>1 for field in fields}
 e['other_source_fields_vary']=any(e['other_source_field_variation'].values())
summary={}
for y in (2016,2017):
 rr=[x for x in selected if x['year']==y];ee=[x for x in runs if x['year']==y]
 summary[str(y)]={'zero_source_targets':len(rr),'bounded_runs':len(ee),'months_utc':dict(Counter(x['month'] for x in rr)),
  'context_bands':dict(Counter(x['context_band'] for x in rr)),'old_weewx_outTemp_nonnull':sum(x['old_weewx_outTemp'] is not None for x in rr),
  'nonzero_neighbor_targets':sum(x['nonzero_neighbor_count']>0 for x in rr),'runs_with_other_field_variation':sum(e['other_source_fields_vary'] for e in ee),
  'run_lengths':dict(Counter(str(e['n']) for e in ee))}
out={'schema':'b5-short-gap-zero-outtemp-2016-2017-review-v1','input':'data/short_gap_source_detail_per_target.json','database_access':'NONE_FROZEN_LOCAL_SNAPSHOT_ONLY',
 'method':'Group only exact 300-second adjacent candidate rows in the same existing gap. Endpoint-linear temperature is a screening contrast, never ground truth. Check within-run variation in rain, rainRate, windSpeed, windGust and pressure to avoid claiming whole-row freeze.',
 'summary':{'targets':len(selected),'runs':len(runs),'target_change_events':sum(x['target_change_events'] for x in selected),'proposals':0,'by_year':summary},
 'interpretation':'All selected zero outTemp values remain REVIEW_REQUIRED. Rows with >5 C endpoint-linear contrast receive a suspected sensor-quality flag, not confirmed error/deletion. Source temperature is available only in WH1080 for this subset; legacy copies are dependent and do not corroborate. Variation in other fields argues against a blanket whole-row freeze disposition for every run.',
 'records':selected,'runs':runs}
(ROOT/'data/b5_short_gap_zero_outtemp_2016_2017_review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'targets':len(selected),'runs':len(runs),'by_year':summary,'proposals':0},ensure_ascii=False,indent=2))
