#!/usr/bin/env python3
"""Validate residual 2013/2016/2020 strict-copy cohort evidence offline."""
import json
from pathlib import Path
d=json.loads((Path(__file__).resolve().parents[1]/'data/source_only_remaining_strict_copy_cohorts.json').read_text())
r=d['records']
assert d['count']==len(r)==10 and d['neighbor_rows']==86
assert {x['utc_year'] for x in r}=={2013,2016,2020}
assert {y:sum(x['utc_year']==y for x in r) for y in (2013,2016,2020)}=={2013:3,2016:2,2020:5}
assert all(x['old_units']==x['wh_units']==17 and x['old_interval']==x['wh_interval']==5 for x in r)
assert all(x['old_temp']==x['wh_temp'] and x['old_rh']==x['wh_rh'] and x['old_rain']==x['wh_rain'] and x['old_rainRate']==x['wh_rainRate'] and x['old_wind']==x['wh_wind'] for x in r)
assert all(not x['has_pocasi_main'] and not x['has_gw1000'] and not x['has_pocasi_old'] and x['change_events']==0 for x in r)
assert sum(x['old_temp']==0 for x in r)==2 and sum(x['old_rh'] is None for x in r)==5
assert sum(x['neighbor_rows_10min'] for x in r)==43  # one copy; 86 rows across both exact copies
print('PASS: residual strict-copy rows, year counts, field equality, target/history absence and neighbor summary')
