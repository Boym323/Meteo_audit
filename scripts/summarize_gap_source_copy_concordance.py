#!/usr/bin/env python3
"""Aggregate per-chunk SELECT results for WH1080-vs-old gap source concordance."""
import csv,glob,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];data=R/'data/gap_source_copy_concordance'
chunks=[]
for p in sorted(glob.glob(str(data/'chunk_results_*.json'))):chunks.extend(json.loads(Path(p).read_text())['chunks'])
ids=[int(x['chunk']) for x in chunks]
assert sorted(ids)==list(range(1,104)) and len(ids)==len(set(ids)), 'all 103 query chunks must appear exactly once'
totals=Counter();groups=Counter()
for c in chunks:
 for row in c['rows']:
  key=(int(row['utc_year']),row['gap_band'],row['protection_scope'])
  for k,v in row.items():
   if k in ('utc_year','gap_band','protection_scope'):continue
   totals[k]+=int(v)
   groups[(key,k)]+=int(v)
assert totals['wh1080_rows']==44406
assert totals['old_weewx_rows']==44393 and totals['old_weewx_missing']==13
assert totals['units_equal']==44393 and totals['intervals_equal']==44393
assert totals['wh_outTemp_zero']==42298 and totals['wh_outTemp_null']==0
assert totals['outTemp_both_present']==5367 and totals['outTemp_conflict']==0 and totals['outTemp_equal']==5367
assert totals['outHumidity_both_present']==1709 and totals['outHumidity_conflict']==169
assert totals['rain_both_present']==44387 and totals['rain_conflict']==0
assert totals['rainRate_both_present']==44392 and totals['rainRate_conflict']==0
assert totals['windSpeed_both_present']==5901 and totals['windSpeed_conflict']==0
fields=sorted({k for _,k in groups})
records=[]
for key in sorted({k for k,_ in groups}):
 row={'utc_year':key[0],'gap_band':key[1],'protection_scope':key[2]}
 for field in fields:row[field]=groups[(key,field)]
 records.append(row)
summary={'status':'PASS','chunks':103,'target_candidates':44406,'records':dict(totals),'by_year_gap_band':records,
 'interpretation':{'source_agreement':'archive-copy concordance only; no independent observation or lineage proof','outTemp_zero':'flagged for sentinel/failure review, not automatically rejected; exact 0 C can be real','RH_conflicts':'169 paired non-NULL values differ; keep per-target REVIEW_REQUIRED','protected_q1_2018':'diagnostic-only rows remain segregated by protection_scope','year_2021':'excluded from the underlying gap overlay'},
 'disposition':{'RESTORED':0,'ESTIMATED':0,'REVIEW_REQUIRED':44406,'MISSING':0}}
(data/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
csv_path=R/'reports/2026-11-13-gap-source-copy-concordance-by-year.csv'
with csv_path.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
print(json.dumps({'status':'PASS','chunks':len(ids),'WH1080':totals['wh1080_rows'],'old':totals['old_weewx_rows'],'outTemp_zero':totals['wh_outTemp_zero'],'temp_equal_nonnull':totals['outTemp_both_present'],'RH_pairs':totals['outHumidity_both_present'],'RH_conflicts':totals['outHumidity_conflict']}))
