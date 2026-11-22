#!/usr/bin/env python3
import json
from pathlib import Path
d=json.loads((Path(__file__).resolve().parents[1]/'data/2014_source_only_scope_reconciliation.json').read_text())
c=d['counts']; assert c['old_weewx_rows']==c['weewx_WH1080_rows']==c['shared_source_keys']==97228
assert c['shared_source_keys_absent_eu_old']==1071
assert c['of_absent_eu_old_keys_absent_reconstruction']==1070
assert c['of_absent_eu_old_keys_present_reconstruction']==1
assert c['reconstruction_source_only_cohort_total']==c['reconstruction_source_only_and_eu_old_present']+c['of_absent_eu_old_keys_absent_reconstruction']==11698
assert d['overlap_key']['dateTime']==1406150700 and d['overlap_key']['reconstruction_outTemp_C']==16.2
assert d['safety']['writes']==0 and d['safety']['staging'] is False and d['safety']['application'] is False
print('PASS: 2014 EU-old/reconstruction cohort scopes reconcile (1071 = 1070 + 1).')
