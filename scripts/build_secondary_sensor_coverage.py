#!/usr/bin/env python3
"""Build coverage summaries within observed archive-presence epochs."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'reports/2026-11-12-monthly-sensor-null-coverage.csv'
out=ROOT/'reports/2026-11-13-secondary-sensor-coverage-by-observed-epoch.csv'
rows=list(csv.DictReader(src.open(newline='')))
variables=['outTemp','outHumidity','rain','rainRate','windSpeed','pressure','radiation','UV','pm25','soilMoist1','lightning_distance']
result=[]
for var in variables:
    col=f'{var}_null'
    months=[r['utc_month'] for r in rows if int(r['rows_n'])>int(r[col])]
    if not months: continue
    first,last=months[0],months[-1]
    eligible=[r for r in rows if first<=r['utc_month']<=last and r['utc_month'][:4]!='2021']
    row_n=sum(int(r['rows_n']) for r in eligible)
    available=sum(int(r['rows_n'])-int(r[col]) for r in eligible)
    result.append({'variable':var,'first_observed_utc_month':first,'last_observed_utc_month':last,'eligible_archive_rows_excluding_2021':row_n,'non_null_rows_excluding_2021':available,'null_rows_in_observed_epoch_excluding_2021':row_n-available,'archive_row_availability_pct':f'{100*available/row_n:.4f}' if row_n else '' ,'interpretation':'observed field presence only; not proof of installation/continuous operation'})
with out.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
print(f'Wrote {len(result)} aggregate rows to {out.relative_to(ROOT)}')
