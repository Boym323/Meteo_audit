#!/usr/bin/env python3
"""Validate the bounded 2017 warm/frost RH case screen."""
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
d=json.loads((p/'data/rh_p2_2017_exact_bracket_review.json').read_text())
assert d['candidate_count']==8 and len(d['candidates'])==8
assert d['summary']['all_six_archive_rows_present']==8
assert d['summary']['warm_season_cases']==4 and d['summary']['subzero_frost_review_cases']==4
assert d['summary']['history_events']==0 and d['summary']['proposals_created']==0
assert all(x['source_copies_equal'] and x['source_temp_matches_target'] for x in d['candidates'])
assert all(x['decision']=='REVIEW_REQUIRED' and not x['proposal_created'] for x in d['candidates'])
assert all(x['rh_events']==0 and x['all_events']==0 for x in d['candidates'])
assert all(x['target_rows_present_all_six_archives'] for x in d['candidates'])
assert sum(x['expert_issue']=='ER-38' for x in d['candidates'])==4
assert sum(x['expert_issue']=='ER-39' for x in d['candidates'])==4
for f in ['data/rh_p2_2017_exact_bracket_review.csv','sql/readonly/rh_p2_2017_bracketed_case_review.sql','reports/2026-11-13-rh-p2-2017-exact-bracket-review.md']:
 assert (p/f).is_file(),f
print('PASS: eight 2017 exact-bracket cases, 4 warm-season ER-39 and 4 frost ER-38; no corrections.')
