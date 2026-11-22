#!/usr/bin/env python3
"""Generate exact-time READ-ONLY detail queries for short source-covered gaps."""
import csv,hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
GAP=R/'reports/2026-11-12-gap-event-catalog.csv'
EXACT_HOUR='--exact-hour' in sys.argv
OUT=R/('sql/readonly/exact_hour_source_detail' if EXACT_HOUR else 'sql/readonly/short_gap_source_detail');OUT.mkdir(parents=True,exist_ok=True)
DBS=['loucka_reconstruction','pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old','old_weewx','weewx_WH1080']
FIELDS=['outTemp','outHumidity','rain','rainRate','barometer','pressure','altimeter','inTemp','inHumidity','windSpeed','windDir','windGust','windGustDir','dewpoint','windchill','heatindex','ET','radiation','UV','extraTemp1','extraTemp2','soilTemp1','soilTemp2','soilTemp3','soilTemp4','soilMoist1']
Q1=(1514764800,1522540800)
events=[]
with GAP.open(newline='',encoding='utf-8') as f:
 for r in csv.DictReader(f):
  year=int(r['utc_year']);left=int(r['prev_ts']);right=int(r['target_ts']);delta=int(r['delta_seconds'])
  if not 2009<=year<=2020 or r['exceeds_both_steps']!='1' or delta%300 or (delta!=3600 if EXACT_HOUR else (delta>=3600 or delta<=300)):continue
  gid=f'{year}:{left}:{right}'
  for ts in range(left+300,right,300):
   events.append((ts,left,right,gid,delta,'PROTECTED_Q1_2018_DIAGNOSTIC' if Q1[0]<=ts<Q1[1] else 'NORMAL'))
events.sort()
if len({x[0] for x in events})!=len(events):raise AssertionError('duplicate target timestamps')
chunks=[events[i:i+300] for i in range(0,len(events),300)]
manifest=[]
for ci,chunk in enumerate(chunks,1):
 cte=' UNION ALL '.join((f"SELECT {ts} target_time,{left} left_time,{right} right_time,'{gid}' gap_id,{delta} gap_seconds,'{scope}' protection_scope" if j==0 else f"SELECT {ts},{left},{right},'{gid}',{delta},'{scope}'") for j,(ts,left,right,gid,delta,scope) in enumerate(chunk))
 branches=[]
 for db in DBS:
  cols=', '.join(f'a.`{f}` AS `{f}`' for f in FIELDS)
  branches.append(f"SELECT '{db}' source_database,t.target_time,t.gap_id,t.gap_seconds,t.protection_scope,a.usUnits source_usUnits,a.interval source_interval,{cols},p.dateTime source_prev_time,p.outTemp source_prev_outTemp,n.dateTime source_next_time,n.outTemp source_next_outTemp,l.outTemp left_outTemp,r.outTemp right_outTemp,l.outHumidity left_outHumidity,r.outHumidity right_outHumidity,l.rain left_rain,r.rain right_rain,(SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=t.target_time) change_event_count,(SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=t.target_time AND c.variable='outTemp') outTemp_change_event_count,(SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=t.target_time AND c.variable='outHumidity') outHumidity_change_event_count,(SELECT COUNT(*) FROM loucka_reconstruction.reconstruction_changes c WHERE c.target_time=t.target_time AND c.variable='rain') rain_change_event_count FROM targets t JOIN `{db}`.archive a ON a.dateTime=t.target_time LEFT JOIN `{db}`.archive p ON p.dateTime=t.target_time-300 LEFT JOIN `{db}`.archive n ON n.dateTime=t.target_time+300 LEFT JOIN loucka_reconstruction.archive l ON l.dateTime=t.left_time LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=t.right_time LEFT JOIN loucka_reconstruction.archive current_row ON current_row.dateTime=t.target_time WHERE current_row.dateTime IS NULL")
 sql='''-- READ-ONLY exact-time source evidence. Aggregate source exports locally; no correction is implied.
-- Q1 2018 targets are diagnostic/protected. 2021 is excluded by target generation.
WITH targets AS ('''+cte+''')
'''+ '\nUNION ALL\n'.join(branches)+'''
ORDER BY target_time,source_database;
'''
 prefix='exact_hour_source_detail' if EXACT_HOUR else 'short_gap_source_detail'
 path=OUT/f'{prefix}_{ci:03d}.sql';path.write_text(sql)
 manifest.append({'chunk':ci,'targets':len(chunk),'sql':str(path.relative_to(R)),'sql_bytes':path.stat().st_size,'sql_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
selection='2009-2020 only; exceeds_both_steps; delta divisible by 300; interior 300-second targets; delta exactly 3600 seconds' if EXACT_HOUR else '2009-2020 only; exceeds_both_steps; delta divisible by 300; interior 300-second targets; delta < 3600 and > 300 seconds'
index={'snapshot':'reports/2026-11-12-gap-event-catalog.csv','selection':selection,'candidate_targets':len(events),'protected_q1_2018_targets':sum(x[5]=='PROTECTED_Q1_2018_DIAGNOSTIC' for x in events),'excluded_2021':True,'databases':DBS,'fields':FIELDS,'chunks':manifest}
index_name='exact_hour_source_detail_query_index.json' if EXACT_HOUR else 'short_gap_source_detail_query_index.json'
(R/'data'/index_name).write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'candidate_targets':len(events),'protected_q1_2018_targets':index['protected_q1_2018_targets'],'chunks':len(chunks),'largest_query_bytes':max(x['sql_bytes'] for x in manifest)},indent=2))
