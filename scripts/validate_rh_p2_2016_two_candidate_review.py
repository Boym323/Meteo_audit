#!/usr/bin/env python3
"""Deterministic integrity/decision checks for the bounded 2016 RH review."""
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
d=json.loads((p/'data/rh_p2_2016_two_candidate_review.json').read_text())
assert d['analysed_target_timestamps']==2 and len(d['decisions'])==2
assert {x['dateTime'] for x in d['decisions']}=={1458239400,1474061400}
a,b=d['decisions']
assert a['source_rh']==23 and a['target_rh'] is None and a['reference_rh_difference_pp']==53
assert a['neighbor_rh']==[23,24] and a['decision']=='REVIEW_REQUIRED'
assert b['source_temperature']==-7.16 and b['target_temperature']==17 and b['decision']=='REVIEW_REQUIRED'
assert all(x['all_events']==0 and x['rh_events']==0 for x in d['context_rows'] if x['dateTime'] in {1458239400,1474061400})
assert d['limits'] and 'No correction operation created.' in d['limits']
for f in ['sql/readonly/rh_p2_2016_bracketed_case_review.sql','sql/readonly/rh_p2_2016_luhamet_context.sql','data/rh_p2_2016_two_candidate_review.csv','reports/2026-11-13-rh-p2-2016-two-candidate-review.md']:
 assert (p/f).is_file(),f
print('PASS: 2 exact-time RH candidates, six-archive evidence, neighbor context, reference disagreement/anomalous source-row holds; no proposals.')
