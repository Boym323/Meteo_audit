#!/usr/bin/env python3
import json,csv
from pathlib import Path
R=Path(__file__).resolve().parents[1];d=json.loads((R/'data/2018_q2_q4_source_only_field_eligibility.json').read_text());rows=list(csv.DictReader((R/'reports/2026-11-14-2018-q2-q4-source-only-field-eligibility.csv').open()))
assert d['source_only_timestamps']==422 and len(d['fields'])==50 and len(rows)==50
assert d['quarter_interval_row_counts']=={'2018-Q2_interval5':212,'2018-Q3_interval5':16,'2018-Q3_interval6':1,'2018-Q4_interval5':193}
assert d['safety']['q1_2018_queried'] is False and d['safety']['year_2021_queried'] is False
for x in d['fields']:
 assert not x['eligible_for_restoration']
 assert x['old_nonnull']==x['paired_equal']+x['paired_conflict']+x['old_only_nonnull']
 assert x['wh_nonnull']==x['paired_equal']+x['paired_conflict']+x['wh_only_nonnull']
 assert x['source_only_timestamps']==x['old_only_nonnull']+x['wh_only_nonnull']+x['paired_equal']+x['paired_conflict']+x['both_null']
print('PASS: 2018 Q2-Q4 only; 422 rows and 50 fields reconcile; Q1 excluded; no restoration eligibility.')
