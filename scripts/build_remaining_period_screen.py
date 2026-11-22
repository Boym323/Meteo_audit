#!/usr/bin/env python3
"""Build conservative monthly/annual availability screens from frozen post-322 snapshots.
These ratios use archive-row denominators, never inferred expected sensor slots.
"""
import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1]
MONTH=R/'reports/2026-11-13-monthly-archive-field-availability-2009-2026.csv'
ANNUAL=R/'reports/2026-11-13-annual-archive-field-availability-2009-2026.csv'
FIELDS=None
def label(y, month=None, variable=''):
    if y==2021:return 'DIAGNOSTIC_ONLY_PROTECTED'
    if y==2018 and (month is None or month<=3):return 'PROTECTED_Q1_2018'
    if variable in ('rain','rainRate'):return 'PROTECTED_E4_RAINFALL_NO_STATISTICAL_CLASSIFICATION'
    if y==2026:return 'PARTIAL_YEAR_REVIEW_REQUIRED'
    return 'REVIEW_REQUIRED_NO_OPERATIONAL_DENOMINATOR_OR_ROW_LEVEL_PROVENANCE'
def run(src,dst,monthly):
    out=[]
    for r in csv.DictReader(src.open()):
        y=int(r['year']); mo=int(r['month_utc']) if monthly else None
        rows=int(r['archive_rows']); nn=int(r['nonnull_rows']) if 'nonnull_rows' in r else rows-int(r['null_rows'])
        out.append({'period':f'{y:04d}-{mo:02d}' if monthly else str(y),'variable':r['variable'],'archive_rows':rows,'nonnull_rows':nn,'null_rows':rows-nn,'nonnull_share_of_archive_rows':f'{nn/rows:.8f}' if rows else '', 'readiness':label(y,mo,r['variable']),'interpretation':'Availability only; this ratio is not expected-slot coverage. Daily/monthly/annual statistics, extremes and records remain uncertified; missing rows may reflect cadence, sensor epoch, outage or loss.'})
    with dst.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    return len(out)
print('monthly_rows',run(MONTH,R/'data/remaining_monthly_period_screen.csv',True))
print('annual_rows',run(ANNUAL,R/'data/remaining_annual_period_screen.csv',False))
