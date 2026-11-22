#!/usr/bin/env python3
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for y,n in [(2019,814),(2020,1466)]:
 d=json.loads((R/f'data/{y}_source_only_field_eligibility.json').read_text());src=json.loads((R/f'data/{y}_source_only_field_month.json').read_text())
 assert d['source_only_timestamps']==n and len(d['fields'])==50
 assert sum(m['source_only_rows'] for m in src['monthly'])==n
 for x in d['fields']:
  field=x['field'];ms=[m for m in src['monthly'] if field in m['fields']]
  old=sum(int(m['fields'][field]['old_nonnull']) for m in ms);wh=sum(int(m['fields'][field]['wh_nonnull']) for m in ms);eq=sum(int(m['fields'][field]['both_equal']) for m in ms);conf=sum(int(m['fields'][field]['both_conflict']) for m in ms)
  assert (x['old_nonnull'],x['wh1080_nonnull'],x['paired_equal'],x['paired_conflict'])==(old,wh,eq,conf)
  assert x['both_null']+x['old_only_nonnull']+x['wh1080_only_nonnull']+x['paired_nonnull']==n
  assert x['eligible_for_restoration'] is False
 assert d['summary']['restored']==d['summary']['estimated']==0
r=list(csv.DictReader((R/'reports/2026-11-14-2019-2020-source-only-field-eligibility.csv').open()));assert len(r)==100
print('PASS: 2019/2020 source-only cohorts (814/1,466) partition across 50 fields each; no field approved for restoration.')
