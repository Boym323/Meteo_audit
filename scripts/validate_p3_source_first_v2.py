#!/usr/bin/env python3
"""Validate the preserved historical P3 v2 snapshot (not the active v2.1 package)."""
import csv,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'archives/p3_v2_pre_filter_history_review'
m=json.loads((P/'manifest.json').read_text())
for name,rec in m['artifacts'].items():
 b=(P/name).read_bytes();assert len(b)==rec['bytes'] and hashlib.sha256(b).hexdigest()==rec['sha256'],name
meta=json.loads((P/'candidate_metadata.json').read_text());ops=json.loads((P/'corrections.json').read_text());batch=json.loads((P/'weather_mcp_batches.json').read_text())
review=list(csv.DictReader((P/'review_required.csv').open()))
assert len(meta)==107 and len(ops)==24 and len(review)==83
assert m['revision']=='v2' and m['estimated_count']==24 and m['review_required_count']==83
by={int(x['timestamp']):x for x in meta};assert len(by)==107
assert all(by[int(x['timestamp'])]['p3_v2_status']=='ESTIMATED' for x in ops)
assert all(not any(by[int(x['timestamp'])]['exact_source_rows_by_archive'].values()) for x in ops)
assert all(by[int(x['timestamp'])]['reconstruction_changes_events_all_variables']==0 for x in ops)
assert all(x['p3_v2_status'].startswith('REVIEW_REQUIRED') for x in meta if any(x['exact_source_rows_by_archive'].values()))
assert batch['batch_count']==1 and batch['batches'][0]['size']==24 and not batch['batches'][0]['episode_split']
assert batch['batches'][0]['episodes']==14 and batch['max_batch_size']==50
assert m['database_access']=='READ_ONLY_SELECT_ONLY' and m['writes_or_staging'] is False
print(json.dumps({'validation':'PASS_HISTORICAL_SUPERSEDED','active':False,'snapshot':'archives/p3_v2_pre_filter_history_review','targets':107,'RESTORED':0,'ESTIMATED':24,'REVIEW_REQUIRED':83,'MISSING':0,'batch_count':1,'batch_size':24,'episodes':14,'manifest_files':len(m['artifacts'])},indent=2))
