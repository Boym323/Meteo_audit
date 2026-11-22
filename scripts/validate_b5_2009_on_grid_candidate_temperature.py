#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/'data/b5_2009_on_grid_candidate_temperature_review.json').read_text())
assert d['total_source_rows']==100 and len(d['episodes'])==2
ap,au=d['episodes']
assert ap['source_row_count']==14 and ap['outTemp']['distinct_values']==1 and ap['outTemp']['min']==ap['outTemp']['max']==4.8
assert ap['reconstruction_bounds']['before']['outTemp']==14.279999999999998 and ap['reconstruction_bounds']['after']['outTemp']==22.0
assert au['source_row_count']==86 and au['outTemp']['distinct_values']==1 and au['outTemp']['min']==au['outTemp']['max']==22.2
assert au['reconstruction_bounds']['before']['outTemp']==20.92 and abs(au['reconstruction_bounds']['after']['outTemp']-22.08)<1e-10
assert all(e['disposition']=='SOURCE_SENSOR_STUCK_SUSPECTED_REVIEW_REQUIRED' and not e['restored_proposal_created'] for e in d['episodes'])
assert d['all_target_keys_absent_from_reconstruction'] and d['all_source_keys_exactly_present_in_old_wh_euold']
assert d['safety']['writes']==0 and d['safety']['staging'] is False and d['safety']['application'] is False
assert d['safety']['q1_2018_queried'] is False and d['safety']['year_2021_queried'] is False
print('PASS: both 2009 flat-temperature source episodes are held; no proposal and all safety conditions pass.')
