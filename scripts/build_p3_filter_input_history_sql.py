#!/usr/bin/env python3
"""Build read-only history query for every P3 v2 input/filter timestamp and variable."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
meta=json.loads((R/'proposals/estimated_short_temperature_gaps_v2/candidate_metadata.json').read_text())
selected=[r for r in meta if r['p3_v2_status']=='ESTIMATED']
roles={}
for r in selected:
 t=int(r['timestamp']);roles[(t,'TARGET')]=1
 roles[(int(r['left']['t']),'LEFT_ENDPOINT')]=1;roles[(int(r['right']['t']),'RIGHT_ENDPOINT')]=1
role_sql=' UNION ALL '.join((f"SELECT {t} AS event_time, '{role}' AS event_role" if i==0 else f"SELECT {t}, '{role}'") for i,(t,role) in enumerate(sorted(roles)))
vars=['outTemp','outHumidity','rain','rainRate','windSpeed']
var_sql=' UNION ALL '.join((f"SELECT '{v}' AS variable" if i==0 else f"SELECT '{v}'") for i,v in enumerate(vars))
sql='''-- READ-ONLY audit of value provenance for P3 estimate-selection inputs.
-- Target outTemp is absent; endpoint/context history is checked for every filter variable.
WITH role_times AS ('''+role_sql+'''), filter_variables AS ('''+var_sql+''')
SELECT rt.event_time,rt.event_role,a.dateTime AS archive_row_present,
       a.usUnits,a.interval,a.outTemp,a.outHumidity,a.rain,a.rainRate,a.windSpeed,
       fv.variable,c.id AS change_id,c.state AS change_state,c.batch_key,
       c.old_value,c.new_value,c.source_database,c.source_time,c.source_value,
       c.reason,c.created_at,c.applied_at
FROM role_times rt CROSS JOIN filter_variables fv
LEFT JOIN loucka_reconstruction.archive a ON a.dateTime=rt.event_time
LEFT JOIN loucka_reconstruction.reconstruction_changes c
 ON c.target_time=rt.event_time AND c.variable=fv.variable
ORDER BY rt.event_time,rt.event_role,fv.variable,c.id;
'''
p=R/'sql/readonly/p3_filter_input_history_2019_2020.sql';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(sql)
idx={'targets':len(selected),'role_time_pairs':len(roles),'variables':vars,'query':str(p.relative_to(R)),'sql_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'all active P3 v2 ESTIMATED targets plus their selected left/right endpoint values; context variables are outTemp,outHumidity,rain,rainRate,windSpeed'}
(R/'data/p3_filter_input_history_query_index.json').write_text(json.dumps(idx,indent=2)+'\n')
print(json.dumps(idx,indent=2))
