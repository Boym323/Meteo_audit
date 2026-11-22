#!/usr/bin/env python3
"""Generate bounded READ-ONLY gap-window availability SQL for existing 2022-2025 B5 episodes."""
import csv,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];src=ROOT/'reports/2026-11-12-gap-events-over-1h.csv';out=ROOT/'sql/readonly/b5_2022_2025_gap_availability';out.mkdir(parents=True,exist_ok=True)
by=defaultdict(list)
with src.open(newline='') as f:
 for r in csv.DictReader(f):
  y=int(r['utc_year']);d=int(r['delta_seconds'])
  if 2022<=y<=2025 and 3600<=d<86400:
   by[y].append({'gap_id':len(by[y])+1,'prev_ts':int(r['prev_ts']),'target_ts':int(r['target_ts']),'delta_seconds':d,'prev_utc':r['prev_utc'],'target_utc':r['target_utc']})
archives={'reconstruction':'loucka_reconstruction','eu':'pocasi-loucka.eu','gw1000':'pocasi-loucka.eu_GW1000','eu_old':'pocasi-loucka.eu_old','old_weewx':'old_weewx','wh1080':'weewx_WH1080'}
fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','barometer']
for y,gaps in sorted(by.items()):
 case=' '.join(f"WHEN `dateTime`>{g['prev_ts']} AND `dateTime`<{g['target_ts']} THEN {g['gap_id']}" for g in gaps)
 ranges=' OR '.join(f"(`dateTime`>{g['prev_ts']} AND `dateTime`<{g['target_ts']})" for g in gaps)
 for key,db in archives.items():
  field_metrics=', '.join(f"COUNT(DISTINCT CASE WHEN `{f}` IS NOT NULL THEN gap_id END) AS gaps_with_{f}, SUM(`{f}` IS NOT NULL) AS values_{f}" for f in fields)
  sql=f"SELECT gap_id,COUNT(*) AS source_rows,SUM(MOD(`dateTime`,300)=0) AS on_300s_grid,SUM(MOD(`dateTime`,300)<>0) AS off_300s_grid,COUNT(DISTINCT `usUnits`) AS distinct_usUnits,MIN(`usUnits`) AS min_usUnits,MAX(`usUnits`) AS max_usUnits,COUNT(DISTINCT `interval`) AS distinct_intervals,MIN(`interval`) AS min_interval,MAX(`interval`) AS max_interval,MIN(`dateTime`) AS first_source_ts,MAX(`dateTime`) AS last_source_ts,{', '.join(f'SUM(`{f}` IS NOT NULL) AS nonnull_{f}' for f in fields)},SUM(`outTemp`=0) AS outTemp_zero_values FROM (SELECT CASE {case} ELSE NULL END AS gap_id,`dateTime`,`usUnits`,`interval`,{','.join(f'`{f}`' for f in fields)} FROM `{db}`.`archive` WHERE {ranges}) q WHERE gap_id IS NOT NULL GROUP BY gap_id ORDER BY gap_id;\n"
  (out/f'b5_{y}_{key}_per_gap.sql').write_text('-- READ-ONLY exact-open-gap aggregate; bounded by frozen UTC candidate intervals.\n'+sql)
  summary_sql=f"SELECT '{key}' AS archive,{len(gaps)} AS gap_count,COUNT(DISTINCT gap_id) AS gaps_with_rows,{len(gaps)}-COUNT(DISTINCT gap_id) AS gaps_without_rows,COUNT(*) AS source_rows,{field_metrics} FROM (SELECT CASE {case} ELSE NULL END AS gap_id,`dateTime`,{','.join(f'`{f}`' for f in fields)} FROM `{db}`.`archive` WHERE {ranges}) q;\n"
  (out/f'b5_{y}_{key}_summary.sql').write_text('-- READ-ONLY six-archive cohort summary; SELECT only.\n'+summary_sql)
 meta={'year_utc':y,'gap_count':len(gaps),'gap_definition':'existing gap catalog; 3600 <= delta_seconds <86400; open interval','archives':archives,'fields':fields,'protected_2021_excluded':True,'gaps':gaps}
 (ROOT/f'data/b5_{y}_gap_availability_scope.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 print(y,len(gaps))
