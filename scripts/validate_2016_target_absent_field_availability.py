#!/usr/bin/env python3
import csv,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/2016_target_absent_source_field_availability.json').read_text());a=d['alignment']
assert d['source_only_rows']==16330==a['source_only'] and len(d['common_fields'])==50
assert a['source_rows_by_archive']=={'old_weewx':104785,'weewx_WH1080':104785}
assert a['target_rows']==88455 and a['exact_shared']==88455
assert a['off_grid_source_only']==10587 and a['source_only_without_nearby_target']==16330 and a['target_slot_collisions']==0
assert sum(x['source_only'] for x in a['monthly'])==16330
assert sum(x['rows'] for x in d['unit_interval_profile'])==16330
assert d['field_counts']['outTemp']=={'old_nonnull':2,'wh1080_nonnull':16330,'both_equal':2,'both_conflict':0}
assert d['field_counts']['outHumidity']=={'old_nonnull':0,'wh1080_nonnull':0,'both_equal':0,'both_conflict':0}
with (R/'reports/2026-11-13-2016-target-absent-source-field-availability.csv').open() as f:assert sum(1 for _ in csv.DictReader(f))==50
for p in [R/'sql/readonly/2016_target_absent_source_field_availability.sql',R/'sql/readonly/2016_target_absent_source_timestamp_inventory.sql']:
 s=p.read_text().upper();assert 'SELECT' in s and 'INSERT' not in s and 'UPDATE ' not in s and 'DELETE ' not in s and not re.search(r'\b2021\b',s)
assert d['interpretation'].startswith('UNRESOLVED_SOURCE_ONLY')
print('PASS: 16,330 timestamp cohort; field, unit/interval, monthly and ±150s summaries; SELECT-only SQL verified.')
