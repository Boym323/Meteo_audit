#!/usr/bin/env python3
"""Validate the saved bounded 2016–2017 source-only aggregate snapshot."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/source_only_outtemp_2016_2017_exact_grid_screen.json').read_text())
assert d['scope']['requirements']==['exact timestamp present in both sources','epoch timestamp divisible by 300 seconds','usUnits=17 in both','interval=5 in both']
y={x['utc_year']:x for x in d['years']}
assert set(y)=={2016,2017}
assert y[2016]['source_rows']==5740 and y[2016]['old_outTemp_nonnull']==2 and y[2016]['wh1080_outTemp_nonnull']==5740
assert y[2016]['both_outTemp_nonnull']==y[2016]['equal_outTemp']==y[2016]['old_outTemp_zero']==2
assert y[2017]['source_rows']==24531 and y[2017]['old_outTemp_nonnull']==10 and y[2017]['wh1080_outTemp_nonnull']==24531
assert y[2017]['both_outTemp_nonnull']==y[2017]['equal_outTemp']==y[2017]['old_outTemp_zero']==10
assert y[2016]['wh1080_outTemp_zero']==5740 and y[2017]['wh1080_outTemp_zero']==24531
assert sum(x['source_rows'] for x in y.values())==30271
assert d['interpretation']['eligible_restored_outTemp']==0
print('PASS: saved 2016–2017 strict source-only aggregate; 30,271 rows, 12 old temperatures all zero, WH1080 zero throughout; no restoration emitted.')
