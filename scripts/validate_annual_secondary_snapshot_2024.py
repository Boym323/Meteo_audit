#!/usr/bin/env python3
"""Validate 2024 bounded annual aggregate for 42 fields."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'reports'
rows=list(csv.DictReader((R/'2026-11-13-annual-secondary-sensor-snapshot-2024.csv').open(newline='',encoding='utf-8')))
d=json.loads((R/'2026-11-13-annual-secondary-sensor-snapshot-2024.json').read_text(encoding='utf-8'))
assert len(rows)==42 and len({r['variable'] for r in rows})==42
assert d['rows_n']==104935 and d['first_epoch']==1704067200 and d['last_epoch']==1735689300
for r in rows:
 assert int(r['archive_rows'])==104935
 assert int(r['null_rows'])+int(r['nonnull_rows'])==104935,r['variable']
 if r['min_value'] and r['max_value']:assert float(r['min_value'])<=float(r['max_value']),r['variable']
assert sum(int(r['nonnull_rows'])==0 for r in rows)==11
print('PASS: 2024 annual aggregate, 42 fields and per-field counts/ranges')
