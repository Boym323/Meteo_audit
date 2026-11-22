#!/usr/bin/env python3
"""Validate the bounded 2010 off-grid/source-to-occupied-slot evidence."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/source_only_2010_nearest_slot_review.json').read_text())
c=d['cohort']; a=d['alignment']; f=d['nearest_slot_field_comparison']
assert c['target_absent_source_pairs']==1989
assert sum(a['remainder_counts_seconds'].values())==1989
assert '0' not in a['remainder_counts_seconds'] and a['on_grid_rows']==0
assert a['nearest_target_rows_present']==1989 and a['nearest_target_usUnits16_interval5']==1989
assert a['unique_nearest_target_slots']==1983 and a['source_rows_beyond_unique_nearest_slots']==6
assert a['nearest_offset_min_seconds']==60 and a['nearest_offset_max_seconds']==120
assert a['nearest_outTemp_exact_equal']==1955 and a['nearest_outTemp_within_0_3C']==1969
assert c['eu_old_exact_source_rows']==1988 and c['eu_old_exact_outTemp_equal']==1988
assert len(d['projection_collisions'])==6
targets=set()
for x in d['projection_collisions']:
    assert x['target_time']%300==0 and x['target_time'] not in targets;targets.add(x['target_time'])
    assert len(x['source_times'])==len(x['source_outTemp'])==len(x['offset_seconds'])==2
    assert all(t%300 in (60,120,180,240) for t in x['source_times'])
    assert all(abs(t-x['target_time'])==off for t,off in zip(x['source_times'],x['offset_seconds']))
assert c['source_copy_field_concordance_from_frozen_eligibility']['outTemp']['paired_equal']==1989
assert c['source_copy_field_concordance_from_frozen_eligibility']['outHumidity']['paired_equal']==1988
assert f['windSpeed']=={'nonzero_pairs':1957,'ratio_1':1933,'ratio_3_6':0,'other':24}
assert f['windGust']=={'nonzero_pairs':1980,'ratio_1':1968,'ratio_3_6':0,'other':12}
assert d['decision']['classification']=='TIMESTAMP_DUPLICATE_SUSPECTED_REVIEW_REQUIRED'
assert d['decision']['restored_proposals']==d['decision']['estimated_proposals']==0
assert d['safety']['database_access']=='READ_ONLY SELECT' and d['safety']['writes']==0
sql=(ROOT/'sql/readonly/source_only_2010_nearest_slot_review.sql').read_text()
assert '1262304000' in sql and '1293840000' in sql and 'MOD(o.dateTime,300)' in sql
for forbidden in ('INSERT INTO','UPDATE ','DELETE FROM','REPLACE INTO','ALTER TABLE','DROP TABLE'):
    assert forbidden not in sql.upper(),forbidden
report=(ROOT/'reports/2026-11-14-source-only-2010-nearest-slot-review.md').read_text()
assert 'TIMESTAMP_DUPLICATE_SUSPECTED_REVIEW_REQUIRED' in report and 'šest projekcí koliduje' in report
print(json.dumps({'status':'PASS','source_only_rows':1989,'off_grid_rows':1989,'nearest_target_rows':1989,'unique_nearest_target_slots':1983,'collision_groups':6,'temp_exact':1955,'temp_within_0_3C':1969,'disposition':'TIMESTAMP_DUPLICATE_SUSPECTED_REVIEW_REQUIRED','new_proposals':0,'database_writes':0},ensure_ascii=False))
