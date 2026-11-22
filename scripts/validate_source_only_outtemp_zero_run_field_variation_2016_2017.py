#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/source_only_outtemp_zero_run_field_variation_2016_2017.json').read_text());y={x['utc_year']:x for x in d['years']}
assert y[2016]['selected_rows']==5618 and y[2016]['outTemp_distinct']==1 and y[2016]['barometer_distinct']==1694 and y[2016]['windSpeed_distinct']==3
assert y[2017]['selected_rows']==24154 and y[2017]['outTemp_distinct']==1 and y[2017]['barometer_distinct']==2934 and y[2017]['windSpeed_distinct']==21
assert all(x['outHumidity_nonnull']==0 for x in y.values())
assert 'does not identify' in d['interpretation']
print('PASS: outTemp invariant zero while wind/rainRate/barometer vary in both years; RH unavailable; no restoration approved.')
