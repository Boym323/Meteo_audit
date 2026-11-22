#!/usr/bin/env python3
"""Aggregate 2016 1h-to-24h gap availability from six READ-ONLY archive screens."""
import csv,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
A=('reconstruction','eu','gw1000','eu_old','old_weewx','wh1080')
F=('row_count','outTemp_nonnull','outTemp_zero','outHumidity_nonnull','rain_nonnull','rainRate_nonnull','windSpeed_nonnull','windGust_nonnull','windDir_nonnull','barometer_nonnull','distinct_usUnits','distinct_interval')
events=[]
with (R/'reports/2026-11-12-gap-event-catalog.csv').open(newline='',encoding='utf-8') as f:
 for e in csv.DictReader(f):
  if e['utc_year']=='2016' and 3600<=int(e['delta_seconds'])<86400:
   events.append({'gap_id':f"2016:{e['prev_ts']}:{e['target_ts']}",'left_time':int(e['prev_ts']),'right_time':int(e['target_ts']),'gap_seconds':int(e['delta_seconds'])})
assert len(events)==135
raw={a:{} for a in A}
for p in sorted((R/'data/b5_2016_gap_per_archive_raw_chunks').glob('b5_2016_*.json')):
 x=json.loads(p.read_text());raw[x['archive']].update({r['gap_id']:r for r in x['rows']})
assert all(a in raw for a in A)
records=[]
for event in events:
 per={}
 for a in A:
  q=raw[a].get(event['gap_id'],{})
  per[a]={f:int(q.get(f,0) or 0) for f in F}
 both=per['old_weewx']['row_count']>0 and per['wh1080']['row_count']>0
 if not sum(v['row_count'] for v in per.values()):state='NO_SOURCE_ROW_OBSERVED_IN_SIX_ARCHIVES'
 elif both and per['old_weewx']['row_count']==per['wh1080']['row_count']:state='LEGACY_ROWS_EQUAL_COUNTS_ROW_LEVEL_MATCH_NOT_TESTED'
 elif both:state='LEGACY_ROW_COUNT_CONFLICT_REVIEW'
 elif per['eu_old']['row_count']:state='EU_OLD_ONLY_OR_LEGACY_ABSENT_REVIEW'
 else:state='MIXED_SOURCE_AVAILABILITY_REVIEW'
 records.append({**event,'source_state':state,'per_archive':per,'source_copy_identity_or_quality_proven':False})
summary={a:{'gaps_with_rows':sum(r['per_archive'][a]['row_count']>0 for r in records),'rows':sum(r['per_archive'][a]['row_count'] for r in records),'outTemp_nonnull':sum(r['per_archive'][a]['outTemp_nonnull'] for r in records),'outTemp_zero':sum(r['per_archive'][a]['outTemp_zero'] for r in records),'outHumidity_nonnull':sum(r['per_archive'][a]['outHumidity_nonnull'] for r in records),'rain_nonnull':sum(r['per_archive'][a]['rain_nonnull'] for r in records)} for a in A}
states=Counter(r['source_state'] for r in records)
out={'schema':'b5-2016-gap-per-archive-source-availability-v1','year':2016,'scope':'All 135 1-hour-to-under-24-hour gap events from frozen catalog; six archives queried in three event chunks per archive. Existing >=24h gap and sub-hour cohorts excluded.','database_mode':'READ_ONLY_SELECT_ONLY','query_execution_timestamp_utc':'NOT_CAPTURED_BY_WEATHER_MCP','records':records,'state_counts':dict(states),'per_archive_summary':summary,'correction_proposals':0,'source_row_sum_non_additive':True,'limitations':['All rows are any rows in exact open intervals, including off-grid timestamps; counts do not imply the slot was expected.','Legacy archive row counts do not prove timestamp/value concordance or sensor independence.','2016 source-only zero-temperature cohorts have separate source quality reviews; this availability inventory does not determine whether they were removed or valid.','No historical omission cause, station downtime, or local meteorological truth is inferred.','Counts overlap existing 30,271 strict 2016-2017 source-only records and 44,406 gap source rows; do not add to cumulative record counts.']}
(R/'data/b5_2016_per_gap_availability.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-B5-2016-per-gap-availability.csv').open('w',newline='',encoding='utf-8') as f:
 cols=['gap_id','left_time','right_time','gap_seconds','source_state']+[f'{a}_{v}' for a in A for v in F];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for r in records:
  q={k:r[k] for k in cols[:5]}
  for a in A:
   for v in F:q[f'{a}_{v}']=r['per_archive'][a][v]
  w.writerow(q)
lines=['# B5: per-gap source availability for 2016 gaps of 1 to <24 hours','','The frozen gap-event catalog contains 135 such 2016 events. They were screened through 18 READ-ONLY queries (three chunks per archive) to keep each statement bounded. The prior 2016 >=24h per-gap review is excluded.','', '| Archive | Gaps with rows | Rows | outTemp non-NULL | outTemp=0 | RH non-NULL | rain non-NULL |','|---|---:|---:|---:|---:|---:|---:|']
for a in A:
 s=summary[a];lines.append(f"| `{a}` | {s['gaps_with_rows']} | {s['rows']} | {s['outTemp_nonnull']} | {s['outTemp_zero']} | {s['outHumidity_nonnull']} | {s['rain_nonnull']} |")
lines+=['',f"Per-gap source-state classes: `{json.dumps(dict(states),ensure_ascii=False)}`.",'','The legacy archives contain the same number of source rows per interval only where the state says equal counts; the query does not compare the timestamp sequences or field values. Source-row availability includes off-grid rows and cannot establish intended sampling. WH1080 zero temperatures are retained as evidence and are not automatically invalidated. Existing 2016–2017 source-only quality screens remain authoritative for their narrower cohorts.','', 'No correction was proposed. B5 remains IN_PROGRESS because source availability and cause have not been determined for the complete gap-event catalog. The per-archive row totals overlap previous 30,271 and 44,406 cohorts.','', 'Reproduction: SQL files `sql/readonly/b5_2016_gap_availability/b5_2016_gap_availability_*.sql`; frozen results under `data/b5_2016_gap_per_archive_raw_chunks/`; run this builder and `scripts/validate_b5_2016_per_gap_report.py`. Query execution UTC is not returned by Weather MCP.']
(R/'reports/2026-11-14-B5-2016-per-gap-availability.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'gaps':len(records),'states':dict(states),'archives':summary},ensure_ascii=False,indent=2))
