#!/usr/bin/env python3
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
expected={2016:16330,2017:28015}
for y,n in expected.items():
 d=json.loads((R/f'data/{y}_source_only_field_eligibility.json').read_text());src=json.loads((R/f'data/{y}_target_absent_source_field_availability.json').read_text())
 assert d['source_only_timestamps']==n==src['source_only_rows'] and len(d['fields'])==50
 for x in d['fields']:
  c=src['field_counts'][x['field']];assert x['old_nonnull']==c['old_nonnull'] and x['wh1080_nonnull']==c['wh1080_nonnull'] and x['paired_equal']==c['both_equal'] and x['paired_conflict']==c['both_conflict']
  assert x['paired_nonnull']==x['paired_equal']+x['paired_conflict']
  assert x['old_only_nonnull']+x['paired_nonnull']==x['old_nonnull']
  assert x['wh1080_only_nonnull']+x['paired_nonnull']==x['wh1080_nonnull']
  assert x['both_null']+x['old_only_nonnull']+x['wh1080_only_nonnull']+x['paired_nonnull']==n
  assert x['eligible_for_restoration'] is False
 assert d['summary']['restored']==d['summary']['estimated']==0
r=list(csv.DictReader((R/'reports/2026-11-14-2016-2017-source-only-field-eligibility.csv').open()));assert len(r)==100
assert all(x['year_utc'] in ('2016','2017') for x in r)
print('PASS: 2016/2017 source-only cohorts (16,330 and 28,015 rows) partition across 50 fields each; no field approved for restoration.')
