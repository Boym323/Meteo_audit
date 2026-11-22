#!/usr/bin/env python3
"""Validate the bounded 2019 RH case-review evidence without database access."""
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
d=json.loads((p/'data/rh_p2_2019_exact_bracket_candidate_review.json').read_text())
assert d['candidate_count']==6 and len(d['candidates'])==6
assert d['summary']['source_copies_equal']==6
assert d['summary']['target_rows_present_in_all_six_archives']==6
assert all(all(x['archive_row_presence'].values()) for x in d['candidates'])
assert d['summary']['target_RH_bracketed']==6
assert d['summary']['LuhaMet_exact_reference_rows']==5
assert d['summary']['proposals_created']==0
assert all(x['decision']=='REVIEW_REQUIRED' and not x['proposal_created'] for x in d['candidates'])
assert all(x['source_units_interval']=='17/5' and x['target_units_interval']=='16/5' for x in d['candidates'])
assert all(x['rh_events']==0 and x['all_events']==0 for x in d['candidates'])
assert all(x['luhamet_minus_source_rh_pp'] is None or 42 <= x['luhamet_minus_source_rh_pp'] <= 61 for x in d['candidates'])
for f in ['data/rh_p2_2019_exact_bracket_candidate_review.csv','sql/readonly/rh_p2_2019_bracketed_case_review.sql','reports/2026-11-13-rh-p2-2019-exact-bracket-review.md']:
 assert (p/f).is_file(),f
print('PASS: six exact 2019 RH candidates reconciled; 5/5 LuhaMet references show large disagreement; all held; no proposals.')
