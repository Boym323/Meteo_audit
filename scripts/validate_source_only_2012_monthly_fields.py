#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/2012_source_only_field_month.json').read_text())
assert d['source_only_rows']==8424
assert sum(m['source_only_rows'] for m in d['monthly'])==8424
assert all(m['off_grid']==m['source_only_rows'] for m in d['monthly'])
assert len(d['monthly'])==10
for m in d['monthly']:
    assert len(m['fields'])==50
    for v in m['fields'].values():
        assert 0<=v['old_nonnull']<=m['source_only_rows']
        assert 0<=v['wh_nonnull']<=m['source_only_rows']
        assert v['both_equal']+v['both_conflict']<=min(v['old_nonnull'],v['wh_nonnull'])
assert d['database_writes']==0
q=(R/'sql/readonly/2012_source_only_monthly_field_availability.sql').read_text().upper()
assert q.lstrip().startswith('-- READ-ONLY')
assert not any(x in q for x in ('INSERT ','UPDATE ','DELETE ','REPLACE '))
print('PASS: 8,424 rows, ten months, 50 fields/month, off-grid and READ-ONLY query invariants.')
