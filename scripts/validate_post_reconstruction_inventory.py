#!/usr/bin/env python3
"""Deterministic checks for the live U1 inventory artifacts."""
import csv, datetime, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
inventory=json.loads((ROOT/'POST_RECONSTRUCTION_INVENTORY.json').read_text())
annual=inventory['annual_coverage']
assert len(annual)==18
assert sum(int(r['row_count']) for r in annual)==1_690_201
assert inventory['rows_outside_2021_utc']==1_586_737
expected={'outTemp':17298,'outHumidity':159226,'rain':20917,'rainRate':10543,'windSpeed':26012,'barometer':16978}
for field,count in expected.items():
    found=sum(int(r['null_'+field]) for r in annual if int(r['utc_year'])!=2021)
    assert found==count,(field,found,count)
rows=list(csv.DictReader((ROOT/'ARCHIVE_GAP_INTERVALS.csv').open()))
assert len(rows)==24_488
seen=set()
for r in rows:
    target=int(r['target_epoch']);previous=int(r['previous_epoch']);delta=int(r['delta_seconds'])
    assert target-previous==delta
    assert delta>min(int(r['previous_interval_minutes']),int(r['current_interval_minutes']))*60
    assert datetime.datetime.fromtimestamp(target,datetime.timezone.utc).strftime('%Y-%m')==r['utc_year']+'-'+r['utc_month']
    key=(previous,target)
    assert key not in seen
    seen.add(key)
summary=list(csv.DictReader((ROOT/'ARCHIVE_TIME_COVERAGE.csv').open()))
assert sum(int(r['gap_edges']) for r in summary)==len(rows)
assert sum(int(r['unobserved_grid_slots_candidate']) for r in summary)==sum(int(r['unobserved_grid_slots_candidate']) for r in rows if r['unobserved_grid_slots_candidate'])
assert all(r['gap_classification']!='UNOBSERVED_CADENCE_SLOTS_CAUSE_UNKNOWN' or r['utc_year']!='2013' for r in rows)
print('PASS: 18 UTC years; row/null checkpoints; 24,488 unique interval-aware gap edges; UTC/delta/interval invariants; candidate-slot aggregate')
