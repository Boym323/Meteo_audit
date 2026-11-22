#!/usr/bin/env python3
"""Aggregate 2018 1h-to-under-24h source availability; does not infer quality."""
import csv,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]; A=('reconstruction','eu','gw1000','eu_old','old_weewx','wh1080')
F=('row_count','outTemp_nonnull','outTemp_zero','outHumidity_nonnull','rain_nonnull','rainRate_nonnull','windSpeed_nonnull','windGust_nonnull','windDir_nonnull','barometer_nonnull','distinct_usUnits','distinct_interval')
events=[]
for e in csv.DictReader((R/'reports/2026-11-12-gap-event-catalog.csv').open()):
 if e['utc_year']=='2018' and 3600<=int(e['delta_seconds'])<86400:
  events.append({'gap_id':f"2018:{e['prev_ts']}:{e['target_ts']}",'left_time':int(e['prev_ts']),'right_time':int(e['target_ts']),'gap_seconds':int(e['delta_seconds'])})
assert len(events)==63
raw={a:{} for a in A}
for p in (R/'data/b5_2018_gap_per_archive_raw_chunks').glob('b5_2018_*.json'):
 x=json.loads(p.read_text()); assert x['archive'] in raw
 raw[x['archive']].update({r['gap_id']:r for r in x['rows']})
assert all(len(list((R/'data/b5_2018_gap_per_archive_raw_chunks').glob(f'b5_2018_*_{a}.json')))==2 for a in A)
records=[]
for e in events:
 per={}
 for a in A:
  q=raw[a].get(e['gap_id'],{})
  per[a]={f:int(q.get(f,0) or 0) for f in F}
 both=per['old_weewx']['row_count']>0 and per['wh1080']['row_count']>0
 state=('LEGACY_ROWS_EQUAL_COUNTS_ROW_LEVEL_MATCH_NOT_TESTED' if both and per['old_weewx']['row_count']==per['wh1080']['row_count'] else 'NO_SOURCE_ROW_OBSERVED_IN_SIX_ARCHIVES' if not sum(v['row_count'] for v in per.values()) else 'SOURCE_AVAILABILITY_REVIEW')
 records.append({**e,'source_state':state,'per_archive':per,'source_copy_identity_or_quality_proven':False,'protected_q1_2018':e['left_time']<1522540800})
summary={a:{'gaps_with_rows':sum(r['per_archive'][a]['row_count']>0 for r in records),'rows':sum(r['per_archive'][a]['row_count'] for r in records),'outTemp_nonnull':sum(r['per_archive'][a]['outTemp_nonnull'] for r in records),'outTemp_zero':sum(r['per_archive'][a]['outTemp_zero'] for r in records),'outHumidity_nonnull':sum(r['per_archive'][a]['outHumidity_nonnull'] for r in records),'rain_nonnull':sum(r['per_archive'][a]['rain_nonnull'] for r in records)} for a in A}
states=Counter(r['source_state'] for r in records)
out={'schema':'b5-2018-gap-per-archive-source-availability-v1','year':2018,'scope':'All 63 catalogued 1h-to-under-24h gap events in 2018. Q1 events are diagnostic-only/protected from correction proposals.','database_mode':'READ_ONLY_SELECT_ONLY','query_execution_timestamp_utc':'NOT_CAPTURED_BY_WEATHER_MCP','records':records,'protected_q1_gap_count':sum(r['protected_q1_2018'] for r in records),'post_q1_gap_count':sum(not r['protected_q1_2018'] for r in records),'state_counts':dict(states),'per_archive_summary':summary,'correction_proposals':0,'source_row_sum_non_additive':True,'limitations':['Availability rows may be off-grid and do not establish expected slots or historical omission cause.','Equal legacy per-gap row counts are not row-level timestamp/value concordance.','No measurement correctness, source identity, station operational status or prior removal intent is inferred.','Counts overlap existing gap/source-only inventories; do not add to cumulative analyzed-record total.']}
(R/'data/b5_2018_per_gap_availability.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-B5-2018-per-gap-availability.csv').open('w',newline='') as f:
 cols=['gap_id','left_time','right_time','gap_seconds','source_state','protected_q1_2018']+[f'{a}_{v}' for a in A for v in F];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for r in records:
  q={k:r[k] for k in cols[:6]}
  for a in A:
   for v in F:q[f'{a}_{v}']=r['per_archive'][a][v]
  w.writerow(q)
lines=['# B5: per-gap source availability for 2018 gaps of 1 to <24 hours','','The frozen gap catalog contains 63 events. Twelve READ-ONLY exact-range queries were run (two event chunks for each of six archives). Q1 2018 remains protected from correction proposals; this is diagnostic evidence only.','', '| Archive | Gaps with rows | Rows | outTemp non-NULL | outTemp=0 | RH non-NULL | rain non-NULL |','|---|---:|---:|---:|---:|---:|---:|']
for a in A:
 s=summary[a];lines.append(f"| `{a}` | {s['gaps_with_rows']} | {s['rows']} | {s['outTemp_nonnull']} | {s['outTemp_zero']} | {s['outHumidity_nonnull']} | {s['rain_nonnull']} |")
lines+=['',f"Per-gap availability classes: `{json.dumps(dict(states))}`.",'','All 63 events are within protected Q1 2018 and are diagnostic-only; all 63 gaps have source rows in both legacy archives, with equal per-gap row counts. WH1080 outTemp is zero in every one of its 4,717 source rows; old_weewx outTemp is NULL in all 4,717 rows. This is a quality flag requiring source-epoch/context review, not proof the sensor values are wrong or that these rows were intentionally removed. This report does not compare row-level timestamps or other values. No correction proposal was created.','', 'Counts overlap prior inventories; B5 remains IN_PROGRESS. Weather MCP did not supply exact query execution times (`NOT_CAPTURED_BY_WEATHER_MCP`).', '', 'Reproduction: run `scripts/build_b5_2018_per_gap_report.py` then `scripts/validate_b5_2018_per_gap_report.py`; SQL and frozen raw aggregates are under `sql/readonly/b5_2018_gap_availability/` and `data/b5_2018_gap_per_archive_raw_chunks/`.']
(R/'reports/2026-11-14-B5-2018-per-gap-availability.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'gaps':len(records),'states':dict(states),'archives':summary},indent=2))
