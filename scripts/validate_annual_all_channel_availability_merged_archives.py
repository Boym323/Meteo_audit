#!/usr/bin/env python3
"""Validate completeness, arithmetic, prior row-count concordance, and SELECT-only SQL."""
import csv,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/annual_all_channel_availability_merged_archives_2009_2020.json').read_text())
assert data['years']==list(range(2009,2021))
expected={'pocasi-loucka.eu':77,'pocasi-loucka.eu_GW1000':63,'pocasi-loucka.eu_old':111}
for db,nfields in expected.items():
 items=data['data'][db]; assert len(items)==12
 assert sum(len(x['fields']) for x in items)==nfields*12
 for x in items:
  assert x['year'] in data['years']
  for v in x['fields'].values():
   assert v['nonnull']>=0 and v['null']>=0 and v['nonnull']+v['null']==x['archive_rows'],(db,x['year'],v,x['archive_rows'])
# Prior independent row aggregates.
core=json.loads((ROOT/'data/six_archive_core_availability_2009_2020.json').read_text())
print('core keys',core.keys())
# Derive and compare only where source schemas are represented by prior snapshots.
old=json.loads((ROOT/'data/annual_merged_archive_core_availability_2009_2020.json').read_text())
for db in ['pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old']:
 for item in data['data'][db]:
  # both prior snapshots provide archive rows; field counts stay in their native representation
  prior=old['data'].get(db)
  if prior:
   pi=next(x for x in prior if x['year']==item['year'])
   assert pi.get('archive_rows',pi.get('rows'))==item['archive_rows'],(db,item['year'],pi,item['archive_rows'])
# Six-archive baseline uses a different shape; confirm rows if present.
rows_by_archive=core.get('archive_rows_by_year',{})
for db in ['pocasi-loucka.eu','pocasi-loucka.eu_GW1000']:
 entries=rows_by_archive.get(db)
 if entries:
  for item in data['data'][db]:
   if isinstance(entries,dict): prior=entries[str(item['year'])]
   else: prior=next(x for x in entries if x['year']==item['year'])
   if isinstance(prior,dict): prior=prior.get('archive_rows',prior.get('rows'))
   assert prior==item['archive_rows'],(db,item['year'],prior,item['archive_rows'])
files=list((ROOT/'sql/readonly').glob('annual_all_channel_*.sql'))
assert len(files)==84,len(files)
for p in files:
 s=p.read_text().upper()
 assert 'SELECT' in s and 'INSERT' not in s and 'UPDATE ' not in s and 'DELETE ' not in s
 assert not re.search(r'\b2021\b',s)
 assert 'WHERE `DATETIME` >=' in s and ' AND `DATETIME` < ' in s
csvp=ROOT/'reports/2026-11-13-annual-all-channel-availability-merged-archives-2009-2020.csv'
with csvp.open() as f: count=sum(1 for _ in csv.DictReader(f))
assert count==3012,count
print('PASS: 3,012 archive/year/field cells; values sum to row counts; prior row counts agree where available; 84 SQL files are bounded SELECT-only and exclude 2021.')
