#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/2013_source_only_field_month.json').read_text())
assert d['source_only_rows']==2025
assert sum(m['source_only_rows'] for m in d['monthly'])==2025
assert len(d['monthly'])==12
assert sum(m['off_grid'] for m in d['monthly'])==2022
assert d['pilot_relationship']['existing_2013_july_source_only_restored_pilot_timestamps']==3
assert d['pilot_relationship']['remaining_source_only_rows']==2022
for m in d['monthly']:
 assert len(m['fields'])==50
 for v in m['fields'].values():
  assert v['both_equal']+v['both_conflict']<=min(v['old_nonnull'],v['wh_nonnull'])
assert d['database_writes']==0
q=(R/'sql/readonly/2013_source_only_monthly_field_availability.sql').read_text().upper()
assert q.lstrip().startswith('-- READ-ONLY')
assert not any(x in q for x in ('INSERT ','UPDATE ','DELETE ','REPLACE '))
print('PASS: 2,025 rows, monthly coverage, 50 fields, pilot overlap, READ-ONLY SQL.')
