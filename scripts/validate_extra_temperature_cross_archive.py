#!/usr/bin/env python3
"""Validate the bounded extraTemp2 cross-archive aggregate snapshot."""
import csv
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'reports/2026-11-13-extra-temperature-cross-archive.csv'
rows={r['source']:r for r in csv.DictReader(p.open(newline='',encoding='utf-8'))}
expected={
'pocasi-loucka.eu':(790,790,790,790,260),
'pocasi-loucka.eu_GW1000':(790,790,0,0,0),
'pocasi-loucka.eu_old':(790,776,0,0,0),
'old_weewx':(790,0,0,0,0),
'weewx_WH1080':(790,0,0,0,0),
}
assert set(rows)==set(expected)
for name, vals in expected.items():
 r=rows[name]
 actual=tuple(int(r[k]) for k in ('target_n','matched_rows','available_n','exact_matches','distinct_values'))
 assert actual==vals,(name,actual,vals)
assert sum(int(r['exact_matches']) for r in rows.values())==790
print('extraTemp2 cross-archive aggregate: PASS (5 archives, 790 targets)')
