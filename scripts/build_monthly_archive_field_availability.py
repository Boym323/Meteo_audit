#!/usr/bin/env python3
"""Build month-by-field archive availability from bounded yearly SQL aggregates."""
import csv, json
from calendar import month_name
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/monthly_archive_field_availability'
REPORTS=ROOT/'reports'
STEM='2026-11-13-monthly-archive-field-availability-2009-2026'
ANNUAL=REPORTS/'2026-11-13-annual-archive-field-availability-2009-2026.json'

def main():
 annual=json.loads(ANNUAL.read_text()); fields=annual['records']
 field_names=list(dict.fromkeys(x['variable'] for x in fields))
 annual_map={(int(x['year']),x['variable']):x for x in fields}
 matrix=[]; months=[]
 for year in range(2009,2027):
  path=DATA/f'{year}.tsv'
  with path.open(newline='') as f: raw=list(csv.DictReader(f,delimiter='\t'))
  got={int(x['month_utc']):x for x in raw}
  assert len(got)==len(raw)
  for month in range(1,13):
   x=got.get(month)
   rows=int(x['archive_rows']) if x else 0
   nonnull_fields=allnull_fields=partial_fields=0
   for field in field_names:
    nulls=int(x[f'{field}__null']) if x else 0
    nonnull=int(x[f'{field}__nonnull']) if x else 0
    if rows==0: status='NO_ARCHIVE_ROWS'
    elif nonnull==0: status='ALL_NULL'
    elif nulls==0: status='NO_NULL_ON_ARCHIVE_ROWS'
    else: status='PARTIAL_NULL'
    if status=='ALL_NULL':allnull_fields+=1
    elif status=='NO_NULL_ON_ARCHIVE_ROWS':nonnull_fields+=1
    elif status=='PARTIAL_NULL':partial_fields+=1
    null_share=nulls/rows if rows else None
    record={'year':year,'month_utc':month,'variable':field,'archive_rows':rows,'null_rows':nulls,'nonnull_rows':nonnull,'null_share':null_share,'status':status}
    matrix.append(record)
    if x:
     a=annual_map[(year,field)]
     assert nulls+nonnull==rows
   months.append({'year':year,'month_utc':month,'archive_rows':rows,'month_name_utc':month_name[month],
    'available_field_count':len(field_names),'all_null_field_count':allnull_fields,'no_null_field_count':nonnull_fields,
    'partial_null_field_count':partial_fields,'month_status':'NO_ARCHIVE_ROWS' if rows==0 else 'HAS_ARCHIVE_ROWS'})
 # Reconciliation is independent of the output validator: monthly counts must sum to annual SQL counts.
 for key,a in annual_map.items():
  vals=[x for x in matrix if (x['year'],x['variable'])==key]
  assert sum(x['archive_rows'] for x in vals)==int(a['archive_rows'])
  assert sum(x['null_rows'] for x in vals)==int(a['null_rows'])
  assert sum(x['nonnull_rows'] for x in vals)==int(a['nonnull_rows'])
 with (REPORTS/f'{STEM}.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(matrix[0]));w.writeheader();w.writerows(matrix)
 summary={'database':'loucka_reconstruction','time_basis':'UTC explicit Unix-epoch month ranges','years':list(range(2009,2027)),
  'fields':field_names,'field_count':len(field_names),'year_month_count':len(months),'field_month_count':len(matrix),
  'year_month_summary':months,
  'interpretation':'Archive row availability only. NO_ARCHIVE_ROWS is distinct from a month with rows whose field is all NULL; no expected-slot or sensor-installation inference.'}
 (REPORTS/f'{STEM}.json').write_text(json.dumps(summary,indent=2)+'\n')
 lines=['# Měsíční dostupnost 77 číselných archive fields — 2009–2026','',
 'Měsíční agregace používají explicitní UTC epochové hranice a stávající archive rows. Výsledná tabulka má 16 632 kombinací rok/měsíc/pole. `NO_ARCHIVE_ROWS` je odlišeno od měsíce s řádky a celým polem NULL. Nejsou odvozovány očekávané sloty ani data instalace senzorů. Q1 2018 zůstává `INTERIM_LIVE`; rok 2021 je diagnostický; rok 2026 je partial.','',
 '| Rok | Měsíce s archive rows | Měsíce bez archive rows | Field-month ALL_NULL | Field-month PARTIAL_NULL |', '|---:|---:|---:|---:|---:|']
 for y in range(2009,2027):
  m=[x for x in months if x['year']==y]
  lines.append(f"| {y} | {sum(x['archive_rows']>0 for x in m)} | {sum(x['archive_rows']==0 for x in m)} | {sum(x['all_null_field_count'] for x in m)} | {sum(x['partial_null_field_count'] for x in m)} |")
 lines+=['',f'Per-field-month CSV: `{STEM}.csv`; month summary JSON: `{STEM}.json`; SQL: `sql/readonly/monthly_archive_field_availability_2009_2026.sql`.','',
 'Validace porovnává měsíční row/NULL/non-NULL součty s nezávislým ročním agregátem pro všech 77 polí a 18 UTC roků. Absence archive rows sama nerozlišuje odstávku stanice, ztrátu exportu či jiné příčiny.']
 (REPORTS/f'{STEM}.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
