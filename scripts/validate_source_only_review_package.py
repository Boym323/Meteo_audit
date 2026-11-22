#!/usr/bin/env python3
"""Deterministic validator for the P3 whole-row source-only review package."""
import csv,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'proposals/restored_source_only_rows_v2'
m=json.loads((P/'manifest.json').read_text())
for name,rec in m['artifacts'].items():
 data=(P/name).read_bytes()
 assert len(data)==rec['bytes'] and hashlib.sha256(data).hexdigest()==rec['sha256'],name
rows=list(csv.DictReader((P/'source_only_rows.csv').open()))
review=json.loads((P/'review_required.json').read_text())
ops=json.loads((P/'corrections.json').read_text())
b=json.loads((P/'weather_mcp_batches.json').read_text())
assert len({int(x['timestamp']) for x in review})==83
assert len(rows)==165 and len(ops)==0
assert m['RESTORED']==m['ESTIMATED']==m['MISSING']==0 and m['REVIEW_REQUIRED']==83
assert b['batch_count']==0 and not b['batches'] and b['max_batch_size']==50
assert all(x['classification']=='REVIEW_REQUIRED' for x in review)
assert {x['source_database'] for x in rows}=={'old_weewx','weewx_WH1080'}
assert all(int(x['timestamp'])<1609459200 for x in rows),'2021+ target escaped protected scope'
print(json.dumps({'validation':'PASS','source_timestamps':83,'archive_rows':165,'restored':0,'estimated':0,'review_required':83,'missing':0,'correction_operations':0,'mcp_batches':0,'database_access':'none'},indent=2))
