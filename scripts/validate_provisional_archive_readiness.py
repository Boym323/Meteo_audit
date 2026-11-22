#!/usr/bin/env python3
"""Validate coverage and conservative classifications in provisional readiness matrix."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'reports'
rows=list(csv.DictReader((R/'2026-11-13-provisional-archive-readiness.csv').open(newline='',encoding='utf-8')))
d=json.loads((R/'2026-11-13-provisional-archive-readiness.json').read_text())
assert len(rows)==198 and len(d['records'])==198
assert len({(int(x['utc_year']),x['variable']) for x in rows})==198
assert {int(x['utc_year']) for x in rows}==set(range(2009,2027))
assert len({x['variable'] for x in rows})==11
assert all(x['readiness'] in {'REVIEW_REQUIRED','NOT_AVAILABLE'} for x in rows)
assert all(x['validated_recommended_corrections']=='0' for x in rows)
assert all(x['conditional_candidate_count']=='' and x['unresolvable_gap_count']=='' for x in rows)
assert all(x['readiness']=='REVIEW_REQUIRED' for x in rows if int(x['utc_year'])==2021)
assert all('interim/live' in x['reason'] for x in rows if int(x['utc_year'])==2018)
assert all(x['readiness']=='REVIEW_REQUIRED' for x in rows if int(x['utc_year'])==2026)
assert sum(int(x['archive_rows']) for x in rows if x['variable']=='outTemp')==1_689_890
assert {int(x['internal_zero_row_months']) for x in rows if int(x['utc_year'])==2011}=={4}
assert {int(x['internal_zero_row_months']) for x in rows if int(x['utc_year'])==2012}=={2}
assert d['scope_limitations']
print('PASS: 198 cells, 18 years x 11 variables, protected/interim/partial flags and denominator cautions')
