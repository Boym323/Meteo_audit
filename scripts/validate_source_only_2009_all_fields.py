#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];d=json.loads((R/'data/2009_source_only_field_month.json').read_text())
assert d['source_only_rows']==3811
assert sum(m['source_only_rows'] for m in d['monthly'])==3811
assert sum(m['off_grid'] for m in d['monthly'])==3711
assert len(d['monthly'])==10
assert sum(g['rows'] for g in d['unit_interval_profile'])==3811
assert sum(g['rows'] for g in d['alignment_groups'])==3811
assert sum(g['rows'] for g in d['alignment_groups'] if g['projected_target_present']==g['rows'])==3711
assert all(len(m['fields'])==50 for m in d['monthly'])
assert d['strict_copy_pilot']['timestamps']==100 and d['strict_copy_pilot']['classification']=='REVIEW_REQUIRED'
for name in ['2009_source_only_monthly_field_availability.sql','2009_source_only_projected_slot_alignment.sql']:
 q=(R/'sql/readonly'/name).read_text().upper();assert q.lstrip().startswith('-- READ-ONLY');assert not any(k in q for k in ('INSERT ','UPDATE ','DELETE ','REPLACE '))
print('PASS: 3,811 rows, 50 fields/month, 3,711 occupied projected slots, 100 strict review cases, READ-ONLY SQL.')
