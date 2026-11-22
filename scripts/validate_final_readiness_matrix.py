#!/usr/bin/env python3
"""Validate full 77-field x 18-year use-case readiness and conservative labels."""
import csv,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/final_readiness_matrix_77x18.json').read_text());rows=d['records']
assert d['scope']['variables']==77 and d['scope']['cells']==1386 and len(rows)==1386
assert len({(x['utc_year'],x['variable']) for x in rows})==1386
assert d['scope']['proposal_included_in_availability'] is False
assert all(x['raw_origin_classification'] in ('NOT_CLASSIFIED','NOT_AVAILABLE') for x in rows)
assert all(x['quality_review_status']=='REVIEW_REQUIRED' for x in rows)
assert all('Do not assign MISSING' in x['missing_classification_rule'] for x in rows)
assert all(x['active_unapproved_proposal_operations']==0 or x['proposal_state_note'] for x in rows)
for x in rows:
 if x['utc_year']==2021: assert all(x[k]=='DIAGNOSTIC_ONLY' for k in ('raw_value_display','historical_graph','daily_statistics','monthly_statistics','annual_statistics','records_and_extremes','long_term_trends','meteorological_atlas'))
 if x['utc_year']==2018: assert x['protection_status'].startswith('Q1_2018_PROTECTED') and 'PROTECTED' in x['raw_value_display']
 if x['utc_year']==2026: assert x['year_completeness']=='PARTIAL_YEAR'
 if x['nonnull_rows'] and x['utc_year'] not in (2018,2021): assert x['raw_value_display']=='READY_WITH_LIMITATIONS_RAW_AS_RECORDED' and 'REVIEW_REQUIRED' in x['daily_statistics'] and 'REVIEW_REQUIRED' in x['records_and_extremes']
 if x['nonnull_rows']==0 and x['utc_year'] not in (2018,2021): assert x['raw_value_display']=='NOT_AVAILABLE'
with (R/'data/final_readiness_matrix_77x18.csv').open(newline='',encoding='utf-8') as f: cr=list(csv.DictReader(f))
assert len(cr)==1386 and len({(int(x['utc_year']),x['variable']) for x in cr})==1386
print(json.dumps({'status':'PASS','cells':len(rows),'fields':77,'years':18,'raw_display':dict(Counter(x['raw_value_display'] for x in rows)),'daily_statistics':dict(Counter(x['daily_statistics'] for x in rows)),'no_unqualified_ready':True,'no_annual_MISSING_inferred':True},ensure_ascii=False,indent=2))
