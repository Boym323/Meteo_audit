#!/usr/bin/env python3
"""Validate the saved bounded READ-ONLY current-state evidence, without DB access."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/active_proposal_current_state_readonly_20261113.json').read_text())
assert d['query_mode']=='Weather MCP READ_ONLY SELECT'
assert (d['active_packages'],d['active_timestamps'],d['active_field_operations'])==(5,56,65)
assert (d['target_rows_present'],d['target_rows_absent'])==(2,54)
assert d['proposed_timestamp_variable_pairs_with_history_events']==0
assert d['context_history_groups']==1 and d['context_history'][0]['variable']=='outTemp'
assert d['context_history'][0]['timestamp']==1546297200 and d['context_history'][0]['not_in_active_proposal'] is True
assert d['context_history'][0]['current_value_c']==-1.26666666666667
assert d['database_writes']==0 and d['staging'] is False and d['dry_run'] is False
assert d['protected_2021_queried'] is False and d['q1_2018_queried'] is False
assert len(d['existing_target_rows'])==2
print('PASS: 65 active keys, 54 absent rows, 2 expected existing rows; history context and READ-ONLY limits consistent.')
