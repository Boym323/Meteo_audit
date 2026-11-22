#!/usr/bin/env python3
"""Validate O4's complete 77-numeric-field x 18-year conservative availability matrix."""
import csv,json
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=json.loads((R/'reports/2026-11-13-annual-archive-field-availability-2009-2026.json').read_text())
summary=json.loads((R/'reports/2026-11-13-readiness-77-fields-expanded.json').read_text())
with (R/'reports/2026-11-13-readiness-77-fields-expanded.csv').open(newline='',encoding='utf-8') as f: csv_rows=list(csv.DictReader(f))
reg=json.loads((R/'config/active_proposal_registry.json').read_text())
rows=summary['records']; assert len(rows)==len(csv_rows)==1386
assert summary['variable_count']==source['fields_count']==77 and summary['matrix_cells']==1386
assert summary['years']==list(range(2009,2027))
assert len({(r['utc_year'],r['variable']) for r in rows})==1386
assert len({(int(r['utc_year']),r['variable']) for r in csv_rows})==1386
source_rows={(int(x['year']),x['variable']):x for x in source['records']}
proposal_counts=defaultdict(int)
for pkg in reg['packages']:
    if pkg['status']!='ACTIVE':continue
    for op in pkg.get('operation_keys',[]):
        import datetime
        year=datetime.datetime.fromtimestamp(int(op['timestamp']),datetime.timezone.utc).year
        proposal_counts[(year,op['variable'])]+=1
states=Counter()
for r in rows:
    y=int(r['utc_year']); key=(y,r['variable']); orig=source_rows[key]
    assert int(r['archive_rows'])==int(orig['archive_rows'])
    assert int(r['nonnull_rows'])==int(orig['nonnull_rows'])
    assert int(r['null_rows'])==int(orig['null_rows'])
    assert int(r['active_unapproved_proposal_operations'])==proposal_counts[key]
    expected='NOT_AVAILABLE' if int(orig['nonnull_rows'])==0 else 'REVIEW_REQUIRED'
    assert r['readiness']==expected
    states[r['readiness']]+=1
    assert r['atlas_suitability']==expected and r['records_impact']==expected
    if y==2018: assert r['protection_status']=='CONTAINS_Q1_2018_INTERIM'
    if y==2021: assert r['protection_status']=='DIAGNOSTIC_ONLY'
assert states==Counter({'REVIEW_REQUIRED':673,'NOT_AVAILABLE':713})
assert summary['active_proposal_operations_in_matrix']==reg['active_operation_count']
assert all(r['readiness']!='READY' for r in rows)
assert 'availability-based screen' in summary['limitations'][0]
assert 'No cell is READY' in summary['limitations'][1]
# Ensure CSV mirrors the machine-readable JSON on the scope-driving fields.
by_json={(int(r['utc_year']),r['variable']):r for r in rows}
for r in csv_rows:
    j=by_json[(int(r['utc_year']),r['variable'])]
    for k in ('readiness','archive_rows','nonnull_rows','null_rows','active_unapproved_proposal_operations','protection_status'):
        assert str(r[k])==str(j[k]),(r['utc_year'],r['variable'],k)
print(json.dumps({'status':'PASS','cells':len(rows),'fields':77,'years':18,'states':dict(states),'active_operations':reg['active_operation_count'],'ready_cells':0,'database_access':'NONE'}))
