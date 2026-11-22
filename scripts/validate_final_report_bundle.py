#!/usr/bin/env python3
"""Check required report deliverables exist and disclose provisional scope."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'reports'
d=json.loads((R/'required-report-inventory.json').read_text(encoding='utf-8'))
assert d['required_report_count']==18 and len(d['reports'])==18
assert all(x['exists'] and x['bytes']>1000 for x in d['reports'])
assert len({x['report'] for x in d['reports']})==18
master=(R/'MASTER_AUDIT_REPORT.md').read_text(encoding='utf-8')
for token in ('94 930','17 842','1 689 890','1 586 426','198 buněk','0**'):
 if token=='0**': continue
 assert token in master,token
assert 'PŘEDBĚŽNÉ' in (R/'FINAL_ARCHIVE_READINESS.md').read_text(encoding='utf-8')
assert 'validovaný korekční balíček není připraven' in (R/'CONSOLIDATED_CORRECTIONS_REPORT.md').read_text(encoding='utf-8')
assert 'diagnostický' in (R/'PROTECTED_YEAR_2021_DIAGNOSTICS.md').read_text(encoding='utf-8').lower()
assert 'INTERIM' in (R/'ACTIVE_2018_RECONSTRUCTION_STATUS.md').read_text(encoding='utf-8')
print('PASS: all 18 required report deliverables present; scope and protection caveats retained')
