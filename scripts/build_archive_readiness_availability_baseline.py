#!/usr/bin/env python3
"""Derive bounded readiness states from the frozen annual archive availability snapshot."""
from __future__ import annotations
import csv,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'reports/2026-11-13-annual-archive-field-availability-2009-2026.json'
data=json.loads(source.read_text())
assert data['database']=='loucka_reconstruction'
rows=[]
for item in data['records']:
    n=int(item['archive_rows']); nulls=int(item['null_rows']); values=int(item['nonnull_rows'])
    assert n==nulls+values
    # This is a scoped data-availability state, not a quality certification.
    status='NOT_AVAILABLE' if n==0 or values==0 else 'REVIEW_REQUIRED'
    year=int(item['year'])
    protection='PROTECTED_DIAGNOSTIC_ONLY' if year==2021 else ('INTERIM_LIVE_NO_NEW_PROPOSALS' if year==2018 else 'NONE')
    rows.append({'year':year,'variable':item['variable'],'archive':'loucka_reconstruction.archive','archive_rows':n,'nonnull_rows':values,'null_rows':nulls,'null_share':item['null_share'],'availability_state':'ALL_NULL' if values==0 else ('NO_ROWS' if n==0 else ('NO_NULLS_IN_ROWS' if nulls==0 else 'PARTIAL_NULL')),'readiness':status,'protection_status':protection,'scope_note':'Availability snapshot only; no temporal denominator, provenance certification, physical QC, source-only coverage or readiness sign-off is implied.'})
assert len(rows)==len(data['years'])*data['fields_count']==1386
assert all(sum(r['year']==y for r in rows)==data['fields_count'] for y in data['years'])
summary=Counter(r['readiness'] for r in rows)
allnull=[r for r in rows if r['availability_state']=='ALL_NULL']
byyear=[]
for year in data['years']:
    yr=[r for r in rows if r['year']==year]
    byyear.append({'year':year,'archive_rows':data['year_row_counts'][str(year)],'field_cells':len(yr),'review_required_cells':sum(r['readiness']=='REVIEW_REQUIRED' for r in yr),'not_available_cells':sum(r['readiness']=='NOT_AVAILABLE' for r in yr),'all_null_fields':[r['variable'] for r in yr if r['availability_state']=='ALL_NULL'],'partial_2026':year==2026,'protection_status':'PROTECTED_DIAGNOSTIC_ONLY' if year==2021 else ('INTERIM_LIVE_NO_NEW_PROPOSALS' if year==2018 else 'NONE')})
out={'schema':'archive-readiness-availability-baseline-v1','source_snapshot':str(source.relative_to(ROOT)),'database':data['database'],'period':data['period'],'fields_count':data['fields_count'],'year_count':len(data['years']),'cell_count':len(rows),'readiness_method':'REVIEW_REQUIRED if reconstruction rows contain any non-NULL values; NOT_AVAILABLE only if that reconstruction archive field/year has no values. This is scoped availability, not quality readiness.','cell_counts':dict(summary),'all_null_cells':len(allnull),'records':rows,'by_year':byyear,'limitations':['No expected-slot denominator or operational epoch adjustment','No row-level quality, source-lineage or sensor-identity certification','NOT_AVAILABLE refers only to this reconstruction archive snapshot; source archives may contain values','2021 is diagnostic-only; Q1 2018 is interim-live and receives no new proposal','2026 is partial through snapshot latest archive row'],'database_writes':0}
(ROOT/'data/archive_readiness_availability_baseline_2009_2026.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (ROOT/'reports/2026-11-13-archive-readiness-availability-baseline.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
md=['# Archive readiness availability baseline — 2009–2026','','This baseline converts the frozen annual `loucka_reconstruction.archive` availability snapshot into per-year/per-field availability states. It is a measurable input to readiness, not a quality or publication sign-off.','','- Source: `reports/2026-11-13-annual-archive-field-availability-2009-2026.json` (77 numeric fields × 18 UTC years = 1,386 cells).','- `REVIEW_REQUIRED`: at least one non-NULL value exists; physical quality, provenance, temporal completeness and source eligibility are not implied.','- `NOT_AVAILABLE`: the field has zero non-NULL values in that archive/year cell only; it may exist in another source archive.','- No `READY` classification is emitted from availability counts alone.','','## Cell summary','',f"- REVIEW_REQUIRED: {summary['REVIEW_REQUIRED']}",f"- NOT_AVAILABLE: {summary['NOT_AVAILABLE']}",f"- All-null cells in reconstruction snapshot: {len(allnull)}",'- 2026 is partial; Q1 2018 remains interim/live with no new proposals; 2021 remains diagnostic-only.','','## Per-year summary','','| Year | Archive rows | Field cells | REVIEW_REQUIRED | NOT_AVAILABLE | All-null fields |', '|---:|---:|---:|---:|---:|---|']
for y in byyear: md.append(f"| {y['year']} | {y['archive_rows']} | {y['field_cells']} | {y['review_required_cells']} | {y['not_available_cells']} | {', '.join(y['all_null_fields']) or '—'} |")
md += ['', 'Reproduce: `python3 scripts/build_archive_readiness_availability_baseline.py`. The per-cell JSON and CSV are `data/archive_readiness_availability_baseline_2009_2026.json` and `reports/2026-11-13-archive-readiness-availability-baseline.csv`. This does not refresh the production tail or query databases.']
(ROOT/'reports/2026-11-13-archive-readiness-availability-baseline.md').write_text('\n'.join(md)+'\n')
print(f"cells={len(rows)} readiness={dict(summary)} all_null={len(allnull)}")
