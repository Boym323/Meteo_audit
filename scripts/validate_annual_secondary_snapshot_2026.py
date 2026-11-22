#!/usr/bin/env python3
"""Validate 2026 bounded per-field secondary and technical aggregates."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'reports'
rows=list(csv.DictReader((R/'2026-11-13-annual-secondary-sensor-snapshot-2026.csv').open(newline='',encoding='utf-8')))
d=json.loads((R/'2026-11-13-annual-secondary-sensor-snapshot-2026.json').read_text(encoding='utf-8'))
assert len(rows)==42 and len(d['variables'])==42 and len({r['variable'] for r in rows})==42
assert d['rows_n']==86877 and d['first_epoch']==1767225600 and d['last_epoch']==1793286600
for r in rows:
 assert int(r['archive_rows'])==86877
 assert int(r['null_rows'])+int(r['nonnull_rows'])==86877,r['variable']
 if r['min_value'] and r['max_value']: assert float(r['min_value'])<=float(r['max_value']),r['variable']
assert next(r for r in rows if r['variable']=='lightning_energy')['nonnull_rows']=='0'
assert next(r for r in rows if r['variable']=='lightning_disturber_count')['null_rows']=='39278'
print('PASS: 42 fields, 86,877 archive rows, per-field counts and ranges reconcile')
