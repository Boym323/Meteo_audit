#!/usr/bin/env python3
"""Validate completeness and safety labels of the annual availability baseline."""
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=json.loads((ROOT/'reports/2026-11-13-annual-archive-field-availability-2009-2026.json').read_text())
out=json.loads((ROOT/'data/archive_readiness_availability_baseline_2009_2026.json').read_text())
assert out['fields_count']==77 and out['year_count']==18 and out['cell_count']==1386
assert len(out['records'])==1386
keys={(x['year'],x['variable']) for x in out['records']}
assert len(keys)==1386
source={(x['year'],x['variable']):x for x in src['records']}
assert keys==set(source)
for x in out['records']:
    s=source[(x['year'],x['variable'])]
    assert (x['archive_rows'],x['null_rows'],x['nonnull_rows'])==(s['archive_rows'],s['null_rows'],s['nonnull_rows'])
    expect='NOT_AVAILABLE' if s['nonnull_rows']==0 else 'REVIEW_REQUIRED'
    assert x['readiness']==expect
    assert x['readiness']!='READY'
    if x['year']==2021: assert x['protection_status']=='PROTECTED_DIAGNOSTIC_ONLY'
    if x['year']==2018: assert x['protection_status']=='INTERIM_LIVE_NO_NEW_PROPOSALS'
assert all(x['partial_2026'] for x in out['by_year'] if x['year']==2026)
assert sum(1 for x in out['records'] if x['readiness']=='NOT_AVAILABLE')==713
assert sum(1 for x in out['records'] if x['readiness']=='REVIEW_REQUIRED')==673
print('PASS: all 1,386 field/year cells reconcile; no availability-only READY claims; 2018/2021 guards and partial 2026 validated')
