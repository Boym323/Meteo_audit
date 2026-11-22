#!/usr/bin/env python3
"""Validate 2009–2026 monthly field matrix against annual aggregates."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports';STEM='2026-11-13-monthly-archive-field-availability-2009-2026'
def main():
 d=json.loads((R/f'{STEM}.json').read_text());a=json.loads((R/'2026-11-13-annual-archive-field-availability-2009-2026.json').read_text())
 assert d['field_count']==77 and d['year_month_count']==216 and d['field_month_count']==16632
 assert len(d['year_month_summary'])==216
 with (R/f'{STEM}.csv').open(newline='') as f: rows=list(csv.DictReader(f))
 assert len(rows)==16632
 by={(int(x['year']),int(x['month_utc']),x['variable']):x for x in rows};assert len(by)==16632
 annual={(int(x['year']),x['variable']):x for x in a['records']}
 for (year,field),ar in annual.items():
  group=[by[(year,m,field)] for m in range(1,13)]
  assert sum(int(x['archive_rows']) for x in group)==int(ar['archive_rows'])
  assert sum(int(x['null_rows']) for x in group)==int(ar['null_rows'])
  assert sum(int(x['nonnull_rows']) for x in group)==int(ar['nonnull_rows'])
  for x in group:
   n=int(x['archive_rows']);nulls=int(x['null_rows']);nonnull=int(x['nonnull_rows'])
   assert nulls+nonnull==n
   if n==0: assert x['status']=='NO_ARCHIVE_ROWS' and x['null_share']==''
   elif nonnull==0: assert x['status']=='ALL_NULL' and float(x['null_share'])==1
   elif nulls==0: assert x['status']=='NO_NULL_ON_ARCHIVE_ROWS' and float(x['null_share'])==0
   else: assert x['status']=='PARTIAL_NULL' and 0<float(x['null_share'])<1
 # Monthly row totals also reconcile to each annual denominator.
 for y in range(2009,2027):
  total=sum(int(by[(y,m,d['fields'][0])]['archive_rows']) for m in range(1,13))
  assert total==int(a['year_row_counts'][str(y)])
 assert (R/f'{STEM}.md').stat().st_size>500
 print('PASS: 77 fields × 216 UTC months = 16,632 field-month rows')
 print('PASS: monthly row/null/non-NULL counts reconcile to all 1,386 annual field-year aggregates')
 print('PASS: NO_ARCHIVE_ROWS, ALL_NULL, PARTIAL_NULL and no-NULL statuses are distinct')
if __name__=='__main__':main()
