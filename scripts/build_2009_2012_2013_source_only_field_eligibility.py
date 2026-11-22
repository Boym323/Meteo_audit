#!/usr/bin/env python3
"""Derive annual field availability matrices from frozen monthly aggregates only."""
import csv,json
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1]
rows=[]; outputs=[]
for year in (2009,2012,2013):
 src=json.loads((R/f'data/{year}_source_only_field_month.json').read_text())
 totals={}; months=src['monthly']; nyear=src['source_only_rows']
 assert sum(m['source_only_rows'] for m in months)==nyear
 for m in months:
  n=m['source_only_rows']
  for field,x in m['fields'].items():
   t=totals.setdefault(field,{k:0 for k in ('old_nonnull','wh_nonnull','paired_equal','paired_conflict','old_only_nonnull','wh_only_nonnull','both_null')})
   pair=x['both_equal']+x['both_conflict']; union=x['old_nonnull']+x['wh_nonnull']-pair
   oldonly=x['old_nonnull']-pair; whonly=x['wh_nonnull']-pair; bothnull=n-union
   assert min(oldonly,whonly,bothnull)>=0,(year,m['month'],field)
   assert pair+x['old_nonnull']-pair==x['old_nonnull']
   for k,v in [('old_nonnull',x['old_nonnull']),('wh_nonnull',x['wh_nonnull']),('paired_equal',x['both_equal']),('paired_conflict',x['both_conflict']),('old_only_nonnull',oldonly),('wh_only_nonnull',whonly),('both_null',bothnull)]:t[k]+=v
 for field,t in sorted(totals.items()):
  assert t['old_only_nonnull']+t['wh_only_nonnull']+t['paired_equal']+t['paired_conflict']+t['both_null']==nyear
  if t['paired_equal']+t['paired_conflict']:
   disposition='REVIEW_REQUIRED_SOURCE_CONFLICT' if t['paired_conflict'] else 'REVIEW_REQUIRED_COPY_AGREEMENT_ONLY'
  elif t['old_nonnull'] or t['wh_nonnull']: disposition='REVIEW_REQUIRED_SINGLE_COPY_ONLY'
  else: disposition='MISSING_IN_BOTH_COPIES'
  item={'year':year,'field':field,'source_only_timestamps':nyear,**t,'classification':disposition,'eligible_for_restoration':False,'reason':'Monthly exact-source snapshots establish availability/concordance only; they do not establish local correctness, independent provenance, or absence of historical cleaning/removal.'}
  rows.append(item)
 summary={'year':year,'source_only_timestamps':nyear,'months_in_snapshot':len(months),'fields':len(totals),'conflict_fields':sum(x['paired_conflict']>0 for x in totals.values()),'fully_paired_and_equal_fields':sum(x['paired_equal']==nyear and x['paired_conflict']==0 for x in totals.values()),'eligible_fields':0}
 out={'schema':'derived-source-only-field-eligibility-v1','year':year,'source_snapshot':f'data/{year}_source_only_field_month.json','source_only_timestamps':nyear,'months_in_snapshot':len(months),'fields':[x for x in rows if x['year']==year],'summary':summary,'derivation':'Monthly aggregates only; paired nonnull = both_equal + both_conflict; one-sided and both-null counts derived by exact partition identities.','interpretation':'Exact source-copy row availability and concordance only. Copy agreement is not independent evidence and does not rule out deliberate historical removal. No field is approved for restoration.','safety':src.get('database_writes',0)}
 (R/f'data/{year}_source_only_field_eligibility.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 outputs.append(summary)
outcsv=R/'reports/2026-11-14-2009-2012-2013-source-only-field-eligibility.csv'
with outcsv.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
now=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
lines=['# Source-only field eligibility: 2009, 2012, 2013','',f'Derived at {now} UTC exclusively from frozen monthly source-copy aggregates; no DB query was run.','', '| Year | Timestamps | Months | Fields | Fields with conflicts | Fully paired/equal fields | Restoration-eligible fields |','|---:|---:|---:|---:|---:|---:|---:|']
for s in outputs:lines.append(f"| {s['year']} | {s['source_only_timestamps']:,} | {s['months_in_snapshot']} | {s['fields']} | {s['conflict_fields']} | {s['fully_paired_and_equal_fields']} | 0 |")
lines+=['','Each field partition reconciles exactly across old_weewx and weewx_WH1080 for source-only exact timestamps. Paired agreement does not prove independent source lineage, measurement quality, or that a value was not removed by historical cleaning. No RESTORED or ESTIMATED proposal was emitted.','', 'Machine-readable outputs: `data/{2009,2012,2013}_source_only_field_eligibility.json`; full field CSV is this report companion. Validator: `scripts/validate_2009_2012_2013_source_only_field_eligibility.py`.']
(R/'reports/2026-11-14-2009-2012-2013-source-only-field-eligibility.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'BUILT','year_summaries':outputs,'field_rows':len(rows),'database_access':'NONE'},ensure_ascii=False,indent=2))
