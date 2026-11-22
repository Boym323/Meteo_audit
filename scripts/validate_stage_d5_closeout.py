#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=json.loads((root/'PROGRESS.json').read_text())
d=next(s for s in p['stages'] if s['id']=='D')
t=next(t for t in d['subtasks'] if t['id']=='D5')
assert t['status']=='COMPLETED_WITH_LIMITATIONS' and t['verified'] is True
assert t['remaining_review_cases']==1234
assert t['additional_review_checkpoint_2014_rare_value_candidates']['new_row_level_review_targets']==12
assert t['additional_review_checkpoint_2016_2019_residual']['new_unique_targets']==59
assert d['status']=='COMPLETED_WITH_LIMITATIONS' and d['verified_subtasks']==7 and d['subtask_completion_percent']==100.0
assert p['overall']['verified_subtasks']==137 and p['overall']['defined_subtasks']==142
assert p['overall']['subtask_completion_percent']==96.5
assert p['overall']['status']=='IN_PROGRESS'
reg=json.loads((root/'config/active_proposal_registry.json').read_text())
assert reg['active_operation_count']==65 and reg['active_restored_operations']==44 and reg['active_estimated_operations']==21
assert len([x for x in reg['packages'] if x['status']=='ACTIVE'])==7
report=(root/'reports/2026-11-14-stage-d5-p2-eligibility-closeout.md').read_text()
assert '1,234' in report and 'REVIEW_REQUIRED' in report and 'COMPLETED_WITH_LIMITATIONS' in report
assert 'No additional source configuration' in report
print('PASS: D5 closed with explicit limits; 1,234 cases held; active register unchanged; overall goal remains in progress.')
