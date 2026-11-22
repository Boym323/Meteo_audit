#!/usr/bin/env python3
"""Prevent historical P3 v1 counts from being presented as active recommendations."""
from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
checks={
 'reports/P3_INDEPENDENT_REVIEW.md':['Current disposition (2026-11-13): RESTORED 0, ESTIMATED 21, REVIEW_REQUIRED 86','Historical v2 decision'],
 'reports/CONSOLIDATED_CORRECTIONS_REPORT.md':['Active P3 v2.1 is **RESTORED 0, ESTIMATED 21, REVIEW_REQUIRED 86','historical v1 107 interpolations are not active'],
 'reports/MASTER_AUDIT_REPORT.md':['Current P3 counts are **RESTORED 0 / ESTIMATED 21 / REVIEW_REQUIRED 86'],
 'reports/NEXT_STEPS.md':['aktivní rozhodnutí je v2.1: 21 ESTIMATED / 86 REVIEW_REQUIRED','Historických 24 estimates v2 a 107 v1 je superseded'],
 'MASTER_PLAN.md':['Historický checkpoint P3 v1 — 107 interpolací (superseded revizí v2.1)','Aktuální P3 v2.1: RESTORED 0 / ESTIMATED 21 / REVIEW_REQUIRED 86'],
 'STATUS.md':['Historický P3 v1 checkpoint — 107 interpolací (superseded revizí v2.1; 2026-11-13)','Aktivní stav P3 v2.1 je RESTORED 0 / ESTIMATED 21 / REVIEW_REQUIRED 86'],
 'reports/LOCAL_SIMULATION_REPORT.md':['Historická P3 v1 simulation — superseded revizí v2.1','P3 v1 je superseded'],
 'EXPERT_REVIEW_REQUIRED.md':['Historical P3 v1 supplement — short estimated gaps (superseded by v2.1','These candidates are no longer active recommendations'],
 'reports/2026-11-13-estimated-short-temperature-gap-proposals.md':['Historical P3 v1 proposal report — superseded by v2.1','not a current recommendation'],
 'reports/SOURCE_ONLY_GAP_OVERLAY_2009_2020.md':['archived P3 v1/v2 snapshots','Current recommendation status is P3 v2.1'],
 'reports/2026-11-13-priority-proposal-package-validation.SUPERSEDED.md':['historical artifact','not the current P3 disposition'],
 'decisions.md':['The earlier 107-value P3 v1 entry above is preserved as an append-only historical decision','Current P3 v2.1 disposition: RESTORED 0 / ESTIMATED 21 / REVIEW_REQUIRED 86'],
}
for f,needles in checks.items():
 s=(r/f).read_text()
 for n in needles: assert n in s,(f,n)
active=json.loads((r/'proposals/estimated_short_temperature_gaps_v2/manifest.json').read_text())
assert active['revision']=='v2.1'
assert (active['restored_count'],active['estimated_count'],active['review_required_count'],active['missing_count'])==(0,21,86,0)
print(f'PASS: {len(checks)} active and historical narrative locations match active P3 v2.1 manifest')
