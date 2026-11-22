#!/usr/bin/env python3
"""Validate conditional 10-minute holdout histogram and candidate uncertainty mapping."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
h=list(csv.DictReader((R/'reports/2026-11-13-p3-10m-conditional-holdout-histogram.csv').open()))
assert sum(int(x['count']) for x in h if x['utc_year']=='2019')==2756
assert sum(int(x['count']) for x in h if x['utc_year']=='2020')==2120
assert sum(int(x['count']) for x in h)==4876
p=json.loads((R/'proposals/estimated_short_temperature_gaps/candidate_metadata.json').read_text())
a=[x for x in p if x['gap_s']==600];b=[x for x in p if x['gap_s']!=600]
assert len(a)==36 and len(b)==71
assert all(x['uncertainty_abs_error_c']=={'p50':0.1,'p90':0.2,'p95':0.3} for x in a)
assert all('deterministic hourly' in x['uncertainty_source'] for x in a)
assert all(x['uncertainty_abs_error_c']=={'p50':0.15,'p90':0.55,'p95':0.75} for x in b)
assert all(x['uncertainty_limitation'] for x in p)
print('PASS: conditional 4,876-point holdout; 36/107 candidates receive duration-matched conservative bounds; remaining 71 retain broad bounds')
