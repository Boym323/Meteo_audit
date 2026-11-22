#!/usr/bin/env python3
"""Cross-check row membership, run boundaries, and key aggregates."""
import json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=json.loads((R/'data/short_gap_source_detail_per_target.json').read_text())['records']
d=json.loads((R/'data/b5_short_gap_zero_outtemp_2016_2017_review.json').read_text())
expected=[r for r in source if r['utc_year'] in (2016,2017) and r['outTemp_exact_zero_source_present']]
assert len(expected)==4679 and len(d['records'])==4679
assert {r['timestamp'] for r in expected}=={r['timestamp'] for r in d['records']}
assert d['summary']['runs']==1483 and d['summary']['target_change_events']==0 and d['summary']['proposals']==0
for year,targets,runs,contrast,near,novary in ((2016,1116,360,697,90,221),(2017,3563,1123,2680,332,710)):
 y=d['summary']['by_year'][str(year)]
 assert (y['zero_source_targets'],y['bounded_runs'])==(targets,runs)
 assert y['context_bands'].get('CONTEXT_CONTRAST_GT_5C',0)==contrast
 assert y['context_bands'].get('NEAR_ZERO_CONTEXT',0)==near
 assert y['runs_with_other_field_variation']==novary
 assert y['old_weewx_outTemp_nonnull']==(0 if year==2016 else 10)
assert all(r['wh1080_outTemp']==0 and r['disposition'].startswith('REVIEW_REQUIRED') for r in d['records'])
assert all(r['source_usUnits']==17 and r['source_interval_min']==5 for r in d['records'])
assert all(e['n']>=1 for e in d['runs'])
# Independently rebuild gap-constrained 300-second runs from the frozen input.
expected=sorted(expected,key=lambda r:(r['utc_year'],r['timestamp']))
raw_runs=[]
for r in expected:
 if raw_runs and raw_runs[-1][-1]['gap_id']==r['gap_id'] and r['timestamp']-raw_runs[-1][-1]['timestamp']==300: raw_runs[-1].append(r)
 else: raw_runs.append([r])
assert len(raw_runs)==1483
fields=('rain','rainRate','windSpeed','windGust','pressure')
for year,expected_varying in ((2016,221),(2017,710)):
 varying=0
 for run in raw_runs:
  if run[0]['utc_year']!=year: continue
  wh=[r['source_archives']['weewx_WH1080']['fields'] for r in run]
  if any(len({x.get(f) for x in wh if x.get(f) is not None})>1 for f in fields): varying+=1
 assert varying==expected_varying

print('PASS: 4,679 rows in 1,483 bounded candidate runs; 2016/2017 context and cross-field variation aggregates reconcile; zero proposals/writes.')
