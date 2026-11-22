#!/usr/bin/env python3
"""Validate full 103-chunk cross-copy concordance rollup for gap source rows."""
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'data/gap_source_copy_concordance/summary.json'
d=json.loads(p.read_text());r=d['records'];years=d['by_year_gap_band']
assert d['status']=='PASS' and d['chunks']==103 and d['target_candidates']==44406
assert r['old_weewx_rows']==44393 and r['old_weewx_missing']==13
assert r['wh_units17']==44406 and r['wh_interval5']==44390
assert r['units_equal']==44393 and r['intervals_equal']==44393
assert r['wh_outTemp_zero']==42298 and r['wh_outHumidity_null']==42341
assert r['outTemp_both_present']==5367 and r['outTemp_conflict']==0
assert r['outHumidity_both_present']==1709 and r['outHumidity_conflict']==169
assert r['rain_both_present']==44387 and r['rain_conflict']==0
assert r['rainRate_both_present']==44392 and r['rainRate_conflict']==0
assert r['windSpeed_both_present']==5901 and r['windSpeed_conflict']==0
assert sum(x['wh1080_rows'] for x in years if x['protection_scope']=='PROTECTED_Q1_2018_DIAGNOSTIC')==7386
assert all(x['utc_year']!=2021 for x in years)
assert d['disposition']=={'RESTORED':0,'ESTIMATED':0,'REVIEW_REQUIRED':44406,'MISSING':0}
print('PASS: 103 chunks, 44,406 source rows, variable concordance, protected Q1 2018 separation, 2021 exclusion')
