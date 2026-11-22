#!/usr/bin/env python3
import csv,json
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1]; raw=json.loads((R/'data/source_only_2018_q2_q4_field_aggregates.json').read_text())
assert len(raw)==200 and len({x['field_name'] for x in raw})==50
keys={(x['utc_quarter'],int(x['old_interval']),int(x['wh_interval'])) for x in raw}
assert keys=={('2018-Q2',5,5),('2018-Q3',5,5),('2018-Q3',6,6),('2018-Q4',5,5)}
expected={('2018-Q2',5):212,('2018-Q3',5):16,('2018-Q3',6):1,('2018-Q4',5):193}
expected_json={'2018-Q2_interval5':212,'2018-Q3_interval5':16,'2018-Q3_interval6':1,'2018-Q4_interval5':193}
for x in raw:assert int(x['source_only_rows'])==expected[(x['utc_quarter'],int(x['old_interval']))]
fields=[]
for f in sorted({x['field_name'] for x in raw}):
 a=[x for x in raw if x['field_name']==f]; vals={k:sum(int(x[k]) for x in a) for k in ('old_nonnull','wh_nonnull','paired_equal','paired_conflict','unit_conflict_rows','interval_conflict_rows')}; n=422
 pair=vals['paired_equal']+vals['paired_conflict']; oo=vals['old_nonnull']-pair;wo=vals['wh_nonnull']-pair;bn=n-(vals['old_nonnull']+vals['wh_nonnull']-pair)
 assert min(oo,wo,bn)>=0 and oo+wo+pair+bn==n
 fields.append({'field':f,'source_only_timestamps':n,**vals,'old_only_nonnull':oo,'wh_only_nonnull':wo,'both_null':bn,'eligible_for_restoration':False,'classification':'REVIEW_REQUIRED_SOURCE_CONFLICT' if vals['paired_conflict'] else 'REVIEW_REQUIRED_AVAILABILITY_ONLY'})
summary={'rows':422,'fields':50,'quarter_interval_rows':expected_json,'fields_with_conflicts':sum(x['paired_conflict']>0 for x in fields),'fully_paired_equal_fields':sum(x['paired_equal']==422 and x['paired_conflict']==0 for x in fields),'eligible_fields':0}
out={'schema':'source-only-field-eligibility-v1','scope':'2018 Q2-Q4 UTC; protected Q1 excluded','target_archive':'loucka_reconstruction','source_archives':['old_weewx','weewx_WH1080'],'source_only_timestamps':422,'quarter_interval_row_counts':expected_json,'query_execution_utc':'NOT_CAPTURED_BY_WEATHER_MCP','recorded_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'fields':fields,'summary':summary,'interpretation':'Field availability/concordance only. All 421 interval-5 source keys are off-grid (as independently established by frozen alignment inventory); source-only key does not imply projected target absence. The distinct interval-6 row remains separate. No RESTORED eligibility.','safety':{'database_access':'READ_ONLY SELECT','writes':0,'staging':False,'application':False,'q1_2018_queried':False,'year_2021_queried':False}}
(R/'data/2018_q2_q4_source_only_field_eligibility.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-2018-q2-q4-source-only-field-eligibility.csv').open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=fields[0].keys());w.writeheader();w.writerows(fields)
lines=['# Source-only field eligibility: 2018 Q2–Q4','', 'READ-ONLY exact-key aggregate; Q1 2018 was excluded. Exact query SQL is in `sql/readonly/source_only_2018_q2_q4_field_aggregates/`.','', '| Period/interval | Rows | Off-grid 5-minute keys | Unit/interval conflicts |','|---|---:|---:|---:|','| 2018-Q2 / 5 min | 212 | 212 | 0 |','| 2018-Q3 / 5 min | 16 | 16 | 0 |','| 2018-Q3 / 6 min | 1 | separate interval-6 row | 0 |','| 2018-Q4 / 5 min | 193 | 193 | 0 |','| Total | 422 | 421 | 0 |','',f"Across 50 fields, {summary['fields_with_conflicts']} show paired value conflicts and {summary['fully_paired_equal_fields']} are fully paired/equal. Field partitions reconcile. No field is approved for restoration. Existing alignment evidence indicates all 421 interval-5 keys have nearest projected rows; exact-key absence must not be interpreted as a missing target slot. The interval-6 record is not shifted or resampled.",'', 'No Q1 2018 record was queried. No correction proposal was added.']
(R/'reports/2026-11-14-2018-q2-q4-source-only-field-eligibility.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'BUILT','summary':summary},indent=2))
