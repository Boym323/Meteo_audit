#!/usr/bin/env python3
"""Validate saved 2011 target-absent episode summary; performs no DB operations."""
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/2011_target_absent_source_episode_screen.json').read_text())
assert d['database_access']=='READ_ONLY' and d['database_writes']==0
assert d['protected_2021']=='not queried'
assert d['total']['source_rows']==4468 and d['total']['distinct_timestamps']==4468
assert d['total']['contiguous_300s_runs']==12 and d['total']['off_grid_300s']==7
assert d['total']['monthly_utc']=={'2011-07':443,'2011-08':4025}
assert sum(e['rows'] for e in d['episodes'])==4460
assert sum(e['rows'] for e in d['episodes'] if 'SOURCE_SENSOR_STUCK_SUSPECTED' in e['classification'])==3551
assert sum(e['rows'] for e in d['episodes'] if e['classification']=='UNRESOLVED_SOURCE_ONLY')==909
assert sum(e['rows'] for e in d['episodes'] if e['pocasi_loucka_rows'] or e['pocasi_loucka_gw1000_rows'])==0
assert 'No RESTORED proposal' in d['decision']
sql=(R/'sql/readonly/source_target_absent_2011_timestamp_list.sql').read_text().upper()
assert 'SELECT' in sql and 'INSERT' not in sql and 'UPDATE ' not in sql and 'DELETE ' not in sql and '2021' not in sql
assert (R/'reports/2026-11-13-2011-target-absent-source-episodes.md').exists()
print('PASS: 4,468 timestamp summary; episode partition, protected scope and SELECT-only SQL verified.')
