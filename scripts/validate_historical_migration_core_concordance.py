#!/usr/bin/env python3
import csv,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/historical_migration_core_exact_concordance_2009_2020.json').read_text())
assert [x['year'] for x in d['years']]==list(range(2009,2021))
for x in d['years']:
 s=x['stats']; assert int(s['union_keys'])>=max(int(s[f'rows_{i}']) for i in range(3))
 for f in d['fields']:
  n=lambda k:int(s[f'{f}_{k}'])
  assert n('source_equal')+n('source_conflict')==n('both_sources'),(x['year'],f)
  assert n('target_with_source_agreement')==n('target_same_raw')+n('target_changed_raw'),(x['year'],f)
  assert n('target_same_raw')+n('target_changed_raw')+n('target_null')<=n('source_equal'),(x['year'],f)
with (R/'reports/2026-11-13-historical-migration-core-exact-concordance-2009-2020.csv').open() as f: assert sum(1 for _ in csv.DictReader(f))==120
files=list((R/'sql/readonly').glob('historical_migration_core_concordance_*.sql'));assert len(files)==12
for p in files:
 s=p.read_text().upper();assert 'SELECT' in s and 'INSERT' not in s and 'UPDATE ' not in s and 'DELETE ' not in s and not re.search(r'\b2021\b',s)
print('PASS: 12 years × 10 fields; concordance arithmetic consistent; 12 bounded SELECT-only SQL files.')
