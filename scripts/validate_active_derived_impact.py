#!/usr/bin/env python3
"""Validate scope/registry consistency for the provisional J4 impact matrix."""
import csv,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
reg=json.loads((R/'config/active_proposal_registry.json').read_text())
d=json.loads((R/'data/active_derived_correction_impact.json').read_text())
rows=d['operations'];summary=d['summary']
assert summary['operation_count']==reg['active_operation_count']
assert summary['timestamp_count']==reg['active_unique_timestamps']
assert summary['physical_insert_operations']==reg['active_insert_operations'] and summary['update_operations']==reg['active_update_operations']
assert len(rows)==reg['active_operation_count']
assert len({(r['timestamp'],r['variable']) for r in rows})==reg['active_operation_count']
assert sum(r['operation']=='insert' for r in rows)==reg['active_insert_operations']
assert sum(r['operation']=='update' for r in rows)==reg['active_update_operations']
assert len({r['timestamp'] for r in rows})==reg['active_unique_timestamps']
assert all(r['dependency_basis'].startswith('PROVISIONAL_CANDIDATE_ONLY') for r in rows)
assert all('2021' not in datetime.fromtimestamp(r['timestamp'],timezone.utc).isoformat() for r in rows)
assert all(not (datetime.fromtimestamp(r['timestamp'],timezone.utc).year==2018 and datetime.fromtimestamp(r['timestamp'],timezone.utc).month<=3) for r in rows)
csvrows=list(csv.DictReader((R/'reports/2026-11-13-active-derived-correction-impact.csv').open()))
assert len(csvrows)==reg['active_operation_count']
assert set(summary['unique_candidate_derived_variables']) <= {r['variable'] for r in csv.DictReader((R/'reports/2026-11-13-derived-variable-schema-map.csv').open())}
assert summary['safety'].startswith('READ_ONLY')
print('PASS: active operation inventory, duplicate/protected-period guards, provisional dependency labels, and derived-variable schema coverage.')
