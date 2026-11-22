#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];items=json.loads((R/'data/b5_2014_2015_gap_source_concordance.json').read_text())['records']
cte='WITH gaps AS (\n'+'\nUNION ALL\n'.join(f"SELECT {x['gap_no']} AS gap_id,{x['year_utc']} AS year_utc,{x['left_time']} AS left_time,{x['right_time']} AS right_time" for x in items)+'\n)\n'
q=cte+'''SELECT g.gap_id,g.year_utc,a.dateTime,a.usUnits,a.interval,a.outTemp AS source_outTemp,w.outTemp AS wh_outTemp,e.outTemp AS euold_outTemp,e.dateTime AS euold_row_ts,
       a.outHumidity AS old_RH,w.outHumidity AS wh_RH,a.rain AS old_rain,w.rain AS wh_rain,
       a.windSpeed AS old_windSpeed,w.windSpeed AS wh_windSpeed,
       l.outTemp AS left_target_outTemp,r.outTemp AS right_target_outTemp,
       (SELECT x.dateTime FROM `old_weewx`.`archive` x WHERE x.dateTime<a.dateTime ORDER BY x.dateTime DESC LIMIT 1) AS prev_source_ts,
       (SELECT x.outTemp FROM `old_weewx`.`archive` x WHERE x.dateTime<a.dateTime ORDER BY x.dateTime DESC LIMIT 1) AS prev_source_T,
       (SELECT x.dateTime FROM `old_weewx`.`archive` x WHERE x.dateTime>a.dateTime ORDER BY x.dateTime LIMIT 1) AS next_source_ts,
       (SELECT x.outTemp FROM `old_weewx`.`archive` x WHERE x.dateTime>a.dateTime ORDER BY x.dateTime LIMIT 1) AS next_source_T,
       (SELECT t.dateTime FROM `loucka_reconstruction`.`archive` t WHERE t.dateTime BETWEEN a.dateTime-600 AND a.dateTime+600 ORDER BY ABS(t.dateTime-a.dateTime),t.dateTime LIMIT 1) AS nearest_target_ts,
       (SELECT t.outTemp FROM `loucka_reconstruction`.`archive` t WHERE t.dateTime BETWEEN a.dateTime-600 AND a.dateTime+600 ORDER BY ABS(t.dateTime-a.dateTime),t.dateTime LIMIT 1) AS nearest_target_T
FROM gaps g
JOIN `old_weewx`.`archive` a ON a.dateTime>g.left_time AND a.dateTime<g.right_time
JOIN `weewx_WH1080`.`archive` w ON w.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.`archive` e ON e.dateTime=a.dateTime
LEFT JOIN `loucka_reconstruction`.`archive` l ON l.dateTime=g.left_time
LEFT JOIN `loucka_reconstruction`.`archive` r ON r.dateTime=g.right_time
WHERE a.outTemp IS NOT NULL AND a.outTemp<>0
ORDER BY g.year_utc,g.gap_id,a.dateTime;
'''
out=R/'sql/readonly/b5_2014_2015_nonzero_candidate_context.sql';out.write_text('-- READ-ONLY bounded 2014-2015 B5 nonzero source-temperature candidates.\n'+q);print(out)
