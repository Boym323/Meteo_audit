#!/usr/bin/env python3
import csv,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];d=json.loads((R/'data/2014_target_absent_source_field_availability.json').read_text());a=d['alignment']
assert d['source_only_rows']==1071==a['source_only'] and len(d['common_fields'])==50
assert a['source_rows_by_archive']=={'old_weewx':97228,'weewx_WH1080':97228} and a['target_rows']==96157
assert a['off_grid_source_only']==442 and a['source_only_without_nearby_target']==1064 and a['target_slot_collisions']==1
assert sum(x['source_only'] for x in a['monthly'])==1071
assert len(d['unit_interval_profile'])==1 and d['unit_interval_profile'][0]['rows']==1071
assert d['field_counts']['outTemp']=={'old_nonnull':120,'wh1080_nonnull':1071,'both_equal':120,'both_conflict':0}
assert d['field_counts']['outHumidity']=={'old_nonnull':120,'wh1080_nonnull':0,'both_equal':0,'both_conflict':0}
assert d['longest_run_review']['rows']==122
with (R/'reports/2026-11-13-2014-target-absent-source-field-availability.csv').open() as f:assert sum(1 for _ in csv.DictReader(f))==50
for p in (R/'sql/readonly').glob('2014_target_absent_source_*.sql'):
 s=p.read_text().upper();assert 'SELECT' in s and 'INSERT' not in s and 'UPDATE ' not in s and 'DELETE ' not in s and not re.search(r'\b2021\b',s)
assert d['classification'].startswith('UNRESOLVED_SOURCE_ONLY')
print('PASS: 1,071 source-only timestamps; 50 fields, time offsets, units/interval and READ-ONLY SQL verified.')
