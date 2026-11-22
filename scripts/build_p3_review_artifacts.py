#!/usr/bin/env python3
"""SUPERSEDED: one-time P3 v2 evidence builder; retained for audit history only."""
raise SystemExit('SUPERSEDED P3 v2 evidence builder; active P3 evidence is frozen in v2.1 package')
import csv,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
pkg=R/'proposals/estimated_short_temperature_gaps_v2'
src=json.loads((pkg/'source_availability_107.json').read_text())
targets=sorted(int(x['target_time']) for x in src['targets'])
fields=['usUnits','interval','outTemp','outHumidity','rain','rainRate','barometer','pressure','altimeter','inTemp','inHumidity','windSpeed','windDir','windGust','windGustDir','dewpoint','windchill','heatindex','ET','radiation','UV','extraTemp1','extraTemp2','soilTemp1','soilTemp2','soilTemp3','soilTemp4','soilMoist1']
vals=',\n'.join(f'({t})' for t in targets)
target_union=' UNION ALL '.join(f'SELECT {t} AS target_time' if i==0 else f'SELECT {t}' for i,t in enumerate(targets))
(R/'sql/readonly/p3_cross_archive_source_availability_107.sql').write_text('''-- Read-only: exact source rows and primary/diagnostic fields for frozen P3 v2 targets.
-- Execute against the connected server with SELECT access to all listed schemas.
'''+ '\nUNION ALL\n'.join(f"SELECT t.target_time, '{db}' AS source_database, a.dateTime AS source_time, "+', '.join('a.`'+f+'`' for f in fields)+f" FROM ({target_union}) t LEFT JOIN `{db}`.archive a ON a.dateTime=t.target_time" for db in src['source_databases'])+';\n')
(R/'sql/readonly/p3_change_event_counts_107.sql').write_text('''-- READ-ONLY count of all-variable reconstruction history events for frozen P3 targets.
SELECT t.target_time, COUNT(c.target_time) AS all_change_events,
 GROUP_CONCAT(DISTINCT c.variable ORDER BY c.variable) AS variables_with_events
FROM ('''+target_union+''') t LEFT JOIN loucka_reconstruction.reconstruction_changes c ON c.target_time=t.target_time
GROUP BY t.target_time ORDER BY t.target_time;\n''')
estimated_ts=sorted(int(x['timestamp']) for x in json.loads((pkg/'corrections.json').read_text()))
estimate_union=' UNION ALL '.join(f'SELECT {t} AS target_time' if i==0 else f'SELECT {t}' for i,t in enumerate(estimated_ts))
offset_sql=[]
for db in src['source_databases']:
 offset_sql.append(f"SELECT t.target_time, '{db}' AS source_database, " + ', '.join(f"MAX(CASE WHEN a.dateTime=t.target_time{d:+d} THEN a.dateTime END) AS offset_{'m' if d<0 else 'p'}{abs(d)}" for d in (-900,-600,-300,300,600,900)) + f" FROM ({estimate_union}) t LEFT JOIN `{db}`.archive a ON a.dateTime IN (t.target_time-900,t.target_time-600,t.target_time-300,t.target_time+300,t.target_time+600,t.target_time+900) GROUP BY t.target_time")
(R/'sql/readonly/p3_source_only_nearby_offsets_24.sql').write_text('-- READ-ONLY exact offset probes around source-free P3 targets; no candidate timestamp shifting is implied.\n'+ '\nUNION ALL\n'.join(offset_sql)+';\n')

# Cross-archive exact-time source evidence as a flat CSV for source-only review.
rows=[]; source_only=[]
for t in src['targets']:
 present=[]
 for db,v in t['sources'].items():
  row={'timestamp':t['target_time'],'source_database':db,'source_row_exists':bool(v['source_row_exists'])}
  row.update(v.get('fields',{})); rows.append(row)
  if v['source_row_exists']: present.append(row)
 if present: source_only.extend(present)
csvpath=R/'proposals/restored_source_only_rows_v2'; csvpath.mkdir(parents=True,exist_ok=True)
with (csvpath/'source_only_rows.csv').open('w',newline='') as f:
 cols=['timestamp','source_database','source_row_exists']+fields
 w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(source_only)
review=[]
for t in src['targets']:
 present=[row for row in source_only if row['timestamp']==t['target_time']]
 if not present: continue
 review.append({'timestamp':t['target_time'],'source_databases':[row['source_database'] for row in present],'classification':'REVIEW_REQUIRED','candidate_variables':sorted({f for row in present for f in fields if f not in ('usUnits','interval') and row.get(f) is not None}), 'reason':'source row is absent from reconstruction archive at this P3 target; archive export role and per-row lineage are not authenticated; do not emit corrections automatically'})
