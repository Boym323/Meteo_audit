#!/usr/bin/env python3
"""Validate bounded cross-archive result for soilTemp1 < -40."""
import csv
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'reports/2026-11-13-soiltemp1-cross-archive.csv'
rows={r['source']:r for r in csv.DictReader(p.open(newline='',encoding='utf-8'))}
expected={'pocasi-loucka.eu':(1,1,1,1,1),'pocasi-loucka.eu_GW1000':(1,1,0,0,0),'pocasi-loucka.eu_old':(1,1,0,0,0),'old_weewx':(1,0,0,0,0),'weewx_WH1080':(1,0,0,0,0)}
assert set(rows)==set(expected)
for k,v in expected.items(): assert tuple(int(rows[k][c]) for c in ('target_n','matched_rows','available_n','exact_matches','distinct_values'))==v,k
print('soilTemp1 cross-archive aggregate: PASS (1 target, 5 archives)')
