#!/usr/bin/env python3
import json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
d=json.loads((r/'data/source_only_2019_36_rh_null_cohort.json').read_text())
assert d['count']==36 and d['review_required']==36 and len(d['rows'])==36
assert [x['count'] for x in d['blocks']]==[1,23,12]
assert all(x['outHumidity'] is None for x in d['rows'])
assert all(x['rain']==0 and x['rainRate']==0 for x in d['rows'])
assert all(x['outTemp'] is not None and x['windSpeed'] is not None for x in d['rows'])
assert len({x['dateTime'] for x in d['rows']})==36
print('PASS: 36 unique source-only rows; RH NULL; 1/23/12 blocks; matching-field screen retained')