(csvpath/'review_required.json').write_text(json.dumps(review,indent=2)+'\n')
(csvpath/'corrections.json').write_text('[]\n')
(csvpath/'corrections.csv').write_text('operation,timestamp,variable,new_value,expected_old_value,reason\n')
(csvpath/'simulation.json').write_text(json.dumps({'database_access':'none','source_rows_reviewed':len(source_only),'restored':0,'estimated':0,'review_required':len(review),'missing':0,'writes':0,'status':'PASS_REVIEW_ONLY'},indent=2)+'\n')
(csvpath/'README.md').write_text('# P3 source-only multi-variable review\n\nThis bounded package covers 83 source-only target timestamps (165 archive rows across old_weewx and WH1080) that have no reconstruction archive row. All available primary/diagnostic fields are retained. It emits zero RESTORED/ESTIMATED operations because source database role and per-row lineage are unresolved. This is not the broader 2009–2020 source-only inventory; see reports/SOURCE_ONLY_ROWS_2009_2020.md for aggregate coverage, and the SQL for reproducible queries.\n')
(csvpath/'source_metadata.json').write_text(json.dumps({'source_archives':['old_weewx','weewx_WH1080'],'read_mode':'Weather MCP READ_ONLY SELECT snapshot','query_date':'2026-11-13','target_timestamps':83,'archive_source_rows':len(source_only),'expected_target_state':'no row at timestamp in loucka_reconstruction.archive','unit_interval_observed':{'usUnits':[17],'interval_minutes':[5]},'source_role':'not authenticated to original Loučka observations; two copies are not independent'},indent=2)+'\n')
(csvpath/'validation.json').write_text(json.dumps({'method':'exact timestamp source row review; neighbor/context values in P3 v2 evidence','physical_screen':'temperature 4.7..33.4 C; no zero or broad-range sentinel; adjacent jumps <=1.3 C','change_history':'0 events across all variables at 83 targets','confidence':'insufficient for RESTORED because export role and per-row lineage are unverified','disposition':'REVIEW_REQUIRED','uncertainty':'source identity and correctness unresolved; no prediction uncertainty applies because no estimate is emitted'},indent=2)+'\n')
(csvpath/'dependency_metadata.json').write_text(json.dumps({'dependencies':['P3 v2 cross-archive exact-time source snapshot','target state/history query','source archive epoch/unit authentication'],'operations':[],'insert_dependency_order':'none; zero operations','duplicate_policy':'deduplicate by timestamp and variable across active package registry'},indent=2)+'\n')
(csvpath/'excluded_cases.csv').write_text('scope,count,disposition,reason\nall P3 source-only target timestamps,83,REVIEW_REQUIRED,source role and per-row provenance not authenticated\nRESTORED operations,0,EXCLUDED,no source lineage gate passes\nESTIMATED operations,0,EXCLUDED,source values exist; do not estimate around unresolved source conflict\n')
(csvpath/'weather_mcp_batches.json').write_text(json.dumps({'contract':'Weather MCP proposal contract only','max_batch_size':50,'batch_count':0,'batches':[],'reason':'review-only package emits no correction operations; do not create or stage database batches'},indent=2)+'\n')
(csvpath/'validate.py').write_text('''#!/usr/bin/env python3
import json
from pathlib import Path
p=Path(__file__).resolve().parent
m=json.loads((p/'manifest.json').read_text());r=json.loads((p/'review_required.json').read_text());o=json.loads((p/'corrections.json').read_text());b=json.loads((p/'weather_mcp_batches.json').read_text())
assert m['source_timestamps']==83 and m['source_archive_rows']==165 and len(r)==83 and not o
assert m['RESTORED']==0 and m['ESTIMATED']==0 and m['REVIEW_REQUIRED']==83 and b['batch_count']==0
print('PASS: source-only package is review-only with zero operations')
''')
sm={'package':'restored_source_only_rows_v2','scope':'P3 107 targets only','source_timestamps':83,'source_archive_rows':len(source_only),'RESTORED':0,'ESTIMATED':0,'REVIEW_REQUIRED':83,'MISSING':0,'database_access':'READ_ONLY_SELECT_ONLY','writes_or_staging':False,'protected_2021':'diagnostic_only','q1_2018':'excluded','validator':'scripts/validate_source_only_review_package.py','artifacts':{}}
for f in sorted(csvpath.iterdir()):
 if f.is_file() and f.name!='manifest.json':
  b=f.read_bytes();sm['artifacts'][f.name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
(csvpath/'manifest.json').write_text(json.dumps(sm,indent=2)+'\n')

# SQL aggregate expands P1/P2 scope to source-only timestamps without pulling raw rows.
aggregate='''-- READ-ONLY aggregate: source rows without a reconstruction timestamp, 2009–2020 only.
-- Results are screening counts, not approved restoration targets.
SELECT YEAR(FROM_UNIXTIME(a.dateTime)) year, COUNT(*) source_only_rows,
 SUM(a.outTemp IS NOT NULL) outTemp_n, SUM(a.outHumidity IS NOT NULL) outHumidity_n,
 SUM(a.rain IS NOT NULL) rain_n, SUM(a.rainRate IS NOT NULL) rainRate_n,
 SUM(a.barometer IS NOT NULL) barometer_n, SUM(a.windSpeed IS NOT NULL) windSpeed_n,
 SUM(a.windDir IS NOT NULL) windDir_n, SUM(a.dateTime % 300 = 0) on_5m_grid
FROM archive a LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
WHERE a.dateTime >= UNIX_TIMESTAMP('2009-01-01') AND a.dateTime < UNIX_TIMESTAMP('2021-01-01')
 AND r.dateTime IS NULL GROUP BY YEAR(FROM_UNIXTIME(a.dateTime)) ORDER BY year;
'''
(R/'sql/readonly/source_only_primary_availability_2009_2020.sql').write_text(aggregate)
print(json.dumps({'target_source_rows':len(source_only),'target_review_rows':len(review),'sql_targets':len(targets)}))
