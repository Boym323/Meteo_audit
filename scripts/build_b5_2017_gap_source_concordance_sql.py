#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2017_per_gap_availability.json').read_text())
records=d['records']; assert len(records)==263 and all(x['gap_seconds']<86400 for x in records)
parts=[]
for i,x in enumerate(records,1):
 parts.append(f"SELECT {i} AS gap_no, {x['left_time']} AS left_time, {x['right_time']} AS right_time")
fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','pressure','barometer','altimeter']
select=['g.gap_no','g.left_time','g.right_time','COUNT(k.dateTime) AS source_union_timestamps','SUM(o.dateTime IS NOT NULL) AS old_rows','SUM(w.dateTime IS NOT NULL) AS wh1080_rows','SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL) AS exact_timestamp_pairs','SUM(o.dateTime IS NOT NULL AND w.dateTime IS NULL) AS old_only_timestamps','SUM(o.dateTime IS NULL AND w.dateTime IS NOT NULL) AS wh1080_only_timestamps','SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND (o.usUnits<>w.usUnits OR o.interval<>w.interval)) AS unit_interval_conflicts']
for f in fields:
 select += [f"SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`{f}` IS NOT NULL AND w.`{f}` IS NOT NULL) AS `{f}_paired_nonnull`",f"SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`{f}` IS NOT NULL AND w.`{f}` IS NOT NULL AND o.`{f}`=w.`{f}`) AS `{f}_equal`",f"SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND o.`{f}` IS NOT NULL AND w.`{f}` IS NOT NULL AND o.`{f}`<>w.`{f}`) AS `{f}_conflict`",f"SUM(o.dateTime IS NOT NULL AND w.dateTime IS NOT NULL AND ((o.`{f}` IS NULL)<>(w.`{f}` IS NULL))) AS `{f}_null_asymmetry`"]
sql='-- READ-ONLY exact source-copy key/value concordance for 2017 source rows inside the frozen 263 1h-to-<24h target gaps. No inference of omission cause or restoration eligibility.\nWITH gaps AS (\n'+' UNION ALL\n'.join(parts)+"\n), source_keys AS (\n SELECT g.gap_no,a.dateTime FROM gaps g JOIN old_weewx.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time\n UNION\n SELECT g.gap_no,a.dateTime FROM gaps g JOIN weewx_WH1080.archive a ON a.dateTime>g.left_time AND a.dateTime<g.right_time\n)\nSELECT\n "+',\n '.join(select)+"\nFROM gaps g LEFT JOIN source_keys k ON k.gap_no=g.gap_no\nLEFT JOIN old_weewx.archive o ON o.dateTime=k.dateTime\nLEFT JOIN weewx_WH1080.archive w ON w.dateTime=k.dateTime\nGROUP BY g.gap_no,g.left_time,g.right_time ORDER BY g.gap_no;\n"
out=R/'sql/readonly/b5_2017_gap_source_concordance.sql';out.write_text(sql)
print(json.dumps({'status':'PASS','gap_events':len(records),'sql_bytes':len(sql.encode()),'fields':fields,'only_select':True},indent=2))
