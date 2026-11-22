#!/usr/bin/env python3
"""Summarize source-only numeric field availability without loading raw observations."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/p3_independent_review/source_only_common_numeric_fields_2009_2020.json').read_text())
out=[]
for source in d['results']:
 rows=source['rows'];n=sum(int(r['source_only_rows']) for r in rows)
 for field in d['numeric_common_fields']:
  if field in ('year','source_only_rows'):continue
  value=sum(int(r.get(field) or 0) for r in rows)
  out.append({'source_database':source['database'],'variable':field,'source_only_rows':n,'nonnull_rows':value,'nonnull_share':round(value/n,8) if n else None})
p=R/'reports/2026-11-13-source-only-field-availability-2009-2020.csv'
with p.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['source_database','variable','source_only_rows','nonnull_rows','nonnull_share']);w.writeheader();w.writerows(out)
branches=[]
for source in d['results']:
 db=source['database']
 projections=', '.join(f"SUM(a.`{field}` IS NOT NULL) AS `{field}`" for field in d['numeric_common_fields'] if field not in ('year','source_only_rows'))
 branches.append(f"SELECT '{db}' AS source_database, YEAR(FROM_UNIXTIME(a.dateTime)) AS year, COUNT(*) AS source_only_rows, {projections} FROM `{db}`.archive a LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime WHERE a.dateTime>=UNIX_TIMESTAMP('2009-01-01') AND a.dateTime<UNIX_TIMESTAMP('2021-01-01') AND r.dateTime IS NULL GROUP BY YEAR(FROM_UNIXTIME(a.dateTime))")
(R/'sql/readonly/source_only_common_numeric_fields_2009_2020.sql').write_text('-- READ-ONLY aggregate: non-NULL availability for all common numeric columns in exact source-only rows.\n'+'\nUNION ALL\n'.join(branches)+' ORDER BY source_database, year;\n')
bydb={}
for x in out:bydb.setdefault(x['source_database'],{})[x['variable']]=x
def v(db,k):return bydb[db].get(k,{}).get('nonnull_rows')
report=f'''# Source-only numeric field availability, 2009–2020

This is a READ-ONLY aggregate over original archive rows whose exact `dateTime` is absent from `loucka_reconstruction.archive`. It uses the 52 numeric columns common to both source archive schemas (including `usUnits` and `interval`) and does not export individual sensor observations. Reproduction SQL is `sql/readonly/source_only_common_numeric_fields_2009_2020.sql`. Full per-year source-by-field counts are in `data/p3_independent_review/source_only_common_numeric_fields_2009_2020.json`; totals and fractions are in the adjacent CSV.

The two source archives have 207,148 (`old_weewx`) and 207,178 (`weewx_WH1080`) source-only rows, representing 207,182 unique timestamps in their union. Availability varies greatly by channel and epoch. For example, old_weewx has {v('old_weewx','outTemp'):,} non-NULL outTemp, {v('old_weewx','outHumidity'):,} RH, {v('old_weewx','soilTemp1'):,} soilTemp1, and {v('old_weewx','radiation'):,} radiation values. WH1080 has {v('weewx_WH1080','outTemp'):,} outTemp, {v('weewx_WH1080','outHumidity'):,} RH, {v('weewx_WH1080','soilTemp1'):,} soilTemp1, and {v('weewx_WH1080','radiation'):,} radiation values.

These figures broaden the P1/P2 NULL-target inventories to whole source-only rows and show potentially recoverable multi-variable content for P5/O triage. They are not restoration approvals. No row-level lineage/unit/time/history/sentinel/context checks have been performed for this 207,182-timestamp union; whole-row candidates remain `REVIEW_REQUIRED` until those gates pass. Timestamp grid modulo is a screening feature only. Q1 2018 remains excluded from new proposals; year 2021 was not queried.
'''
(R/'reports/SOURCE_ONLY_ROWS_2009_2020.md').write_text(report)
print(json.dumps({'common_numeric_columns':len(d['numeric_common_fields']),'unique_timestamps':207182,'rows_per_archive':{x['database']:sum(int(r['source_only_rows']) for r in x['rows']) for x in d['results']},'field_summary_csv':str(p.relative_to(R))},indent=2))
