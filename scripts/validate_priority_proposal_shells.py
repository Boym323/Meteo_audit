#!/usr/bin/env python3
"""Validate the five P1-P5 package schemas, hashes, safety boundaries and P3 simulation."""
import csv,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
PKGS=['restored_temperature','restored_humidity','estimated_short_temperature_gaps','estimated_humidity_2022','restored_secondary_sensors']
required={'README.md','manifest.json','corrections.json','corrections.csv','excluded_cases.csv','source_validation_metadata.json','weather_mcp_batches.json','simulation.json'}
checks=[]
for n in PKGS:
 d=R/'proposals'/n; missing=required-{p.name for p in d.iterdir()}
 m=json.loads((d/'manifest.json').read_text()); js=json.loads((d/'corrections.json').read_text()); batch=json.loads((d/'weather_mcp_batches.json').read_text()); sim=json.loads((d/'simulation.json').read_text())
 with (d/'corrections.csv').open(newline='',encoding='utf8') as f: rows=list(csv.DictReader(f))
 with (d/'excluded_cases.csv').open(newline='',encoding='utf8') as f: excluded=list(csv.DictReader(f))
 assert not missing,(n,missing)
 assert len(excluded)>0 and m['exclusion_scopes_non_additive'] is True
 assert batch.get('status') in {'NO_CANDIDATES; no MCP call made','PROPOSALS_ONLY_NOT_SUBMITTED'}
 assert m['safety']['database']=='READ_ONLY' and m['safety']['apply']=='prohibited'
 if n=='estimated_short_temperature_gaps':
  meta=json.loads((d/'candidate_metadata.json').read_text()); snap=json.loads((d/'source_snapshot.json').read_text())
  assert len(js)==len(rows)==len(meta)==107 and m['candidate_count']==107
  assert sim['status']=='PASS_LOCAL_OFFLINE_SIMULATION' and sim['candidate_inserts']==107 and sim['database_access'] is False
  assert len(batch['batches'])==3 and [len(x['corrections']) for x in batch['batches']]==[50,50,7]
  assert [c for x in batch['batches'] for c in x['corrections']]==js
  assert len(snap['source_observations'])==100 and snap['target_history_absent'] is True
  assert all(c['operation']=='insert' and c['variable']=='outTemp' and c['expected_old_value'] is None and c['us_units']==16 and c['interval_minutes']==5 for c in js)
  assert all(1546300800<=c['timestamp']<1609459200 for c in js)
  assert all(x['classification']=='ESTIMATED' and x['uncertainty_abs_error_c']['p95']==0.75 and all(x['gates'].values()) for x in meta)
  status='PASS_VALIDATED_ESTIMATED_PACKAGE'
 else:
  assert len(js)==len(rows)==m['candidate_count']==0,(n,'unexpected candidate content')
  assert sim['candidate_count']==0 and sim['offline_only'] is True
  assert batch['batches']==[]
  status='PASS_BLOCKED_EMPTY_PACKAGE'
 for fn,record in m['artifacts'].items():
  payload=(d/fn).read_bytes(); assert len(payload)==record['bytes'] and hashlib.sha256(payload).hexdigest()==record['sha256'],(n,fn,'manifest hash mismatch')
 checks.append({'package':n,'status':status,'candidates':len(js),'excluded_scopes':len(excluded)})
out={'validator':'scripts/validate_priority_proposal_shells.py','status':'PASS','checks':checks,'database_access':False,'mcp_calls':0}
(R/'reports/2026-11-13-priority-proposal-package-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False))
