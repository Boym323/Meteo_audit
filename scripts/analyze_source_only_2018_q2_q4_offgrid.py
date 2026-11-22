#!/usr/bin/env python3
"""Offline summary of the 2018 Q2-Q4 off-grid source-only screen."""
import csv,json,math
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
raw=json.loads((R/'data/source_only_2018_q2_q4_offgrid_row_screen.json').read_text())
rows=sorted(raw['rows'],key=lambda x:int(x['dateTime']))
interval6=json.loads((R/'data/source_only_2018_q2_q4_interval6_probe.json').read_text())
qdata=json.loads((R/'data/source_only_year_quarter_interval_utc.json').read_text())

def utc(t): return datetime.fromtimestamp(int(t),timezone.utc).isoformat().replace('+00:00','Z')
def quarter(t):
 d=datetime.fromtimestamp(int(t),timezone.utc);return f'{d.year}-Q{(d.month-1)//3+1}'
def compare(a,b,fa=lambda x:x):
 comp=eq=missing=0;diffs=[]
 for r in rows:
  x,y=r.get(a),r.get(b)
  if x is None or y is None:missing+=1;continue
  comp+=1;delta=float(fa(float(x)))-float(y);diffs.append(delta)
  if math.isclose(delta,0,abs_tol=1e-8,rel_tol=0):eq+=1
 return {'compared':comp,'equal':eq,'mismatches':comp-eq,'missing_either':missing,'mae':sum(abs(x) for x in diffs)/comp if comp else None,'max_abs_diff':max((abs(x) for x in diffs),default=None)}
# Per-variable transformed equality among the three timestamp-exact source archives.
lineage={
 'outTemp_C_site16_to_WH17':compare('site_temp','wh_temp'),
 'outHumidity_site16_to_WH17':compare('site_rh','wh_rh'),
 'rain_cm_site16_to_mm_WH17':compare('site_rain','wh_rain',lambda x:x*10),
 'rainRate_cm_h_site16_to_mm_h_WH17':compare('site_rate','wh_rate',lambda x:x*10),
 'wind_kmh_site16_to_ms_WH17':compare('site_wind','wh_wind',lambda x:x/3.6),
}
nearest={
 'outTemp':compare('wh_temp','target_temp'),
 'outHumidity':compare('wh_rh','target_rh'),
 'rain_WH_mm_to_archive16_cm':compare('wh_rain','target_rain',lambda x:x/10),
 'rainRate_WH_mm_h_to_archive16_cm_h':compare('wh_rate','target_rate',lambda x:x/10),
 'wind_WH_ms_to_archive16_kmh':compare('wh_wind','target_wind',lambda x:x*3.6),
}
# Broad value and successive-sample screens (descriptive only).
value_ranges={}
for field in ['wh_temp','wh_rh','wh_rain','wh_rate','wh_wind']:
 vals=[float(x[field]) for x in rows if x[field] is not None]
 value_ranges[field]={'n':len(vals),'min':min(vals) if vals else None,'max':max(vals) if vals else None,'exact_zero_n':sum(v==0 for v in vals)}
consecutive=[]
for a,b in zip(rows,rows[1:]):
 if int(b['dateTime'])-int(a['dateTime'])==300 and a['wh_temp'] is not None and b['wh_temp'] is not None:
  consecutive.append(abs(float(b['wh_temp'])-float(a['wh_temp'])))
neighbor_delta={'consecutive_300s_pairs':len(consecutive),'max_abs_step_c':max(consecutive,default=None),'pairs_gt_2c':sum(x>2 for x in consecutive),'pairs_gt_5c':sum(x>5 for x in consecutive)}
# UTC quarter / offset profiles and constant-offset contiguous source episodes.
qcounts=Counter(quarter(x['dateTime']) for x in rows)
offsets=defaultdict(list)
for r in rows: offsets[int(r['offset_to_nearest_300'])].append(r)
offrows=[]
for off,rs in sorted(offsets.items()):
 offrows.append({'offset_seconds':off,'rows':len(rs),'first_utc':utc(rs[0]['dateTime']),'last_utc':utc(rs[-1]['dateTime']),'quarters':dict(Counter(quarter(x['dateTime']) for x in rs))})
