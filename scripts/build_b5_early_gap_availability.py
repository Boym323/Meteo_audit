#!/usr/bin/env python3
"""Build bounded READ-ONLY archive availability queries for the existing 2009-2013 1h..<24h B5 gaps."""
import csv,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'reports/2026-11-12-gap-events-over-1h.csv'
out=ROOT/'sql/readonly/b5_2009_2013_gap_availability'
out.mkdir(parents=True,exist_ok=True)
byyear=defaultdict(list)
with source.open(newline='') as f:
 for r in csv.DictReader(f):
  y=int(r['utc_year']); dt=int(r['delta_seconds'])
  if 2009<=y<=2013 and 3600<=dt<86400:
   byyear[y].append({'gap_id':len(byyear[y])+1,'prev_ts':int(r['prev_ts']),'target_ts':int(r['target_ts']),'duration_seconds':dt,'prev_utc':r['prev_utc'],'target_utc':r['target_utc']})
archives={'reconstruction':'loucka_reconstruction','eu':'pocasi-loucka.eu','gw1000':'pocasi-loucka.eu_GW1000','eu_old':'pocasi-loucka.eu_old','old_weewx':'old_weewx','wh1080':'weewx_WH1080'}
fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','barometer']
for year,gaps in sorted(byyear.items()):
 for key,db in archives.items():
  case=' '.join(f"WHEN `dateTime`>{g['prev_ts']} AND `dateTime`<{g['target_ts']} THEN {g['gap_id']}" for g in gaps)
  ranges=' OR '.join(f"(`dateTime`>{g['prev_ts']} AND `dateTime`<{g['target_ts']})" for g in gaps)
  field_metrics=', '.join(f"COUNT(DISTINCT CASE WHEN `{field}` IS NOT NULL THEN gap_id END) AS gaps_with_{field}, SUM(`{field}` IS NOT NULL) AS values_{field}" for field in fields)
  sql=f"SELECT '{key}' AS archive, {len(gaps)} AS gap_count, COUNT(DISTINCT gap_id) AS gaps_with_any_rows, {len(gaps)}-COUNT(DISTINCT gap_id) AS gaps_without_rows, COUNT(*) AS source_rows, {field_metrics} FROM (SELECT CASE {case} ELSE NULL END AS gap_id, {', '.join(f'`{field}`' for field in fields)} FROM `{db}`.`archive` WHERE {ranges}) q;\n"
  (out/f'b5_{year}_{key}_gap_availability.sql').write_text('-- READ-ONLY aggregate; fixed UTC gap episodes from the frozen interval-aware catalog.\n'+sql)
  detail_fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','barometer']
  inner_fields=', '.join(['`dateTime`','`usUnits`','`interval`']+[f'`{field}`' for field in detail_fields])
  detail_metrics=', '.join(['COUNT(*) AS source_rows','SUM(MOD(`dateTime`,300)=0) AS on_300s_grid','SUM(MOD(`dateTime`,300)<>0) AS off_300s_grid','COUNT(DISTINCT `usUnits`) AS distinct_usUnits','COUNT(DISTINCT `interval`) AS distinct_intervals','MIN(`dateTime`) AS first_source_ts','MAX(`dateTime`) AS last_source_ts']+[f'SUM(`{field}` IS NOT NULL) AS nonnull_{field}' for field in detail_fields]+['SUM(`outTemp`=0) AS outTemp_zero_values'])
  detail_sql=f"SELECT gap_id, {detail_metrics} FROM (SELECT CASE {case} ELSE NULL END AS gap_id, {inner_fields} FROM `{db}`.`archive` WHERE {ranges}) q WHERE gap_id IS NOT NULL GROUP BY gap_id ORDER BY gap_id;\n"
  (out/f'b5_{year}_{key}_gap_availability_per_gap.sql').write_text('-- READ-ONLY per-gap aggregate; no raw value rows returned.\n'+detail_sql)
  if key=='old_weewx':
   fields_to_compare=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','barometer','pressure','altimeter']
   comparisons=', '.join([f"SUM(NOT (o.`{f}` <=> w.`{f}`)) AS {f}_old_wh_conflicts, SUM(NOT (o.`{f}` <=> z.`{f}`)) AS {f}_old_euold_conflicts" for f in fields_to_compare]+["SUM(o.`usUnits`<>w.`usUnits`) AS usUnits_old_wh_conflicts", "SUM(o.`interval`<>w.`interval`) AS interval_old_wh_conflicts", "SUM(o.`usUnits`<>z.`usUnits`) AS usUnits_old_euold_conflicts", "SUM(o.`interval`<>z.`interval`) AS interval_old_euold_conflicts"])
   align_sql=f"SELECT o.gap_id, COUNT(*) AS old_source_rows, SUM(w.`dateTime` IS NOT NULL) AS exact_wh1080_matches, SUM(z.`dateTime` IS NOT NULL) AS exact_eu_old_matches, SUM(r.`dateTime` IS NOT NULL) AS exact_reconstruction_matches, SUM(MOD(o.`dateTime`,300)=0) AS on_300s_grid, SUM(MOD(o.`dateTime`,300)<>0) AS off_300s_grid, COUNT(DISTINCT (o.`dateTime`-MOD(o.`dateTime`,300)+IF(MOD(o.`dateTime`,300)>=150,300,0))) AS distinct_nearest_300s_slots, COUNT(*)-COUNT(DISTINCT (o.`dateTime`-MOD(o.`dateTime`,300)+IF(MOD(o.`dateTime`,300)>=150,300,0))) AS source_projection_collisions, SUM(rp.`dateTime` IS NOT NULL) AS rows_projecting_to_occupied_reconstruction_slots, {comparisons} FROM (SELECT CASE {case} ELSE NULL END AS gap_id, `dateTime`, {', '.join(f'`{f}`' for f in fields_to_compare)}, `usUnits`, `interval` FROM `old_weewx`.`archive` WHERE {ranges}) o LEFT JOIN `weewx_WH1080`.`archive` w ON w.`dateTime`=o.`dateTime` LEFT JOIN `pocasi-loucka.eu_old`.`archive` z ON z.`dateTime`=o.`dateTime` LEFT JOIN `loucka_reconstruction`.`archive` r ON r.`dateTime`=o.`dateTime` LEFT JOIN `loucka_reconstruction`.`archive` rp ON rp.`dateTime`=(o.`dateTime`-MOD(o.`dateTime`,300)+IF(MOD(o.`dateTime`,300)>=150,300,0)) WHERE o.gap_id IS NOT NULL GROUP BY o.gap_id ORDER BY o.gap_id;\n"
   (out/f'b5_{year}_oldweewx_cross_archive_exact_alignment.sql').write_text('-- READ-ONLY exact-key and nearest 300-second target check for legacy rows in existing gap windows.\n'+align_sql)
 meta={'year_utc':year,'gap_count':len(gaps),'archive_sources':archives,'availability_fields':fields,'gap_definition':'existing interval-aware transitions in reports/2026-11-12-gap-events-over-1h.csv with 3600 <= delta_seconds < 86400; open interval (prev_ts,target_ts)','excluded_years':[2018,2021],'safety':'SELECT only; no source mutation or correction inference','gaps':gaps}
 (ROOT/f'data/b5_{year}_gap_availability_scope.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 print(year,len(gaps),f'{len(archives)} archive-specific aggregate queries')
