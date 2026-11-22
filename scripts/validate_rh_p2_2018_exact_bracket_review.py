#!/usr/bin/env python3
"""Validate bounded unprotected-2018 RH case review and duplicate exclusion."""
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
d=json.loads((p/'data/rh_p2_2018_exact_bracket_candidate_review.json').read_text())
assert d['selected_target_count']==8 and len(d['candidates'])==8
assert d['q1_2018_included'] is False and d['new_review_rows']==7
assert sum(x['disposition']=='EXISTING_ACTIVE_RESTORED_OPERATION' for x in d['candidates'])==1
assert all(x['source_copies_equal'] and x['target_temp_matches_source_copies'] for x in d['candidates'])
assert all(x['target_rh'] is None and x['rh_events']==0 for x in d['candidates'])
assert all(x['disposition']=='REVIEW_REQUIRED' for x in d['candidates'] if x['dateTime']!=1546297200)
assert all(x['archive_row_presence'].values() for x in d['candidates'] if x['dateTime']!=1546297200)
last=next(x for x in d['candidates'] if x['dateTime']==1546297200)
assert not last['archive_row_presence']['pocasi-loucka.eu'] and not last['archive_row_presence']['pocasi-loucka.eu_GW1000'] and last['all_events']==1
assert d['summary']['new_proposals_created']==0
for f in ['data/rh_p2_2018_exact_bracket_candidate_review.csv','sql/readonly/rh_p2_2018_bracketed_case_review.sql','reports/2026-11-13-rh-p2-2018-exact-bracket-review.md']:
 assert (p/f).is_file(),f
print('PASS: 7 new 2018 cases held; Q1 excluded; 2018-12-31 active operation identified and not duplicated; no proposals.')
