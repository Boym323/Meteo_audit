#!/usr/bin/env python3
import json,csv
from pathlib import Path
R=Path(__file__).resolve().parents[1]
raw=json.loads((R/'data/source_only_2010_2011_field_aggregates.json').read_text());assert len(raw)==100
rows=list(csv.DictReader((R/'reports/2026-11-14-2010-2011-source-only-field-eligibility.csv').open()));assert len(rows)==100
for y,n in ((2010,1989),(2011,5016)):
 d=json.loads((R/f'data/{y}_source_only_field_eligibility.json').read_text());assert len(d['fields'])==50 and d['source_only_timestamps']==n
 for f in d['fields']:
  assert f['eligible_for_restoration'] is False
  assert f['old_nonnull']==f['paired_equal']+f['paired_conflict']+f['old_only_nonnull']
  assert f['wh_nonnull']==f['paired_equal']+f['paired_conflict']+f['wh_only_nonnull']
  assert f['source_only_timestamps']==f['old_only_nonnull']+f['wh_only_nonnull']+f['paired_equal']+f['paired_conflict']+f['both_null']
assert next(f for f in json.loads(Path('data/2010_source_only_field_eligibility.json').read_text())['fields'] if f['field']=='outTemp')['paired_equal']==1989
assert next(f for f in json.loads(Path('data/2011_source_only_field_eligibility.json').read_text())['fields'] if f['field']=='outTemp')['paired_equal']==5014
print('PASS: 2010/2011 exact source-only cohorts (1,989/5,016) partition across 50 fields each; no restoration eligibility inferred.')
