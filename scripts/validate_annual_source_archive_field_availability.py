#!/usr/bin/env python3
"""Check the captured original-source annual availability aggregates and SQL bounds."""
import csv,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/annual_source_archive_field_availability_2009_2020.json').read_text())
assert len(d['fields'])==50 and d['years']==list(range(2009,2021))
with (ROOT/'reports/2026-11-13-annual-source-archive-field-availability-2009-2020.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
assert len(rows)==1200 and len({(r['database'],int(r['year_utc']),r['variable']) for r in rows})==1200
for db in ('old_weewx','weewx_WH1080'):
 dr=[r for r in rows if r['database']==db]
 assert len(dr)==600
 assert sum(int(x['archive_rows']) for x in dr[::50])==sum(int(y['archive_rows']) for y in d['data'][db])
 for year in d['years']:
  group=[r for r in dr if int(r['year_utc'])==year]
  snap=d['data'][db][year-2009]
  assert len(group)==50 and {x['variable'] for x in group}==set(d['fields'])
  assert all(int(x['archive_rows'])==snap['archive_rows'] for x in group)
  for x in group:
   field=snap['fields'][x['variable']]
   assert int(x['nonnull_rows'])==field['nonnull'] and int(x['null_rows'])==field['null']
 sql=ROOT/'sql/readonly'/f'annual_source_field_availability_{db}_2009_2020.sql'
 text=sql.read_text()
 assert text.count('SELECT COUNT(*) AS archive_rows')==36
 assert 'dateTime >= 1230768000' in text and 'dateTime < 1609459200' in text
 assert '2021' not in text.split('SELECT')[-1] # scope ends before 2021; no 2021 SELECT block
report=(ROOT/'reports/2026-11-13-annual-source-archive-field-availability-2009-2020.md').read_text()
assert 'not measurement validation' in report and 'INVALID_ARGUMENT' in report
assert 'Q1 2018 values are descriptive only' in report and '2021 was not queried' in report
print('PASS: 1,200 CSV cells reconcile to captured read-only aggregates; both SQL files contain 36 UTC-year/field-batch SELECTs limited to 2009–2020.')
