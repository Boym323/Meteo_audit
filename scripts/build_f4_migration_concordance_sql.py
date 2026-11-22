#!/usr/bin/env python3
"""Emit one bounded SELECT-only field concordance query for UTC 2014."""
import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1]
meta=R/'reports/2026-11-13-archive-column-metadata.csv'
out=R/'sql/readonly/f4_migration_concordance_2014.sql'
with meta.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
tables={}
for row in rows:
 if row['TABLE_NAME']=='archive':tables.setdefault(row['TABLE_SCHEMA'],set()).add(row['COLUMN_NAME'])
fields=sorted(set.intersection(*(tables[x] for x in ('old_weewx','weewx_WH1080','pocasi-loucka.eu_old')))-{'dateTime','usUnits','interval'})
assert len(fields)==50
select=['SELECT 2014 AS utc_year, COUNT(*) AS source_timestamp_pairs']
for v in fields:
 q=f'`{v}`'
 exprs={
  'old_nonnull':f'o.{q} IS NOT NULL',
  'wh_nonnull':f'w.{q} IS NOT NULL',
  'both_nonnull':f'(o.{q} IS NOT NULL AND w.{q} IS NOT NULL)',
  'source_equal':f'(o.{q} IS NOT NULL AND w.{q} IS NOT NULL AND o.{q}=w.{q})',
  'source_conflict':f'(o.{q} IS NOT NULL AND w.{q} IS NOT NULL AND o.{q}<>w.{q})',
  'merged_nonnull':f'(m.dateTime IS NOT NULL AND m.{q} IS NOT NULL)',
  'merged_matches_old':f'(m.{q} IS NOT NULL AND o.{q} IS NOT NULL AND m.{q}=o.{q})',
  'merged_matches_wh':f'(m.{q} IS NOT NULL AND w.{q} IS NOT NULL AND m.{q}=w.{q})',
  'merged_matches_neither':f'(m.{q} IS NOT NULL AND o.{q} IS NOT NULL AND w.{q} IS NOT NULL AND m.{q}<>o.{q} AND m.{q}<>w.{q})'
 }
 for k,e in exprs.items():select.append(f'  , SUM({e}) AS `{v}__{k}`')
sql='''-- READ-ONLY field-level migration concordance for one bounded UTC year.
-- The source schemas are joined by exact dateTime; merged output is a left join.
-- This detects equality/difference only; it does not authorize transformations.
-- 2021 is outside scope; Q1 2018 is not queried.
'''+ '\n'.join(select)+'''\nFROM `old_weewx`.`archive` o
JOIN `weewx_WH1080`.`archive` w ON w.dateTime=o.dateTime
LEFT JOIN `pocasi-loucka.eu_old`.`archive` m ON m.dateTime=o.dateTime
WHERE o.dateTime >= 1388534400 AND o.dateTime < 1420070400;
'''
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(sql,encoding='utf-8')
print(f'Wrote {out.relative_to(R)} for {len(fields)} shared numeric fields.')
