#!/usr/bin/env python3
import csv,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/historical_migration_conversion_factor_2009_2020.json').read_text())
assert [x['year'] for x in d['years']]==list(range(2009,2021))
for x in d['years']:
 s=x['stats']
 for f in d['fields']:
  n=lambda k:int(s[f'{f}_{k}'])
  assert n('expected_factor')+n('ratio_1')+n('other_factor')==n('target_nonzero_pairs'),(x['year'],f)
  assert n('target_nonzero_pairs')<=n('source_equal')
with (R/'reports/2026-11-13-historical-migration-conversion-factor-2009-2020.csv').open() as f: assert sum(1 for _ in csv.DictReader(f))==48
files=list((R/'sql/readonly').glob('historical_migration_conversion_factor_*.sql'));assert len(files)==12
for p in files:
 s=p.read_text().upper();assert 'SELECT' in s and 'INSERT' not in s and 'UPDATE ' not in s and 'DELETE ' not in s and not re.search(r'\b2021\b',s)
print('PASS: 12 years × 4 fields; ratio classes partition all nonzero pairs; 12 bounded SELECT-only SQL files.')
