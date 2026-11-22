#!/usr/bin/env python3
import json
from pathlib import Path
d=json.loads((Path(__file__).resolve().parents[1]/'data/rh_p2_2013_exact_bracket_review.json').read_text());r=d['rows']
assert len(r)==4 and d['source_pair_agreement_count']==4 and d['target_temperature_exact_count']==4
assert all(x['recon_rh'] is None and x['rh_history_events']==0 and not x['exact_luhamet'] for x in r)
assert r[0]['source_rh']==59.8 and r[0]['prev_rh']==61 and r[0]['next_rh']==60.2
assert r[1]['source_rh']==59.8 and r[1]['prev_rh']==60 and r[1]['next_rh']==60
assert r[2]['source_rh']==10 and r[2]['prev_rh']==65 and r[2]['next_rh']==68
assert r[3]['source_rh']==10 and r[3]['prev_rh']==87 and r[3]['next_rh']==87
assert d['disposition'].startswith('all four REVIEW_REQUIRED')
print('PASS: four 2013 RH cases reviewed; 2 require frost context, 2 conflict; no proposals.')
