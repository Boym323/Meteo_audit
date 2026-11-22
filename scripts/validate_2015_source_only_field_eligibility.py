#!/usr/bin/env python3
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/2015_source_only_field_eligibility.json').read_text())
assert d['source_only_timestamp_count']==2147 and len(d['fields'])==10
assert d['decision'].startswith('No new') and d['safety']['database_access']=='NONE'
for f in d['fields']:
 assert f['eligibility'].startswith('REVIEW_REQUIRED') or f['eligibility']=='MISSING_IN_BOTH_SOURCE_COPIES'
assert next(f for f in d['fields'] if f['field']=='pressure')['paired_equal']==2147
assert next(f for f in d['fields'] if f['field']=='rainRate')['paired_equal']==2147
assert next(f for f in d['fields'] if f['field']=='altimeter')['paired_conflict']==2147
csvrows=list(csv.DictReader((R/'reports/2026-11-14-2015-source-only-field-eligibility.csv').open()))
assert len(csvrows)==10
print('PASS: 2,147 source-only rows; 10 fields; no restoration eligibility without provenance/removal proof.')
