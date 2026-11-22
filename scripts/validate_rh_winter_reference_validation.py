#!/usr/bin/env python3
"""Check key facts in the fixed winter RH validation aggregates."""
import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def load(p):
 with (R/p).open(newline='',encoding='utf8') as f:return list(csv.DictReader(f))
w=load('reports/2026-11-13-rh-winter-local-validation.csv')
m=load('reports/2026-11-13-rh-winter-monthly-validation.csv')
s=load('reports/2026-11-13-rh-winter-source-concordance-q1-2019.csv')
get=lambda winter,scope:next(x for x in w if x['winter']==winter and x['scope']==scope)
a=get('2018-19','all_exact_pairs');b=get('2019-20','all_exact_pairs');f=get('2018-19','freeze_local_temp_le_0')
assert int(a['n'])==5563 and abs(float(a['mae_pp'])-44.5124)<0.001
assert int(b['n'])==24295 and abs(float(b['mae_pp'])-6.1970)<0.001
assert int(f['n'])==2001 and abs(float(f['mae_pp'])-44.1062)<0.001
assert sum(int(x['n']) for x in m if x['month_utc'] in {'2019-01','2019-02','2019-03'})==9627
assert len(s)==3 and sum(int(x['both_available']) for x in s)==12564
assert all(int(x['copies_conflict'])==0 and int(x['current_matches_old'])==int(x['both_available']) for x in s)
print('RH winter reference validation aggregates: PASS (two distinct winters, 29,858 exact winter pairs)')
