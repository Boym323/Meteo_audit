#!/usr/bin/env python3
"""Build field-level source-only partitions from aggregated READ-ONLY MCP query output."""
import csv,json
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1]; raw=json.loads((R/'data/source_only_2010_2011_field_aggregates.json').read_text())
assert len(raw)==100
out_rows=[]; summaries=[]
for year,n in ((2010,1989),(2011,5016)):
 subset=[r for r in raw if int(r['utc_year'])==year];assert len(subset)==50 and {int(r['source_only_rows']) for r in subset}=={n}
 fields=[]
 for r in sorted(subset,key=lambda x:x['field_name']):
  vals={k:int(r[k]) for k in ('old_nonnull','wh_nonnull','paired_equal','paired_conflict','unit_conflict_rows','interval_conflict_rows')}
  paired=vals['paired_equal']+vals['paired_conflict']; old_only=vals['old_nonnull']-paired;wh_only=vals['wh_nonnull']-paired;both_null=n-(vals['old_nonnull']+vals['wh_nonnull']-paired)
  assert min(old_only,wh_only,both_null)>=0
  assert old_only+wh_only+paired+both_null==n
  d={'year':year,'field':r['field_name'],'source_only_timestamps':n,**vals,'old_only_nonnull':old_only,'wh_only_nonnull':wh_only,'both_null':both_null,'classification':'REVIEW_REQUIRED_SOURCE_CONFLICT' if vals['paired_conflict'] else 'REVIEW_REQUIRED_COPY_AGREEMENT_OR_ASYMMETRIC_AVAILABILITY','eligible_for_restoration':False,'reason':'Read-only availability/concordance only. Exact-copy values do not establish independent provenance, quality, or absence of historical cleaning/removal.'}
  fields.append(d);out_rows.append(d)
 summary={'year':year,'source_only_timestamps':n,'fields':50,'conflict_fields':sum(f['paired_conflict']>0 for f in fields),'fully_paired_equal_fields':sum(f['paired_equal']==n and f['paired_conflict']==0 for f in fields),'unit_conflict_rows':max(f['unit_conflict_rows'] for f in fields),'interval_conflict_rows':max(f['interval_conflict_rows'] for f in fields),'eligible_fields':0}
 summaries.append(summary)
 obj={'schema':'source-only-field-eligibility-from-readonly-aggregates-v1','year':year,'source_only_timestamps':n,'source_archives':['old_weewx','weewx_WH1080'],'target_archive':'loucka_reconstruction','cohort_definition':'Exact timestamp present in both source archives and absent from reconstruction.archive, UTC year.','query_source':'Weather MCP READ_ONLY SELECT; five field-partition query chunks; exact SQL in sql/readonly/source_only_2010_2011_field_aggregates/.','query_execution_utc':'NOT_CAPTURED_BY_WEATHER_MCP','recorded_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'fields':fields,'summary':summary,'interpretation':'Availability and raw concordance do not establish meteorological truth or cause of omission. Matching copies are not independent evidence. No correction is approved.','safety':{'database_access':'READ_ONLY SELECT','writes':0,'staging':False,'application':False,'q1_2018_queried':False,'year_2021_queried':False}}
 (R/f'data/{year}_source_only_field_eligibility.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-2010-2011-source-only-field-eligibility.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=out_rows[0].keys());w.writeheader();w.writerows(out_rows)
now=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
lines=['# Source-only field eligibility: 2010–2011','',f'Aggregated READ-ONLY Weather MCP query results recorded at {now} UTC; exact query execution time was not supplied by the tool. Query scope is fixed UTC years 2010 and 2011.','', '| UTC year | Source-only timestamps | Fields | Fields with paired conflicts | Fully paired/equal fields | Unit/interval conflict rows | Restoration-eligible fields |','|---:|---:|---:|---:|---:|---:|---:|']
for s in summaries:lines.append(f"| {s['year']} | {s['source_only_timestamps']:,} | 50 | {s['conflict_fields']} | {s['fully_paired_equal_fields']} | {s['unit_conflict_rows']}/{s['interval_conflict_rows']} | 0 |")
lines+=['','Exact archive key counts: 2010 1,989 and 2011 5,016. These are exact-key source rows, not proof of intended slots or loss cause. The matrices partition NULL, one-sided availability, paired equal and paired conflict per field. No restoration proposal is emitted.','', 'The 2010 temperature is paired and equal for all 1,989 rows. 2011 temperature is paired and equal for 5,014/5,016 rows (two values are absent from old_weewx); 2011 RH is present in old_weewx for all rows but only 1,752 WH1080 rows. RH/derived-field conflicts are not promoted.','', 'JSON: `data/2010_source_only_field_eligibility.json`, `data/2011_source_only_field_eligibility.json`. CSV: companion file. Validation: `scripts/validate_2010_2011_source_only_field_eligibility.py`.']
(R/'reports/2026-11-14-2010-2011-source-only-field-eligibility.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'BUILT','summaries':summaries,'field_rows':len(out_rows)},indent=2))
