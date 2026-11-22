#!/usr/bin/env python3
"""Validate run-length profile totals and the critical timestamp detail rows."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=json.loads((R/'data/gap_zero_temperature_runs/summary.json').read_text())
d=json.loads((R/'data/gap_zero_temperature_runs/top_zero_runs.json').read_text())
m=json.loads((R/'data/gap_zero_temperature_run_detail_query_manifest.json').read_text())
assert s['status']=='PASS' and s['chunks']==21 and s['input_zero_samples']==42298
t=s['totals']
assert t['zero_samples']==42298 and t['zero_run_count']==2247 and t['gaps_with_zero_run']==2085
assert t['singleton_runs']==641 and t['runs_2_to_5']==913 and t['runs_6_to_11']==311 and t['runs_12_plus']==382
assert t['max_run_samples']==2157 and t['runs_bracketed_by_nonzero']==0
rows={c['source_chunk']:c['rows'] for c in d['chunks']}
assert len(rows)==4 and rows[4][0]['sample_count']==2157
assert (rows[4][0]['first_ts'],rows[4][0]['last_ts'])==(1313919300,1314566100)
assert rows[95][0]['sample_count']==1391 and rows[91][0]['sample_count']==584
assert rows[101][0]['sample_count']==1705 and rows[101][0]['protection_scope']=='PROTECTED_Q1_2018_DIAGNOSTIC'
assert m['query_count']==4 and [int(x['source_chunk']) for x in m['queries']]==[4,91,95,101]
assert all(r['utc_year']!=2021 for group in s['by_year_gap_band'] for r in [group])
print('PASS: 21 zero-bearing chunks, 42,298 samples, 2,247 runs, longest-run timestamps, protected Q1 2018 separation')
