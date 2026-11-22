#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/'data/long_gap_2012_gap3_nonzero_source_detail.json').read_text())
s=d['summary'];groups=d['nonzero_value_groups']
assert d['gap_id']==3 and d['schema']=='long-gap-source-detail-v1'
assert s['paired_interior_rows']==3551 and s['nonzero_temperature_rows']==287 and s['zero_temperature_rows']==3264
assert s['epoch_grid_rows']==3546 and s['offgrid_rows']==5
assert s['exact_temperature_matches']==3551 and s['RH_conflicts']==0
assert s['rain_equal_or_both_null']==3551 and s['rainRate_equal_or_both_null']==3551
assert s['usUnits']==17 and s['interval_min_max']==[5,5]
assert groups[0]['row_count']==285 and groups[0]['outTemp']==13.6 and groups[0]['outHumidity']==99.0
assert groups[0]['first_ts']==1313446200 and groups[0]['last_ts']==1313531400
assert sum(x['row_count'] for x in groups)==287
assert d['restored']==0 and d['estimated']==0 and d['review_required']==3551 and d['writes']==0
lg=list(__import__('csv').DictReader((root/'reports/2026-11-13-long-gap-44-source-state-disposition.csv').open()))
g=next(x for x in lg if x['gap_id']=='3')
assert g['start_utc']=='2011-08-15T20:05:00Z' and g['end_utc']=='2012-03-01T09:25:00Z'
print('PASS: gap 3 has 3,551 paired rows, 287 nonzero (285 stationary), 5 off-grid; no proposal.')
