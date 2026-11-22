#!/usr/bin/env python3
"""Validate first-practical milestone ZIP structure, internal file hashes and required reports."""
import hashlib,json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
zp=R/'loucka_historical_audit_and_priority_corrections_v1.zip'
with zipfile.ZipFile(zp) as z:
 names=set(z.namelist()); assert 'MANIFEST.json' in names
 m=json.loads(z.read('MANIFEST.json'))
 assert m['status']=='FIRST_PRACTICAL_AUDIT_MILESTONE_WITH_LIMITATIONS'
 assert m['required_main_reports']==18 and m['required_reports_included']==18
 assert all(x in names for x in m['required_report_paths'])
 assert len(m['contents'])+1==len(names)
 for x in m['contents']:
  b=z.read(x['path']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],x['path']
 assert any(x['path']=='proposals/estimated_short_temperature_gaps/corrections.json' for x in m['contents'])
 assert any(x['path']=='proposals/restored_temperature/year_source_epoch_quality.csv' for x in m['contents'])
 assert any(x['path']=='reports/2026-11-13-rh-source-pair-interval6-cases.csv' for x in m['contents'])
ext=json.loads((R/'reports/2026-11-13-priority-milestone-zip-manifest.json').read_text())
assert ext['files']==len(names)
assert ext['sha256']==hashlib.sha256(zp.read_bytes()).hexdigest()
print(f'PASS: {len(names)} entries; 18/18 required reports; internal SHA-256 manifest and external archive hash verified')
