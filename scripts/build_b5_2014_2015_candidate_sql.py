#!/usr/bin/env python3
"""Build a bounded read-only exact-key source-value query from the frozen 2014-15 gap list."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2014_2015_gap_source_concordance.json').read_text())
rows=d['records']
assert len(rows)==65 and all(x['right_time']>x['left_time'] for x in rows)
case='CASE '+ ' '.join(f"WHEN a.`dateTime`>{x['left_time']} AND a.`dateTime`<{x['right_time']} THEN {x['gap_no']}" for x in rows)+' ELSE NULL END'
where=' OR '.join(f"(a.`dateTime`>{x['left_time']} AND a.`dateTime`<{x['right_time']})" for x in rows)
fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','pressure','barometer','altimeter']
sel=['g.gap_no','g.year_utc','a.`dateTime`','a.`usUnits` AS old_usUnits','a.`interval` AS old_interval','w.`usUnits` AS wh_usUnits','w.`interval` AS wh_interval']
for f in fields:sel.extend([f'a.`{f}` AS old_{f}',f'w.`{f}` AS wh_{f}'])
sel += ['l.`outTemp` AS left_target_outTemp','r.`outTemp` AS right_target_outTemp','ref.`temperature_c` AS luhamet_temp_c','ref.`quality_status` AS luhamet_quality_status','COALESCE(ch.outtemp_events,0) AS outtemp_change_events']
query='''-- READ-ONLY SELECT. Candidate-level source and episode context for the frozen 2014-2015 B5 cohort.
-- All 65 open intervals are exact gap-catalog boundaries; Q1 2018 and 2021 are outside scope.
WITH gaps AS (\n'''+ '\nUNION ALL\n'.join(f"SELECT {x['gap_no']} AS gap_no,{x['year_utc']} AS year_utc,{x['left_time']} AS left_time,{x['right_time']} AS right_time" for x in rows)+'''
)
SELECT '''+',\n       '.join(sel)+'''
FROM gaps g
JOIN `old_weewx`.`archive` a ON a.`dateTime`>g.left_time AND a.`dateTime`<g.right_time
JOIN `weewx_WH1080`.`archive` w ON w.`dateTime`=a.`dateTime`
LEFT JOIN `loucka_reconstruction`.`archive` l ON l.`dateTime`=g.left_time
LEFT JOIN `loucka_reconstruction`.`archive` r ON r.`dateTime`=g.right_time
LEFT JOIN `loucka_reconstruction`.`reference_observations` ref ON ref.`observed_at_utc`=a.`dateTime` AND ref.`station_id`='luhamet_sehradice'
LEFT JOIN (SELECT `target_time`,COUNT(*) AS outtemp_events FROM `loucka_reconstruction`.`reconstruction_changes` WHERE `variable`='outTemp' GROUP BY `target_time`) ch ON ch.`target_time`=a.`dateTime`
WHERE '''+where+'''
ORDER BY g.gap_no,a.`dateTime`;
'''
# use one deterministic CTE gap relation and indexed range joins; no mutation statements.
out=R/'sql/readonly/b5_2014_2015_candidate_level_evidence.sql';out.write_text(query)
print(out)
