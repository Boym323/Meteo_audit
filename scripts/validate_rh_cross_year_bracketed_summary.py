#!/usr/bin/env python3
"""Validate the frozen cross-year RH bracket aggregate and scoped frost review."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/rh_cross_year_bracketed_candidate_summary.json').read_text())
rows=d['yearly_aggregates']
assert sum(x['paired_bracketed'] for x in rows)==121
assert sum(x['within_neighbor_range'] for x in rows)==43
assert sum(x['within_1_percent_midpoint'] for x in rows)==73
assert sum(x['euold_retains_rh'] for x in rows)==6
assert d['protected_period_exclusion']=={'q1_2018_excluded':True,'year_2021_excluded':True}
assert all(x['disposition']=='REVIEW_REQUIRED_FROST_OR_SENSOR_EPOCH' for x in d['selected_for_case_review'])
assert {x['timestamp'] for x in d['selected_for_case_review']}=={1512163800,1512164400,1512234000}
with (ROOT/'data/rh_cross_year_bracketed_candidate_summary.csv').open(newline='') as f:
 csvrows=list(csv.DictReader(f))
assert len(csvrows)==len(rows)
assert [int(x['paired_bracketed']) for x in csvrows]==[x['paired_bracketed'] for x in rows]
print('PASS: 121 year-stratified RH neighbor brackets; 43 within range; 73 near midpoint; three frost-period cases held for review.')
