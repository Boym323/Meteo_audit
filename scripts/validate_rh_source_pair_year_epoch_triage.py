#!/usr/bin/env python3
"""Validate RH source pair year/interval triage against bounded aggregate output."""
import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((R/'reports/2026-11-13-rh-source-pair-year-epoch-triage.csv').open()))
assert len(rows)==11
assert sum(int(x['paired_candidates']) for x in rows)==30391
assert sum(int(x['exact_copy_agreement']) for x in rows)==30385
assert sum(int(x['conflict_count']) for x in rows)==6
assert sum(int(x['both_interval_6']) for x in rows)==4
assert sum(int(x['both_interval_5']) for x in rows)==30387
assert sum(int(x['both_units_17']) for x in rows)==30391
assert sum(int(x['target_null']) for x in rows)==30391
assert all(x['archive_lineage_status']=='UNVERIFIED' for x in rows)
problems=list(csv.DictReader((R/'reports/2026-11-13-rh-source-pair-interval6-cases.csv').open()))
assert len(problems)==4 and len({x['dateTime_utc'] for x in problems})==4
assert all(x['old_interval']==x['wh_interval']=='6' and x['old_usUnits']==x['wh_usUnits']=='17' for x in problems)
assert sum(x['utc_year']=='2019' and int(x['conflict_count'])==6 for x in rows)==1
print('PASS: 30,391 candidates reconcile; 30,385 agreement, 6 conflicts, 4 interval-6 exceptions')
