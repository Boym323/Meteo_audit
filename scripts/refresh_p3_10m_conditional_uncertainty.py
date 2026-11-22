#!/usr/bin/env python3
"""Apply validated conservative histogram-bin upper bounds to the P3 10-minute subgroup."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
h=list(csv.DictReader((R/'reports/2026-11-13-p3-10m-conditional-holdout-histogram.csv').open()))
counts={}
for row in h:
 y=int(row['utc_year']); counts[y]=counts.get(y,0)+int(row['count'])
assert counts=={2019:2756,2020:2120}
pooled={}
for row in h:
 b=float(row['abs_error_bucket_lower_c']); pooled[b]=pooled.get(b,0)+int(row['count'])
def upper_quantile(p):
 total=sum(pooled.values()); target=int(total*p+0.999999); cumul=0
 for b,n in sorted(pooled.items()):
  cumul+=n
  if cumul>=target:return round(b+0.1,1)
 raise AssertionError('quantile missing')
q={f'p{int(p*100)}':upper_quantile(p) for p in (.50,.90,.95)}
assert sum(pooled.values())==4876 and q=={'p50':0.1,'p90':0.2,'p95':0.3}
p=R/'proposals/estimated_short_temperature_gaps/candidate_metadata.json';data=json.loads(p.read_text())
selected=[x for x in data if x['gap_s']==600]
assert len(selected)==36
for x in selected:
 x['uncertainty_abs_error_c']=q
 x['uncertainty_source']='2019-2020 deterministic hourly 10-minute masked holdout, same endpoint filters; 4,876 point-errors'
 x['uncertainty_method']='0.1 C histogram; report conservative bucket upper bounds'
 x['uncertainty_observed_max_abs_error_c_upper_bound']=0.8
 x['uncertainty_limitation']='Synthetic complete rows and deterministic hourly selection; not independent MCAR/MNAR missingness, fog/inversion or rare-regime validation.'
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(f'UPDATED {len(selected)} of {len(data)} candidates; pooled conservative upper p50/p90/p95={q}')
