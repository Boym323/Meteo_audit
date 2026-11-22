#!/usr/bin/env python3
"""Reduce chunked source outTemp=0 run-length aggregates; never load source rows."""
import csv,glob,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data/gap_zero_temperature_runs'
chunks=[]
for p in glob.glob(str(D/'results_*.json')):chunks.extend(json.loads(Path(p).read_text())['chunks'])
manifest=json.loads((R/'data/gap_zero_temperature_run_query_manifest.json').read_text())
expected={int(Path(x['path']).stem.split('_')[-1]) for x in manifest['zero_source_chunks']}
ids=[int(x['source_chunk']) for x in chunks]
assert set(ids)==expected and len(ids)==len(set(ids)) and len(ids)==21
totals=Counter();groups=Counter()
for c in chunks:
 for row in c['rows']:
  key=(int(row['utc_year']),row['gap_band'],row['protection_scope'])
  for k,v in row.items():
   if k in ('utc_year','gap_band','protection_scope'):continue
   if k=='max_run_samples':
    totals[k]=max(totals[k],int(v));groups[(key,k)]=max(groups[(key,k)],int(v))
   else:
    totals[k]+=int(v);groups[(key,k)]+=int(v)
assert totals['zero_samples']==42298
assert totals['zero_run_count']==2247
assert totals['singleton_runs']+totals['runs_2_to_5']+totals['runs_6_to_11']+totals['runs_12_plus']==totals['zero_run_count']
assert totals['max_run_samples']==2157
records=[]
for key in sorted({k for k,_ in groups}):
 row={'utc_year':key[0],'gap_band':key[1],'protection_scope':key[2]}
 for name in sorted({n for _,n in groups}):row[name]=groups[(key,name)]
 records.append(row)
summary={'status':'PASS','chunks':len(ids),'input_zero_samples':42298,'totals':dict(totals),'by_year_gap_band':records,
 'definition':'A run is consecutive source archive rows within one frozen gap_id with adjacent dateTime exactly 300 seconds and outTemp=0. Run lengths count rows, not guaranteed expected samples.',
 'protection':'Q1 2018 rows remain diagnostic-only; 2021 is excluded by the underlying gap catalog.',
 'decision':'All rows remain REVIEW_REQUIRED. Zero values and run lengths are source-quality flags, not proof of sensor failure or valid freezing.'}
(D/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-13-gap-outTemp-zero-run-profile.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
print(json.dumps({'status':'PASS','chunks':len(ids),'zero_samples':totals['zero_samples'],'runs':totals['zero_run_count'],'runs_12_plus':totals['runs_12_plus'],'max_run_samples':totals['max_run_samples']}))
