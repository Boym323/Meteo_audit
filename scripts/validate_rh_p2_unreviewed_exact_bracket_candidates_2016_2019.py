#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/rh_p2_unreviewed_exact_bracket_candidates_2016_2019.json').read_text());rows=d['rows'];assert d['candidate_count']==len(rows)==59
assert len(d['reviewed_timestamp_exclusions'])==40
assert all(x['target_rh'] is None and x['disposition']=='REVIEW_REQUIRED' for x in rows)
assert all(x['source_rh']==x['wh_rh'] and x['euold_rh'] is None for x in rows)
assert {int(x['year']):x['count'] for x in d['yearly_aggregate']}=={2016:2,2017:18,2018:24,2019:15}
a={int(x['year']):x for x in d['yearly_aggregate']}
assert a[2016]['target_temp_exact']==2 and a[2016]['regional_delta_gt20']==2
assert a[2017]['target_temp_exact']==0 and a[2017]['source_temp_zero_or_missing']==12 and a[2017]['regional_delta_gt20']==18
assert a[2018]['within_bracket']==0 and a[2018]['target_temp_exact']==24 and a[2018]['regional_delta_gt20']==8
assert a[2019]['within_bracket']==0 and a[2019]['target_temp_exact']==15 and a[2019]['regional_delta_gt20']==15
assert d['decision'].startswith('Every remaining candidate is REVIEW_REQUIRED')
print('PASS: 59 residual bracketed RH candidates reviewed (2/18/24/15); all held REVIEW_REQUIRED; no proposal.')
