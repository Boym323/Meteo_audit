#!/usr/bin/env python3
"""Aggregate exact-range 2019-2020 1h-to-under-24h gap source availability."""
import csv,json,subprocess,sys
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=('reconstruction','eu','gw1000','eu_old','old_weewx','wh1080')
F=('row_count','outTemp_nonnull','outTemp_zero','outHumidity_nonnull','rain_nonnull','rainRate_nonnull','windSpeed_nonnull','windGust_nonnull','windDir_nonnull','barometer_nonnull','distinct_usUnits','distinct_interval')
events=[]
for e in csv.DictReader((R/'reports/2026-11-12-gap-event-catalog.csv').open()):
 y=int(e['utc_year'])
 if y in (2019,2020) and 3600<=int(e['delta_seconds'])<86400:
  events.append({'year':y,'gap_id':f"{y}:{e['prev_ts']}:{e['target_ts']}",'left_time':int(e['prev_ts']),'right_time':int(e['target_ts']),'gap_seconds':int(e['delta_seconds'])})
assert len(events)==50
raw={a:{} for a in A}
for y in (2019,2020):
 for p in (R/f'data/b5_{y}_gap_per_archive_raw_chunks').glob(f'b5_{y}_*.json'):
  x=json.loads(p.read_text());assert x['archive'] in raw;raw[x['archive']].update({r['gap_id']:r for r in x['rows']})
assert sum(len(list((R/f'data/b5_{y}_gap_per_archive_raw_chunks').glob(f'b5_{y}_*_{a}.json'))) for y in (2019,2020) for a in A)==18
records=[]
for e in events:
 per={}
 for a in A:
  q=raw[a].get(e['gap_id'],{});per[a]={f:int(q.get(f,0) or 0) for f in F}
 both=per['old_weewx']['row_count']>0 and per['wh1080']['row_count']>0
 if both and per['old_weewx']['row_count']==per['wh1080']['row_count']:state='LEGACY_ROWS_EQUAL_COUNTS_ROW_LEVEL_MATCH_NOT_TESTED'
 elif not sum(v['row_count'] for v in per.values()):state='NO_SOURCE_ROW_OBSERVED_IN_SIX_ARCHIVES'
 else:state='MIXED_SOURCE_AVAILABILITY_REVIEW'
 records.append({**e,'source_state':state,'per_archive':per,'source_copy_identity_or_quality_proven':False})
summary={a:{'gaps_with_rows':sum(r['per_archive'][a]['row_count']>0 for r in records),'rows':sum(r['per_archive'][a]['row_count'] for r in records),'outTemp_nonnull':sum(r['per_archive'][a]['outTemp_nonnull'] for r in records),'outTemp_zero':sum(r['per_archive'][a]['outTemp_zero'] for r in records),'outHumidity_nonnull':sum(r['per_archive'][a]['outHumidity_nonnull'] for r in records),'rain_nonnull':sum(r['per_archive'][a]['rain_nonnull'] for r in records)} for a in A}
states=Counter(r['source_state'] for r in records)
by_year={str(y):{'gaps':sum(r['year']==y for r in records),'states':dict(Counter(r['source_state'] for r in records if r['year']==y)),'per_archive_rows':{a:sum(r['per_archive'][a]['row_count'] for r in records if r['year']==y) for a in A}} for y in (2019,2020)}
out={'schema':'b5-2019-2020-gap-per-archive-source-availability-v1','years':[2019,2020],'scope':'All 50 catalogued 1h-to-under-24h gap events in 2019-2020.','database_mode':'READ_ONLY_SELECT_ONLY','query_execution_timestamp_utc':'NOT_CAPTURED_BY_WEATHER_MCP','records':records,'state_counts':dict(states),'per_year':by_year,'per_archive_summary':summary,'correction_proposals':0,'source_row_sum_non_additive':True,'limitations':['Rows include off-grid timestamps and do not establish expected cadence or expected slots.','Equal per-gap counts in legacy archives do not prove row-level timestamp/value concordance.','No absence cause, station downtime, source identity or meteorological correctness is inferred.','Counts overlap existing gap/source-only inventories; do not add to cumulative analyzed records.']}
(R/'data/b5_2019_2020_per_gap_availability.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-B5-2019-2020-per-gap-availability.csv').open('w',newline='') as f:
 cols=['year','gap_id','left_time','right_time','gap_seconds','source_state']+[f'{a}_{v}' for a in A for v in F];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for r in records:
  q={k:r[k] for k in cols[:6]}
  for a in A:
   for v in F:q[f'{a}_{v}']=r['per_archive'][a][v]
  w.writerow(q)
lines=['# B5: per-gap source availability, 2019-2020 (1 to <24 hours)','','The frozen catalog includes 5 events in 2019 and 45 in 2020. Eighteen READ-ONLY queries covered six archives (one chunk for 2019 and two for 2020).','', '| Archive | Gaps with rows | Rows | outTemp non-NULL | outTemp=0 | RH non-NULL | rain non-NULL |','|---|---:|---:|---:|---:|---:|---:|']
for a in A:
 s=summary[a];lines.append(f"| `{a}` | {s['gaps_with_rows']} | {s['rows']} | {s['outTemp_nonnull']} | {s['outTemp_zero']} | {s['outHumidity_nonnull']} | {s['rain_nonnull']} |")
lines+=['',f"Per-gap states: `{json.dumps(dict(states))}`.",'',f"Year-level availability: `{json.dumps(by_year,ensure_ascii=False)}`.",'','Equal per-gap row counts in the legacy archives are availability evidence only; row-level agreement has not been tested. `NO_SOURCE_ROW_OBSERVED` is limited to the six checked archives and does not imply a deletion or original-source absence. No restoration proposal was produced.','', 'B5 remains IN_PROGRESS; counts overlap prior inventories. Exact query execution timestamps were not returned by Weather MCP.', '', 'Reproduce with `scripts/build_b5_2019_2020_per_gap_report.py` and `scripts/validate_b5_2019_2020_per_gap_report.py`; frozen SQL/raw results are under year-specific paths.']
(R/'reports/2026-11-14-B5-2019-2020-per-gap-availability.md').write_text('\n'.join(lines)+'\n')
subprocess.run([sys.executable,str(R/'scripts/enrich_b5_2019_2020_source_copy_concordance.py')],check=True)
print(json.dumps({'states':dict(states),'per_year':by_year,'archive_summary':summary},indent=2))
