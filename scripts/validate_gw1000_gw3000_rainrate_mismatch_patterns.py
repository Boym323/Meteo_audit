#!/usr/bin/env python3
"""Validate exact-pair rainRate mismatch direction against frozen aggregates."""
import json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/gw1000_gw3000_rainrate_mismatch_patterns_2009_2020.json').read_text())
core=json.load(open(R/'data/gw1000_gw3000_core_concordance_2009_2020.json'))
ratio=json.load(open(R/'data/gw1000_gw3000_rainrate_nonzero_ratio_profile_2009_2020.json'))
sql=(R/'sql/readonly/gw1000_gw3000_rainrate_mismatch_patterns_2009_2020.sql').read_text().upper()
assert d['database_access']=='READ_ONLY SELECT' and d['database_writes']==0
assert ratio['database_access']=='READ_ONLY SELECT' and ratio['result_rows']==[]
assert 'SELECT' in sql and not any(k in sql for k in ('INSERT','UPDATE','DELETE','REPLACE','ALTER','DROP','TRUNCATE'))
assert len(d['rows'])==32
assert sum(int(r['mismatch_rows']) for r in d['rows'])==30728
patterns=Counter(); years=Counter(); units=Counter()
for r in d['rows']:
 n=int(r['mismatch_rows']);patterns[r['rain_bucket']]+=n;years[int(r['year_utc'])]+=n
 units[(r['gw1000_usUnits'],r['gw3000_usUnits'],r['gw1000_interval'],r['gw3000_interval'])]+=n
 assert r['gw1000_usUnits']==r['gw3000_usUnits']==16
 assert r['gw1000_interval']==r['gw3000_interval'] and r['gw1000_interval'] in (5,6)
 assert r['gw1000_rate_min']>0 and r['gw3000_rate_min']==r['gw3000_rate_max']==0
assert patterns=={'RAIN_FIELD_POSITIVE':19206,'RAIN_FIELD_ZERO':11511,'RAIN_FIELD_NULL':11}
totals={x['variable']:x for x in core['totals']}
assert totals['rainRate']['both_nonnull']==1073011 and totals['rainRate']['different_values_when_both_nonnull']==30728
assert totals['rainRate']['equal_nonnull']==1042283
assert totals['rain']['different_values_when_both_nonnull']==0
assert sum(years.values())==30728
assert all(years[y]>0 for y in range(2009,2021))
assert sum(n for (u1,u2,i1,i2),n in units.items() if i1==6)==53
print('PASS: all 30,728 rainRate differences are GW1000 positive / GW3000 zero; 19,206 with positive rain, 11,511 zero rain, 11 rain NULL; same usUnits and interval; no nonzero-ratio conversion cohort; prior exact-pair totals reconcile.')
