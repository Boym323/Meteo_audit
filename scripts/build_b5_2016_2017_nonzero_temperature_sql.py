#!/usr/bin/env python3
"""Build compact source-candidate SQL only for gap intervals with old outTemp candidates."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
recs=[]
for y in (2016,2017):
 p=json.loads((R/f'data/b5_{y}_per_gap_availability.json').read_text())
 for x in p['records']:
  a=x['per_archive']['old_weewx']
  if a['outTemp_nonnull']:
   recs.append({'year':y,'left':x['left_time'],'right':x['right_time']})
assert len(recs)>0
cte='WITH gaps AS (\n'+'\nUNION ALL\n'.join(f"SELECT {i+1} AS gap_id,{x['year']} AS year_utc,{x['left']} AS left_time,{x['right']} AS right_time" for i,x in enumerate(recs))+'\n)\n'
fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','barometer','pressure','altimeter']
sel=['g.gap_id','g.year_utc','g.left_time','g.right_time','a.dateTime','a.usUnits AS old_usUnits','a.interval AS old_interval','w.usUnits AS wh_usUnits','w.interval AS wh_interval']
for f in fields:sel.extend([f'a.`{f}` AS old_{f}',f'w.`{f}` AS wh_{f}'])
sel.extend(['e.dateTime AS euold_dateTime','e.usUnits AS euold_usUnits','e.interval AS euold_interval','e.outTemp AS euold_outTemp','l.outTemp AS left_target_outTemp','r.outTemp AS right_target_outTemp','ref.temperature_c AS luhamet_temperature_c','ref.quality_status AS luhamet_quality_status','ch.event_count AS outTemp_event_count'])
q=cte+'SELECT '+',\n       '.join(sel)+'''\nFROM gaps g
JOIN `old_weewx`.`archive` a ON a.dateTime>g.left_time AND a.dateTime<g.right_time
JOIN `weewx_WH1080`.`archive` w ON w.dateTime=a.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.`archive` e ON e.dateTime=a.dateTime
LEFT JOIN `loucka_reconstruction`.`archive` l ON l.dateTime=g.left_time
LEFT JOIN `loucka_reconstruction`.`archive` r ON r.dateTime=g.right_time
LEFT JOIN `loucka_reconstruction`.`reference_observations` ref ON ref.observed_at_utc=a.dateTime AND ref.station_id='luhamet_sehradice'
LEFT JOIN (SELECT target_time,COUNT(*) AS event_count FROM `loucka_reconstruction`.`reconstruction_changes` WHERE variable='outTemp' GROUP BY target_time) ch ON ch.target_time=a.dateTime
WHERE a.outTemp IS NOT NULL AND a.outTemp<>0
ORDER BY g.year_utc,g.gap_id,a.dateTime;
'''
out=R/'sql/readonly/b5_2016_2017_nonzero_temperature_candidates.sql';out.write_text('-- READ-ONLY SELECT; bounded to existing gaps with old_weewx nonzero outTemp candidates.\n'+q);print(f'created {out}; selected_gap_ranges={len(recs)}')
