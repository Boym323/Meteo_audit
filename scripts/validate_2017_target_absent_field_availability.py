#!/usr/bin/env python3
import csv,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/2017_target_absent_source_field_availability.json').read_text())
a=d['alignment'];assert d['source_only_rows']==28015==a['source_only']
assert a['source_rows_by_archive']=={'old_weewx':104873,'weewx_WH1080':104873}
assert a['target_rows']==76858 and a['exact_shared']==76858
assert a['source_only_without_target_within_150s']==28015 and a['target_slot_collisions']==0
assert a['off_grid_source_only']==3473 and len(d['common_fields'])==50
assert d['field_counts']['outTemp']=={'old_nonnull':12,'wh1080_nonnull':28015,'both_equal':12,'both_conflict':0}
assert d['field_counts']['outHumidity']=={'old_nonnull':0,'wh1080_nonnull':0,'both_equal':0,'both_conflict':0}
assert d['field_counts']['rainRate']=={'old_nonnull':28015,'wh1080_nonnull':28015,'both_equal':28015,'both_conflict':0}
with (R/'reports/2026-11-13-2017-target-absent-source-field-availability.csv').open() as f:assert sum(1 for _ in csv.DictReader(f))==50
s=(R/'sql/readonly/2017_target_absent_source_field_availability.sql').read_text().upper()
assert 'SELECT' in s and 'INSERT' not in s and 'UPDATE ' not in s and 'DELETE ' not in s and not re.search(r'\b2021\b',s)
assert d['interpretation'].startswith('UNRESOLVED_SOURCE_ONLY')
print('PASS: 28,015 whole-row cohort, 50 field counts, timestamp alignment and READ-ONLY SQL verified.')