runs=[];cur=[]
for r in rows:
 if cur and (int(r['dateTime'])-int(cur[-1]['dateTime'])!=300 or int(r['offset_to_nearest_300'])!=int(cur[-1]['offset_to_nearest_300'])):
  runs.append(cur);cur=[]
 cur.append(r)
if cur:runs.append(cur)
episodes=[]
for i,run in enumerate(runs,1):
 episodes.append({'episode':i,'n':len(run),'offset_seconds':int(run[0]['offset_to_nearest_300']),'start_utc':utc(run[0]['dateTime']),'end_utc':utc(run[-1]['dateTime']),'quarter':quarter(run[0]['dateTime'])})
collisions=Counter(int(x['nearest_300']) for x in rows)
q2018={x['utc_year_quarter']:sum(int(g['timestamps']) for g in qdata['groups'] if g['utc_year_quarter']==x['utc_year_quarter']) for x in qdata['groups'] if x['utc_year_quarter'].startswith('2018-')}
summary={
 'scope':'UTC 2018 Q2-Q4; source exact time absent from reconstruction; WH1080 interval=5/usUnits=17; separate interval-6 case included below',
 'rows_5min':len(rows),'utc_quarter_counts':dict(qcounts),'source_time_range_utc':[utc(rows[0]['dateTime']),utc(rows[-1]['dateTime'])],
 'third_archive_exact_rows':sum(x['site_units'] is not None for x in rows),
 'units':{'WH1080':dict(Counter(str(x['wh_units']) for x in rows)),'old_weewx':dict(Counter(str(x['old_units']) for x in rows)),'site_old':dict(Counter(str(x['site_units']) for x in rows))},
 'unit_converted_exact_copy_agreement':lineage,'broad_source_value_ranges':value_ranges,'source_300s_temperature_steps':neighbor_delta,
 'offset_to_nearest_300':offrows,
 'nearest_reconstruction_target_rows_present':sum(x['nearest_target_time'] is not None for x in rows),
 'distinct_nearest_target_slots':len(collisions),'nearest_slot_collision_count':sum(v>1 for v in collisions.values()),
 'nearest_target_units':dict(Counter(str(x['target_units']) for x in rows)),
 'nearest_target_interval':dict(Counter(str(x['target_interval']) for x in rows)),
 'source_to_nearest_target_concordance_after_units':nearest,
 'constant_offset_contiguous_episodes':len(episodes),'longest_constant_offset_episode':max(episodes,key=lambda x:x['n']),
 'all_constant_offset_episodes':episodes,
 'utc_2018_quarter_source_only_counts':q2018,
 'q1_2018_protected':True,'2021_included':False,'restored':0,'estimated':0,'review_required':len(rows)+1,
 'interval6_case':interval6
}
(R/'data/source_only_2018_q2_q4_offgrid_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
with (R/'reports/2026-11-13-source-only-2018-q2-q4-offgrid-offsets.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['offset_seconds','rows','first_utc','last_utc','quarters']);w.writeheader()
 for x in offrows:w.writerow({**x,'quarters':json.dumps(x['quarters'],sort_keys=True)})
with (R/'reports/2026-11-13-source-only-2018-q2-q4-offgrid-episodes.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['episode','n','offset_seconds','start_utc','end_utc','quarter']);w.writeheader();w.writerows(episodes)
print(json.dumps({k:summary[k] for k in ['rows_5min','utc_quarter_counts','source_time_range_utc','unit_converted_exact_copy_agreement','nearest_reconstruction_target_rows_present','distinct_nearest_target_slots','nearest_slot_collision_count','source_to_nearest_target_concordance_after_units','constant_offset_contiguous_episodes','longest_constant_offset_episode','utc_2018_quarter_source_only_counts']},indent=2,ensure_ascii=False))
