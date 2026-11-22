#!/usr/bin/env python3
"""SUPERSEDED: historical P3 v2 simulator; preserved for audit history only."""
raise SystemExit('SUPERSEDED P3 v2 (24 estimates); use proposals/estimated_short_temperature_gaps_v2/simulate_v2_1.py')
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/'proposals/estimated_short_temperature_gaps_v2'
sys.path.insert(0,str(ROOT/'src'))
from meteo_audit.source_first import classify_before_estimate
meta=json.loads((PKG/'candidate_metadata.json').read_text())
ops=json.loads((PKG/'corrections.json').read_text())
assert len(meta)==107 and len(ops)==24
by={int(x['timestamp']):x for x in meta}
assert len(by)==107
assert len({(x['timestamp'],x['variable']) for x in ops})==24
assert all(x['variable']=='outTemp' and x['operation']=='insert' and x['expected_old_value'] is None for x in ops)
assert all(not any(by[int(x['timestamp'])]['exact_source_rows_by_archive'].values()) for x in ops)
assert all(by[int(x['timestamp'])]['reconstruction_changes_events_all_variables']==0 for x in ops)
assert all(abs(float(x['new_value'])-float(by[int(x['timestamp'])]['interpolation_value_c']))<1e-8 for x in ops)
assert all(classify_before_estimate(source_checks_complete=True,sources=[{'source_row_exists':False}],target_row_exists=False,change_event_count=0).status=='ESTIMATED_ELIGIBLE_FOR_REVIEW' for _ in [0])
batch=json.loads((PKG/'weather_mcp_batches.json').read_text())
assert batch['batch_count']==1 and batch['batches'][0]['size']<=50 and not batch['batches'][0]['episode_split']
episodes={(x['left']['t'],x['right']['t']) for x in meta if int(x['timestamp']) in {int(o['timestamp']) for o in ops}}
assert len(episodes)==14
out={'simulation':'offline-only','db_access':'none','input_targets':107,'simulated_estimated_inserts':len(ops),'source_conflicts_blocked':sum(x['p3_v2_status'].startswith('REVIEW_REQUIRED') for x in meta),'restored':0,'review_required':83,'missing':0,'batches':1,'max_batch_size':24,'episodes_kept_whole':14,'duplicate_operations':0,'dependency_order':'single-variable inserts only; no whole-row operations','validation':'PASS'}
(PKG/'simulation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
