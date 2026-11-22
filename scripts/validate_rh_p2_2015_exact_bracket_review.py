#!/usr/bin/env python3
import json
from pathlib import Path
d=json.loads((Path(__file__).resolve().parents[1]/'data/rh_p2_2015_exact_bracket_review.json').read_text());r=d['rows']
assert len(r)==12 and all(x['disposition']=='REVIEW_REQUIRED' and x['target_rh'] is None and x['rh_change_events']==0 for x in r)
assert all(x['old_weewx_rh']==x['weewx_WH1080_rh'] and x['old_weewx_temp_c']==x['weewx_WH1080_temp_c']==x['target_temp_c'] for x in r)
assert all(not x['source_within_neighbor_range'] for x in r)
assert sum(x['abs_midpoint_delta_pp']<=1 for x in r)==2
assert sum(x['luhamet_rh'] is not None for x in r)==6
assert d['summary']['restored_proposals']==0
print('PASS: all 12 2015 exact-bracket RH cases remain REVIEW_REQUIRED; no proposal emitted.')
