#!/usr/bin/env python3
"""Validate six-archive core availability output against its three source snapshots."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
years=list(range(2009,2021));fields=['outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','barometer','pressure','altimeter','dewpoint']
recon=json.loads((ROOT/'reports/2026-11-13-annual-archive-field-availability-2009-2026.json').read_text())
src=json.loads((ROOT/'data/annual_source_archive_field_availability_2009_2020.json').read_text())
merged=json.loads((ROOT/'data/annual_merged_archive_core_availability_2009_2020.json').read_text())
out=json.loads((ROOT/'data/six_archive_core_availability_2009_2020.json').read_text())
with (ROOT/'reports/2026-11-13-six-archive-core-field-availability-2009-2020.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
archives=['loucka_reconstruction','old_weewx','weewx_WH1080','pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old']
assert len(rows)==792 and len({(x['database'],int(x['year_utc']),x['variable']) for x in rows})==792
assert out['cell_count']==792 and out['archive_count']==6 and out['years_utc']==years and out['fields']==fields
recon_index={(x['year'],x['variable']):x for x in recon['records']}
for row in rows:
 db=row['database'];y=int(row['year_utc']);f=row['variable']; expected=None
 if db=='loucka_reconstruction':
  x=recon_index[(y,f)];expected=(int(recon['year_row_counts'][str(y)]),int(x['nonnull_rows']),int(x['null_rows']))
 elif db in ('old_weewx','weewx_WH1080'):
  x=src['data'][db][y-2009];v=x['fields'][f];expected=(x['archive_rows'],v['nonnull'],v['null'])
 else:
  x=merged['data'][db][y-2009];v=x['fields'][f];expected=(x['archive_rows'],v['nonnull'],v['null'])
 assert (int(row['archive_rows']),int(row['nonnull_rows']),int(row['null_rows']))==expected,(db,y,f)
for db in archives:
 sql=ROOT/'sql/readonly'/f'annual_core_availability_{db}_2009_2020.sql'
 if db in ('old_weewx','weewx_WH1080'):
  # These archives have a separately captured 50-field aggregate; no new core SQL generated here.
  continue
 if db=='loucka_reconstruction':continue
 s=sql.read_text();assert s.count('SELECT COUNT(*) AS archive_rows')==12
 assert 'INSERT ' not in s.upper() and 'UPDATE ' not in s.upper() and 'DELETE ' not in s.upper()
 assert '`'+db+'`.archive' in s and '2021' not in s
pair=next(x for x in out['pairwise_nonnull_count_comparisons'] if x['archive_a']=='pocasi-loucka.eu' and x['archive_b']=='pocasi-loucka.eu_GW1000')
assert pair['row_count_equal_years']==12 and pair['equal_nonnull_counts']==95 and pair['different_nonnull_counts']==37
assert sum(1 for y in years if out['archive_rows_by_year']['pocasi-loucka.eu'][str(y)]!=out['archive_rows_by_year']['pocasi-loucka.eu_GW1000'][str(y)])==0
print('PASS: 792 six-archive cells reconcile; 12/12 new-db annual row counts equal, while 37/132 core field-year non-NULL counts differ; source SQL is SELECT-only and 2021-free.')
