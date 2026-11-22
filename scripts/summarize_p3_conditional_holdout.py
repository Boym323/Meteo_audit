#!/usr/bin/env python3
"""Summarize conditional P3 masked holdout histograms into conservative bin bounds."""
import csv,json,math
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
data=json.loads((R/'data/p3_independent_review/conditional_holdout_2019_2020.json').read_text())
ext={int(x['gap_minutes']):x['rows'] for x in data['extrema']}
rows=[]
def uq(h,p):
 n=sum(h.values());target=math.ceil(n*p);c=0
 for b,v in sorted(h.items()):
  c+=v
  if c>=target:return round(b+0.1,1)
for g in data['histograms']:
 pooled=Counter(); n_ep=0; byyear={}
 for y,x in g['years'].items():
  h={float(b):int(n) for b,n in x['histogram']};pooled.update(h);n_ep+=int(x.get('episodes',0))
  byyear[y]={'episodes':int(x.get('episodes',0)),'points':int(x.get('points',sum(h.values())))}
 ep=ext[int(g['gap_minutes'])]
 for y,x in byyear.items():
  er=next(z for z in ep if int(z['utc_year'])==int(y))
  rows.append({'gap_minutes':int(g['gap_minutes']),'utc_year':int(y),'episodes':x['episodes'],'point_errors':x['points'],'pooled_p50_abs_error_upper_bin_c':None,'pooled_p90_abs_error_upper_bin_c':None,'pooled_p95_abs_error_upper_bin_c':None,'pooled_sample_max_abs_error_upper_bin_c':None,'episodes_hidden_max':int(er['episodes_hidden_max']),'episodes_hidden_min':int(er['episodes_hidden_min']),'max_hidden_max_error_c':float(er['max_hidden_max_error_c']),'max_hidden_min_error_c':float(er['max_hidden_min_error_c'])})
 summary={'gap_minutes':int(g['gap_minutes']),'episodes':n_ep,'point_errors':sum(pooled.values()),'p50_abs_error_upper_bin_c':uq(pooled,.5),'p90_abs_error_upper_bin_c':uq(pooled,.9),'p95_abs_error_upper_bin_c':uq(pooled,.95),'sample_max_abs_error_upper_bin_c':round(max(pooled)+.1,1), 'max_hidden_max_error_c':max(float(x['max_hidden_max_error_c']) for x in ep),'max_hidden_min_error_c':max(float(x['max_hidden_min_error_c']) for x in ep),'episodes_hidden_max':sum(int(x['episodes_hidden_max']) for x in ep),'episodes_hidden_min':sum(int(x['episodes_hidden_min']) for x in ep)}
 for row in rows[-len(byyear):]:
  row.update({'pooled_p50_abs_error_upper_bin_c':summary['p50_abs_error_upper_bin_c'],'pooled_p90_abs_error_upper_bin_c':summary['p90_abs_error_upper_bin_c'],'pooled_p95_abs_error_upper_bin_c':summary['p95_abs_error_upper_bin_c'],'pooled_sample_max_abs_error_upper_bin_c':summary['sample_max_abs_error_upper_bin_c']})
 summary['yearly']=byyear
 summary.setdefault('_all',[]).append(summary.copy())
# remove internal grouping wrapper
summaries=[]
for r in rows:
 pass
# One summary row per gap for correction metadata and a per-year evidence CSV.
bygap={}
for r in rows:
 g=r['gap_minutes'];bygap.setdefault(g,[]).append(r)
summary_rows=[]
for g,rs in bygap.items():
 r=rs[0]
 summary_rows.append({k:r[k] for k in ('gap_minutes','pooled_p50_abs_error_upper_bin_c','pooled_p90_abs_error_upper_bin_c','pooled_p95_abs_error_upper_bin_c','pooled_sample_max_abs_error_upper_bin_c')})
 summary_rows[-1].update({'total_episodes':sum(x['episodes'] for x in rs),'total_point_errors':sum(x['point_errors'] for x in rs),'episodes_hidden_max':sum(x['episodes_hidden_max'] for x in rs),'episodes_hidden_min':sum(x['episodes_hidden_min'] for x in rs),'max_hidden_max_error_c':max(x['max_hidden_max_error_c'] for x in rs),'max_hidden_min_error_c':max(x['max_hidden_min_error_c'] for x in rs)})
for f,rr in [(R/'reports/2026-11-13-p3-conditioned-short-gap-holdout.csv',rows),(R/'reports/2026-11-13-p3-conditioned-short-gap-holdout-summary.csv',summary_rows)]:
 with f.open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
md=['# P3 conditional short-gap holdout — 2019–2020','',
'Hourly deterministic anchors and exact complete target blocks were screened with the actual P3 endpoint filters: 5-minute interval/usUnits=16; endpoint temperature >0 and ≤35 °C; RH 20–95%; zero rain/rainRate; wind ≥5 km/h; endpoint |ΔT|≤2 °C; no outTemp history at endpoints or held-out points. Target block lengths are restricted to durations actually present in P3 v2 (10, 15, 20, 25 minutes).',
'', 'Absolute errors are summarized in 0.1 °C histogram bins. Reported p50/p90/p95 values use the upper edge of the empirical bin and are screening summaries, **not guaranteed or calibrated predictive intervals**. The deterministic hourly masks are dependent and do not reproduce MNAR missingness. Fog/inversion and rare extreme regimes are not separately identified.', '', '| Gap | Episodes | Point errors | p50 upper bin | p90 upper bin | p95 upper bin | Sample max upper bin | Hidden-max episodes | Hidden-min episodes | Worst hidden max/min |','|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for x in summary_rows:
 md.append(f"| {x['gap_minutes']} min | {x['total_episodes']} | {x['total_point_errors']} | {x['pooled_p50_abs_error_upper_bin_c']} °C | {x['pooled_p90_abs_error_upper_bin_c']} °C | {x['pooled_p95_abs_error_upper_bin_c']} °C | {x['pooled_sample_max_abs_error_upper_bin_c']} °C | {x['episodes_hidden_max']} | {x['episodes_hidden_min']} | {x['max_hidden_max_error_c']}/{x['max_hidden_min_error_c']} °C |")
md+=['','A masked interior value can exceed both endpoints or fall below both. For 15–25 minute blocks, worst sampled missed max/min reached 1.5 °C. These point interpolations must not be used to assert local or daily extrema without separate source evidence. Detailed per-year histogram and extrema are in the adjacent CSVs and `data/p3_independent_review/conditional_holdout_2019_2020.json`.','']
(R/'reports/2026-11-13-p3-conditioned-short-gap-holdout.md').write_text('\n'.join(md))
print(json.dumps(summary_rows,ensure_ascii=False))
