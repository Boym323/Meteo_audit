#!/usr/bin/env python3
"""Validate 2012 off-grid alignment, collisions and merge-conflict aggregates."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/source_only_2012_nearest_slot_review.json').read_text())
c=d['cohort'];a=d['alignment'];f=d['nearest_slot_field_comparison']
assert c['target_absent_source_pairs']==8424
assert sum(a['remainder_counts_seconds'].values())==8424 and a['on_grid_rows']==0
assert a['nearest_reconstruction_rows_present']==8424 and a['nearest_target_usUnits16_interval5']==8424
assert a['unique_nearest_target_slots']==8421 and a['source_rows_beyond_unique_nearest_slots']==3
assert a['nearest_offset_min_seconds']==60 and a['nearest_offset_max_seconds']==120
assert a['nearest_outTemp_exact_equal']==8399 and a['nearest_outTemp_within_0_3C']==8411
assert c['eu_old_exact_source_rows']==8424 and c['current_eu_exact_rows']==c['GW1000_exact_rows']==0
assert c['source_to_source']['outTemp']=={'old_nonnull':8420,'wh_nonnull':8424,'equal':8419,'conflict':1,'wh_only_nonnull':4}
assert c['old_vs_eu_old_equal']=={'outTemp':8416,'outHumidity':8420,'windSpeed':8423,'windGust':8423}
assert len(d['projection_collisions'])==3 and len(d['source_vs_merged_temperature_conflicts'])==8
assert f['windSpeed']=={'raw_equal':8404,'ratio_3_6':0}
assert f['windGust']=={'raw_equal':8410,'ratio_3_6':0}
for x in d['projection_collisions']:
    assert x['target_time']%300==0 and len(x['source_times'])==2
    assert all(t%300 in (60,120,180,240) for t in x['source_times'])
    assert all(abs(t-x['target_time'])==off for t,off in zip(x['source_times'],x['offset_seconds']))
for x in d['source_vs_merged_temperature_conflicts']:
    assert x['LuhaMet_exact'] is False
    assert x['source_time']%300 in (60,120,180,240)
assert d['decision']['classification']=='TIMESTAMP_DUPLICATE_SUSPECTED_REVIEW_REQUIRED_WITH_SOURCE_CONFLICT_SUBSET'
assert d['decision']['restored_proposals']==d['decision']['estimated_proposals']==0
assert d['safety']['database_access']=='READ_ONLY SELECT' and d['safety']['writes']==0
sql=(ROOT/'sql/readonly/source_only_2012_nearest_slot_review.sql').read_text()
assert '1325376000' in sql and '1356998400' in sql and 'MOD(o.dateTime,300)' in sql
for forbidden in ('INSERT INTO','UPDATE ','DELETE FROM','REPLACE INTO','ALTER TABLE','DROP TABLE'):
    assert forbidden not in sql.upper(),forbidden
report=(ROOT/'reports/2026-11-14-source-only-2012-nearest-slot-review.md').read_text()
assert '8 424/8 424' in report and 'TIMESTAMP_DUPLICATE_SUSPECTED_REVIEW_REQUIRED' in report
print(json.dumps({'status':'PASS','source_only_rows':8424,'off_grid_rows':8424,'nearest_target_rows':8424,'unique_nearest_target_slots':8421,'collision_groups':3,'nearest_temp_exact':8399,'eu_old_rows':8424,'eu_old_temperature_conflicts':8,'new_proposals':0,'writes':0},ensure_ascii=False))
