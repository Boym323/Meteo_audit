#!/usr/bin/env python3
"""Validate compact read-only reconciliation aggregates for pending candidates."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'reports/2026-11-12-pending-candidate-current-state.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
with (ROOT/'reports/2026-11-12-pending-candidate-scope.csv').open(newline='',encoding='utf-8') as f: scopes=list(csv.DictReader(f))
assert len(rows)==9
assert sum(int(r['pending_candidates']) for r in rows)==272
assert sum(int(r['missing_archive']) for r in rows)==2
assert sum(int(r['has_any_history']) for r in rows)==58
assert sum(int(r['later_applied_targets_since_own_batch']) for r in rows)==58
assert sum(int(r['later_applied_events_since_own_batch']) for r in rows)==59
assert sum(int(r['current_matches_latest_history_expected']) for r in rows)==58
assert sum(int(r['current_matches_proposal']) for r in rows)==37
assert sum(int(r['current_matches_source']) for r in rows)==47
assert sum(int(r['candidates']) for r in scopes if r['scope']=='2018_Q1_INTERIM')==8
assert sum(int(r['candidates']) for r in scopes if r['scope']=='other')==264
assert not any(r['scope']=='2021_DIAGNOSTIC_ONLY' for r in scopes)
print('pending candidates reconciled:', {'candidates':272,'missing_archive':2,'later_applied_targets':58,'later_applied_events':59,'Q1_2018_interim':8,'2021_candidates':0})
