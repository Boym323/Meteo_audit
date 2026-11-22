#!/usr/bin/env python3
"""Aggregate 2017 1h-to-24h gap availability from six READ-ONLY archive screens."""
import csv,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
A=('reconstruction','eu','gw1000','eu_old','old_weewx','wh1080')
F=('row_count','outTemp_nonnull','outTemp_zero','outHumidity_nonnull','rain_nonnull','rainRate_nonnull','windSpeed_nonnull','windGust_nonnull','windDir_nonnull','barometer_nonnull','distinct_usUnits','distinct_interval')
events=[]
with (R/'reports/2026-11-12-gap-event-catalog.csv').open(newline='',encoding='utf-8') as f:
 for e in csv.DictReader(f):
  if e['utc_year']=='2017' and 3600<=int(e['delta_seconds'])<86400:
   events.append({'gap_id':f"2017:{e['prev_ts']}:{e['target_ts']}",'left_time':int(e['prev_ts']),'right_time':int(e['target_ts']),'gap_seconds':int(e['delta_seconds'])})
assert len(events)==263
raw={a:{} for a in A}
for p in sorted((R/'data/b5_2017_gap_per_archive_raw_chunks').glob('b5_2017_*.json')):
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
out={'schema':'b5-2017-gap-per-archive-source-availability-v1','year':2017,'scope':'All 263 1-hour-to-under-24-hour gap events from the frozen gap catalog; six archives queried in six event chunks per archive. Existing >=24h and sub-hour cohorts are excluded.','database_mode':'READ_ONLY_SELECT_ONLY','query_execution_timestamp_utc':'NOT_CAPTURED_BY_WEATHER_MCP','records':records,'state_counts':dict(states),'per_archive_summary':summary,'correction_proposals':0,'source_row_sum_non_additive':True,'limitations':['Rows include off-grid timestamps; availability does not prove intended cadence or expected slots.','Equal legacy row counts per gap do not prove timestamp or value concordance or sensor independence.','2017 strict source-only zero-temperature cohorts have separate quality reviews; this inventory does not establish invalidity or removal cause.','No historical omission cause, station downtime, or local meteorological truth is inferred.','Counts overlap existing source-only/gap inventories and must not be added to cumulative analyzed-record totals.']}
(R/'data/b5_2017_per_gap_availability.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-B5-2017-per-gap-availability.csv').open('w',newline='',encoding='utf-8') as f:
 cols=['gap_id','left_time','right_time','gap_seconds','source_state']+[f'{a}_{v}' for a in A for v in F];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for r in records:
  q={k:r[k] for k in cols[:5]}
  for a in A:
   for v in F:q[f'{a}_{v}']=r['per_archive'][a][v]
  w.writerow(q)
lines=['# B5: per-gap source availability for 2017 gaps of 1 to <24 hours','','The frozen gap-event catalog contains 263 events of 1 to <24 hours. They were screened through 36 READ-ONLY exact-range queries (six chunks for each of the six archives). Existing sub-hour and >=24h analyses are separate.','', '| Archive | Gaps with rows | Rows | outTemp non-NULL | outTemp=0 | RH non-NULL | rain non-NULL |','|---|---:|---:|---:|---:|---:|---:|']
for a in A:
 s=summary[a];lines.append(f"| `{a}` | {s['gaps_with_rows']} | {s['rows']} | {s['outTemp_nonnull']} | {s['outTemp_zero']} | {s['outHumidity_nonnull']} | {s['rain_nonnull']} |")
lines+=['',f"Per-gap source-state classes: `{json.dumps(dict(states),ensure_ascii=False)}`.",'','Both legacy archives have rows across all 263 events and have equal per-gap row counts (8,359 rows each). This query does not compare per-row timestamp sequences or values. `eu_old` adds 45 rows; reconstruction, current EU and GW1000 have no rows in these intervals. The high WH1080 zero-temperature share remains a source-quality concern already analyzed in narrower source-only cohorts; no invalidity conclusion is inferred from this count.','', 'No correction proposal was generated. B5 remains IN_PROGRESS because these availability observations do not identify expected slots, historical removal, sensor correctness or gap cause. Counts overlap existing inventories.', '', 'Reproduction: SQL under `sql/readonly/b5_2017_gap_availability/`, frozen query results under `data/b5_2017_gap_per_archive_raw_chunks/`, then run this builder and `scripts/validate_b5_2017_per_gap_report.py`. Weather MCP did not provide exact query execution times.']
(R/'reports/2026-11-14-B5-2017-per-gap-availability.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'gaps':len(records),'states':dict(states),'archives':summary},ensure_ascii=False,indent=2))
