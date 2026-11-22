#!/usr/bin/env python3
import json
from pathlib import Path
d=json.loads((Path(__file__).resolve().parents[1]/'data/source_only_target_row_availability_2016_2017.json').read_text()); y={x['utc_year']:x for x in d['by_year']}
assert y[2016]['cohort_rows']==5740 and y[2016]['old_weewx_rows']==y[2016]['weewx_WH1080_rows']==5740
assert all(y[2016][k]==0 for k in ['loucka_reconstruction_rows','pocasi_loucka_eu_rows','pocasi_loucka_eu_GW1000_rows','pocasi_loucka_eu_old_rows'])
assert y[2017]['cohort_rows']==24531 and y[2017]['old_weewx_rows']==y[2017]['weewx_WH1080_rows']==24531
assert all(y[2017][k]==0 for k in ['loucka_reconstruction_rows','pocasi_loucka_eu_rows','pocasi_loucka_eu_GW1000_rows','pocasi_loucka_eu_old_rows'])
assert 'not whether records were intentionally removed' in d['interpretation']
print('PASS: all 30,271 rows present in both legacy archives and absent from the four reconstruction/production archives; cause unresolved.')
