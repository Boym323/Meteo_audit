#!/usr/bin/env python3
"""Build bounded read-only exact-time source queries for conditional 5-minute gap slots.

This is a screening overlay only. It does not assert that all 5-minute slots were expected.
"""
import csv,hashlib,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
GAP=R/'reports/2026-11-12-gap-event-catalog.csv'
OUT=R/'sql/readonly/gap_slot_source_availability'
OUT.mkdir(parents=True,exist_ok=True)
CHUNK_DIR=OUT/'chunks';CHUNK_DIR.mkdir(parents=True,exist_ok=True)
FIELDS=['usUnits','interval','outTemp','outHumidity','rain','rainRate','barometer','pressure','altimeter','inTemp','inHumidity','windSpeed','windDir','windGust','windGustDir','dewpoint','windchill','heatindex','ET','radiation','UV','extraTemp1','extraTemp2','soilTemp1','soilTemp2','soilTemp3','soilTemp4','soilMoist1']
DBS=['loucka_reconstruction','pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old','old_weewx','weewx_WH1080']
PROTECTED_START=1514764800;PROTECTED_END=1522540800
byyear={};excluded=Counter(); total_gap_rows=0
with GAP.open(newline='',encoding='utf-8') as f:
 for row in csv.DictReader(f):
  y=int(row['utc_year']);total_gap_rows+=1
  if y==2021:
   excluded['year_2021_gap_events']+=1;continue
  if not 2009<=y<=2020:continue
  if row['exceeds_both_steps']!='1':
   excluded['not_exceeding_both_interval_steps']+=1;continue
  left=int(row['prev_ts']);right=int(row['target_ts']);delta=int(row['delta_seconds'])
  if delta%300:
   excluded['not_aligned_to_300_second_grid']+=1;continue
  band='lt_1h' if delta<3600 else ('1h_to_lt_1d' if delta<86400 else 'ge_1d')
  if delta<=300:continue
  gap_id=f"{y}:{left}:{right}"
  protected=left+300>=PROTECTED_START and right-300<PROTECTED_END
  # Store gap intervals, not every candidate timestamp. SQL expands them by an
  # indexed source-row range join plus exact modulo-300 alignment.
  slots=byyear.setdefault(y,[])
  slots.append((left,right,gap_id,delta,band))

summary={'snapshot_date':'2026-11-12 gap event catalog; current target state rechecked at query time','source_archives':DBS,'fields':FIELDS,'candidate_slot_rule':'interior timestamps on previous-endpoint + 300-second lattice; only events flagged exceeds_both_steps and delta multiple of 300 seconds','interpretation':'conditional candidate slots, not an assertion that all were expected observations','gap_event_catalog_rows':total_gap_rows,'excluded':dict(excluded),'years':{}}
query_manifest=[]
for year,items in sorted(byyear.items()):
 seen=set()
 for x in items:
  key=(x[0],x[1])
  if key in seen:raise AssertionError(f'duplicate candidate gap {year} {key}')
  seen.add(key)
 select_fields=', '.join(f'a.`{f}`' for f in FIELDS)
 def make_sql(chunk):
  target_union=' UNION ALL '.join(f"SELECT {left} AS left_time, {right} AS right_time, '{gid}' AS gap_id, {delta} AS gap_seconds, '{band}' AS gap_band" if i==0 else f"SELECT {left}, {right}, '{gid}', {delta}, '{band}'" for i,(left,right,gid,delta,band) in enumerate(chunk))
  branches=[]
  for db in DBS:
   branches.append(f"SELECT '{db}' AS source_database, t.gap_band, CASE WHEN a.dateTime >= {PROTECTED_START} AND a.dateTime < {PROTECTED_END} THEN 'PROTECTED_Q1_2018_DIAGNOSTIC' ELSE 'NORMAL' END AS protection_scope, t.gap_id, a.dateTime AS target_time, {select_fields} FROM targets t JOIN `{db}`.archive a ON a.dateTime>t.left_time AND a.dateTime<t.right_time AND MOD(a.dateTime-t.left_time,300)=0 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime WHERE r.dateTime IS NULL")
  return '''-- READ-ONLY source-first overlay: exact source records on conditional interior 5-minute slots.
-- Historical snapshot basis: reports/2026-11-12-gap-event-catalog.csv.
-- This query does not assert those slots were expected; source matches are review candidates only.
WITH targets AS ('''+target_union+'''), matches AS ('''+ '\nUNION ALL\n'.join(branches)+''')
SELECT source_database, gap_band, protection_scope, COUNT(*) AS source_archive_rows,
 COUNT(DISTINCT target_time) AS unique_target_timestamps, COUNT(DISTINCT gap_id) AS gaps_with_source,
 '''+',\n '.join(f'SUM(`{f}` IS NOT NULL) AS `{f}_nonnull`' for f in FIELDS)+'''
FROM matches GROUP BY source_database, gap_band, protection_scope ORDER BY source_database, gap_band, protection_scope;
'''
 chunks=[items[i:i+250] for i in range(0,len(items),250)]
 for ci,chunk in enumerate(chunks,1):
  sql=make_sql(chunk);path=CHUNK_DIR/f'gap_slot_source_availability_{year}_{ci:03d}.sql';path.write_text(sql)
  query_manifest.append({'year':year,'chunk':ci,'gap_events':len(chunk),'sql':str(path.relative_to(R)),'sql_bytes':path.stat().st_size,'sql_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 # retain a concise yearly README/query recipe pointer, not an oversized SQL payload.
 path=OUT/f'gap_slot_source_availability_{year}.sql'
 path.write_text(f"-- Chunked read-only exact timestamp query set. See {CHUNK_DIR.relative_to(R)}/gap_slot_source_availability_{year}_*.sql\n")
 c=Counter(x[4] for x in items);candidate=sum((x[1]-x[0])//300-1 for x in items);q1=sum(max(0,(min(x[1],PROTECTED_END-1)-max(x[0]+300,PROTECTED_START)+300)//300) for x in items)
 summary['years'][str(year)]={'candidate_slots':candidate,'gap_events':len(items),'slots_by_band':dict(c),'protected_q1_2018_slots':q1,'sql_chunks':sum(q['year']==year for q in query_manifest),'sql':str(path.relative_to(R))}
summary['query_chunks']=query_manifest
(R/'data/p1p2_source_gap_overlay_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'years':{y:{'candidate_slots':v['candidate_slots'],'gap_events':v['gap_events'],'sql_chunks':v['sql_chunks']} for y,v in summary['years'].items()},'total_candidate_slots':sum(v['candidate_slots'] for v in summary['years'].values()),'query_chunks':len(query_manifest),'excluded':summary['excluded']},ensure_ascii=False,indent=2))
