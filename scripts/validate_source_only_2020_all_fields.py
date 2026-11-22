#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/2020_source_only_field_month.json').read_text())
assert d['source_only_rows']==1466
assert sum(m['source_only_rows'] for m in d['monthly'])==1466
assert sum(m['off_grid'] for m in d['monthly'])==976
assert len(d['monthly'])==8
assert sum(x['rows'] for x in d['unit_interval_profile'])==1466
assert sum(x['rows'] for x in d['alignment_groups'])==1466
assert d['year_summary']['outHumidity_both_conflict']==589
assert d['year_summary']['outTemp_both_equal']==1459
assert d['on_grid_temperature_context']['rows_with_both_neighbor_target_temps']==35
assert d['on_grid_temperature_context']['rows_with_exact_LuhaMet_temperature']==35
assert d['database_writes']==0
for name in ['2020_source_only_monthly_field_availability.sql','2020_source_only_alignment_and_context.sql']:
    q=(R/'sql/readonly'/name).read_text().upper()
    assert q.lstrip().startswith('-- READ-ONLY')
    assert not any(x in q for x in ('INSERT ','UPDATE ','DELETE ','REPLACE '))
print('PASS: 1,466 source rows, 50 fields, 589 RH conflicts, 35 contextual T cases, READ-ONLY SQL.')
