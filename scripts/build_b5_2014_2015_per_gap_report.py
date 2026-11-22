#!/usr/bin/env python3
"""Build a bounded 2014-2015 six-archive source availability inventory."""
import csv,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
A=('reconstruction','eu','gw1000','eu_old','old_weewx','wh1080')
F=('row_count','outTemp_nonnull','outTemp_zero','outHumidity_nonnull','rain_nonnull','rainRate_nonnull','windSpeed_nonnull','windGust_nonnull','windDir_nonnull','barometer_nonnull','distinct_usUnits','distinct_interval')
records=json.loads((R/'data/b5_2014_gap_per_archive_availability.json').read_text())['records']
raw=json.loads((R/'data/b5_2015_gap_per_archive_raw.json').read_text())
source={a:{r['gap_id']:r for r in z['rows']} for z in raw['archives'] for a in [z['archive']]}
assert set(source)==set(A)
with (R/'reports/2026-11-12-gap-event-catalog.csv').open(newline='',encoding='utf-8') as f:
 for e in csv.DictReader(f):
  if e['utc_year']!='2015' or not 3600<=int(e['delta_seconds'])<86400:continue
  gid=f"2015:{e['prev_ts']}:{e['target_ts']}";per={}
  for a in A:
   q=source[a].get(gid,{})
   per[a]={f:int(q.get(f,0) or 0) for f in F}
  legacy=per['old_weewx']['row_count']>0 and per['wh1080']['row_count']>0
  if not sum(v['row_count'] for v in per.values()):state='NO_SOURCE_ROW_OBSERVED_IN_SIX_ARCHIVES'
  elif legacy and per['old_weewx']['row_count']==per['wh1080']['row_count']:state='LEGACY_COPIES_HAVE_ROWS_AND_EQUAL_COUNTS_ROW_LEVEL_MATCH_NOT_TESTED_HERE'
  elif per['eu_old']['row_count'] and not legacy:state='EU_OLD_ONLY_OR_LEGACY_COUNT_CONFLICT_REVIEW'
  else:state='MIXED_SOURCE_AVAILABILITY_REVIEW'
  records.append({'gap_id':gid,'left_time':int(e['prev_ts']),'right_time':int(e['target_ts']),'gap_seconds':int(e['delta_seconds']),'source_state':state,'per_archive':per,'already_in_ge24h_review':False,'source_copy_identity_or_quality_proven':False})
assert len(records)==66 and len({r['gap_id'] for r in records})==66
S={a:{'gaps_with_rows':sum(r['per_archive'][a]['row_count']>0 for r in records),'rows':sum(r['per_archive'][a]['row_count'] for r in records),'outTemp_nonnull':sum(r['per_archive'][a]['outTemp_nonnull'] for r in records),'outTemp_zero':sum(r['per_archive'][a]['outTemp_zero'] for r in records),'outHumidity_nonnull':sum(r['per_archive'][a]['outHumidity_nonnull'] for r in records)} for a in A}
C=Counter(r['source_state'] for r in records)
out={'schema':'b5-2014-2015-gap-per-archive-source-availability-v1','years':[2014,2015],'scope':'2014 all 37 gaps >=1h plus 2015 29 gaps 1h to <24h; one 2014 >=24h event overlaps existing 44-gap review.','source_query_execution_timestamp':'NOT_CAPTURED_BY_WEATHER_MCP','database_mode':'READ_ONLY_SELECT_ONLY','records':records,'state_counts':dict(C),'per_archive_summary':S,'source_row_sum_non_additive':True,'correction_proposals':0,'limitations':['Source counts include off-grid rows and do not imply expected observations.','Equal old/WH counts do not prove identical timestamps, sensor independence or correct values.','The 2014 >=24h event overlaps prior work.','No omission cause or local meteorological truth is inferred.','B5 remains open across the 24,523-event catalog.']}
(R/'data/b5_2014_2015_per_gap_availability.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-B5-2014-2015-per-gap-availability.csv').open('w',newline='',encoding='utf-8') as f:
 cols=['gap_id','left_time','right_time','gap_seconds','source_state','already_in_ge24h_review']+[f'{a}_{v}' for a in A for v in F];w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
 for r in records:
  q={k:r[k] for k in cols[:6]}
  for a in A:
   for v in F:q[f'{a}_{v}']=r['per_archive'][a][v]
  w.writerow(q)
lines=['# B5: per-gap source availability in the 2014-2015 1h-to-24h cohort','','The six archives were queried separately with READ-ONLY exact-range SELECTs. Scope: 37 events in 2014 (36 <24h; one >=24h overlap) and 29 1h-to-<24h events in 2015. The 2014 long gap is not new evidence.','', '| Archive | Gaps with rows | Rows | outTemp non-NULL | outTemp=0 | RH non-NULL |','|---|---:|---:|---:|---:|---:|']
for a in A:lines.append(f"| `{a}` | {S[a]['gaps_with_rows']} | {S[a]['rows']} | {S[a]['outTemp_nonnull']} | {S[a]['outTemp_zero']} | {S[a]['outHumidity_nonnull']} |")
lines+=['',f"States over 66 gap events: `{json.dumps(dict(C),ensure_ascii=False)}`. Legacy archives both contain rows in 50 events and 1,844 rows each; `eu_old` has 20 rows across 20 events. Reconstruction, EU and GW1000 have no rows inside these open intervals. Sixteen gaps have no observed rows in any archive.",'','The 2015 cohort has 29/29 gaps with legacy source rows (1,050 rows in each archive); 2014 has 21 gaps and 794 rows in each legacy archive. `eu_old` contributes 8 rows in 2015 and 12 in 2014. High WH1080 zero-temperature counts are reported as observations, not automatic sentinels. Equal row counts do not establish timestamp or value concordance.','', 'No correction proposals were created. Availability does not prove expected measurement, source correctness, station downtime or intentional removal. B5 remains IN_PROGRESS. The 2014 >=24h event overlaps prior review; counts must not be added.','', 'Reproduce with `sql/readonly/b5_2014_gap_availability_*.sql`, `sql/readonly/b5_2015_gap_availability_*.sql`, then run this builder and `scripts/validate_b5_2014_2015_per_gap_report.py`. Weather MCP did not return query execution timestamps; none is fabricated.']
(R/'reports/2026-11-14-B5-2014-2015-per-gap-availability.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'gaps':66,'state_counts':dict(C),'per_archive_summary':S},ensure_ascii=False,indent=2))
