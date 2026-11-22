#!/usr/bin/env python3
"""Validate aggregate source-only query reconciliation and protected scope."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
g=json.loads((R/'data/source_only_2009_2020_cross_archive_grouped.json').read_text())
s=json.loads((R/'data/source_only_2009_2020_cross_archive_summary.json').read_text())
n=json.loads((R/'data/source_only_nearest_5m_slot_collision_summary.json').read_text())
q=json.loads((R/'data/source_only_year_quarter_interval.json').read_text())
z=json.loads((R/'data/source_only_outtemp_zero_runs_by_source_year.json').read_text())
za=json.loads((R/'data/source_only_zero_availability_by_year.json').read_text())
pv=json.loads((R/'data/source_only_pocasi_old_value_concordance_by_year.json').read_text())
pu=json.loads((R/'data/source_only_pocasi_old_unit_concordance_by_year.json').read_text())
hc=json.loads((R/'data/source_only_reconstruction_history_candidate_audit.json').read_text())
assert len(g)==158 and sum(int(x['timestamp_count']) for x in g)==207182
assert s['unique_timestamps']==207182 and s['timestamp_count_reconciles']==207182
cc={k:sum(int(x['timestamp_count']) for x in s['copy_concordance'] if x['concordance']==k) for k in {x['concordance'] for x in s['copy_concordance']}}
assert cc=={'ALL_PRIMARY_EQUAL':146858,'TEMP_EQUAL_AUX_DIFF_OR_NULL':5403,'TEMP_CONFLICT':54883,'SINGLE_COPY':38},cc
assert sum(int(x['timestamp_count']) for x in s['year_interval_grid'] if int(x['on_5m_grid']))==44406
iv={int(k):sum(int(x['timestamp_count']) for x in s['year_interval_grid'] if int(x['interval_min'])==int(k)) for k in {x['interval_min'] for x in s['year_interval_grid']}}
assert iv=={5:204999,6:2180,30:3},iv
assert sum(int(x['timestamp_count']) for x in s['other_archive_presence'] if x['has_pocasi_old'])==145837
assert sum(int(x['source_timestamps_in_groups']) for x in n)==207182
assert sum(int(x['timestamps']) for x in q if int(x['utc_year'])==2018 and int(x['utc_quarter'])==1)==8048
assert max(int(x['utc_year']) for x in q)==2020
assert len(z)==20 and max(int(x['max_consecutive_zero_rows']) for x in z)==2157
assert sum(int(x['zero_outTemp']) for x in za)==62464
assert sum(int(x['n']) for x in pv)==145837
assert sum(int(x['p_old_temp_equal_nonnull']) for x in pv)==145473
assert sum(int(x['p_wh_temp_equal_nonnull']) for x in pv)==145482
assert all(int(x['pocasi_old_units'])==16 and int(x['old_units'])==17 and int(x['wh_units'])==17 for x in pu)
assert hc['source_only_unique_timestamps']==207182 and hc['reconstruction_changes_events']==0
assert len(hc['matching_candidate_details'])==1
assert hc['matching_candidate_details'][0]['target_time']==1313640000 and hc['matching_candidate_details'][0]['batch_id']=='loucka-frozen-outdoor-sensors-201108-v1' and hc['matching_candidate_details'][0]['batch_state']=='pending'
print('PASS: 207,182 reconcile; 158 groups; copy/interval/grid/other archive summaries; Q1 2018 count; no 2021 rows; zero series, secondary archive value/unit concordance and pre-existing candidate history')
