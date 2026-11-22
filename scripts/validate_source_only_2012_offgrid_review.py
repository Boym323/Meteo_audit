#!/usr/bin/env python3
"""Local deterministic consistency checks for the read-only 2012 source-only review."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/source_only_2012_offgrid_review.json').read_text())
assert d['scope'].startswith('UTC [2012-01-01, 2013-01-01)')
assert d['source_pair_integrity']['rows_each']==8424
assert d['source_pair_integrity']['distinct_exact_timestamps']==8424
assert sum(x['timestamps'] for x in d['offset_groups'])==8424
assert {x['offset_seconds'] for x in d['offset_groups']}=={-120,-60,60,120}
assert all(x['nearest_target_present']==x['timestamps'] for x in d['offset_groups'])
assert all(x['third_archive_present']==x['timestamps'] for x in d['offset_groups'])
assert sum(x['zero_temp'] for x in d['offset_groups'])==50
assert d['nearest_slot_occupancy']=={
 'source_rows':8424,'distinct_nearest_slots':8421,
 'occupied_slots_with_one_source_time':8418,'occupied_slots_with_two_source_times':3,
 'source_rows_with_nearest_reconstruction_target':8424,'nearest_target_missing':0,'target_interval_min':5}
assert sum(d['source_pair_integrity']['nullsafe_equal'].values()) # structural/nonempty
assert d['disposition']['review_required']==8424
assert d['disposition']['restored']==d['disposition']['estimated']==d['disposition']['missing']==0
assert d['database_writes']==0 and d['protected_q1_2018_proposals']==0 and not d['year_2021_included']
for row in d['copy_anomaly_rows']:
    assert row['utc'].endswith('Z')
    assert row['nearest_target_time'] is not None
result={'status':'PASS','source_rows':8424,'distinct_exact_source_times':8424,
 'offset_bins':4,'nearest_target_rows_present':8424,'distinct_nearest_target_slots':8421,
 'nearest_slot_collision_slots':3,'exact_zero_temperature_rows':50,
 'classified':'8424 REVIEW_REQUIRED / TIMESTAMP_DUPLICATE_SUSPECTED_OR_UNRESOLVED',
 'correction_operations_created':0,'database_writes':0}
(ROOT/'data/source_only_2012_offgrid_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
