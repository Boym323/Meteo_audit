#!/usr/bin/env python3
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/2014_source_only_field_eligibility.json').read_text());src=json.loads((R/'data/2014_target_absent_source_field_availability.json').read_text())
assert d['source_only_rows']==src['source_only_rows']==1071 and len(d['fields'])==50
for x in d['fields']:
 c=src['field_counts'][x['field']]
 assert x['old_nonnull']==c['old_nonnull'] and x['wh1080_nonnull']==c['wh1080_nonnull']
 assert x['paired_equal']==c['both_equal'] and x['paired_conflict']==c['both_conflict']
 assert x['paired_nonnull']==x['paired_equal']+x['paired_conflict']
 assert x['old_only_nonnull']+x['paired_nonnull']==x['old_nonnull']
 assert x['wh1080_only_nonnull']+x['paired_nonnull']==x['wh1080_nonnull']
 assert x['both_null']+x['old_only_nonnull']+x['wh1080_only_nonnull']+x['paired_nonnull']==1071
 assert x['eligible_for_restoration'] is False
assert d['summary']['restored_proposals']==d['summary']['estimated_proposals']==0
assert len(list(csv.DictReader((R/'reports/2026-11-14-2014-source-only-field-eligibility.csv').open())))==50
assert d['safety']['writes']==0 and d['safety']['application'] is False
print('PASS: 1,071 rows x 50 fields partition exactly; no source-only field is approved for restoration.')
