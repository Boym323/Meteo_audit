#!/usr/bin/env python3
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'data/source_only_2013_nearest_slot_review.json';d=json.loads(p.read_text())
assert d['cohort']['source_only_timestamps']==2025 and d['cohort']['exact_target_rows']==0
assert d['alignment']['on_grid_rows']==3 and d['alignment']['off_grid_rows']==2022
assert sum(d['alignment']['off_grid_remainders_seconds'].values())==2022
assert sum(d['alignment']['nearest_target_rows_by_remainder'].values())==2021
assert len(d['on_grid_rows_detail'])==3 and all(x['eu_old_row'] is False for x in d['on_grid_rows_detail'])
assert d['context']['source_cadence_seconds']==600 and d['cohort']['old_interval_minutes']==5
assert d['target_history_review']['events_found']==0 and len(d['target_history_review']['target_timestamps_checked'])==4
assert 'does not establish' in d['target_history_review']['interpretation']
assert d['decision']['active_existing_operations_for_three_source_only_rows']==6
assert d['decision']['active_existing_operations_at_1373320800_boundary']==1
assert d['decision']['new_operations_from_this_review']==0
assert d['decision']['active_operation_breakdown']['package_total_operations']==7
assert d['decision']['approval_status']=='NOT_APPROVED' and d['decision']['application_status']=='NOT_APPLIED'
assert d['decision']['restored_proposals']==0 and d['decision']['estimated_proposals']==0
assert d['safety']['database_access']=='READ_ONLY SELECT' and d['safety']['writes']==0
print('PASS: 2013 cohort/alignment totals, 10-minute source cadence, source-only holds and safety flags reconcile.')
