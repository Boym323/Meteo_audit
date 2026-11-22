#!/usr/bin/env python3
"""Validate frozen read-only GW3000 JSONL payload against its approval manifest."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'data/GW3000_INSERT_ONLY_BACKFILL_PAYLOAD.jsonl';m=json.loads((R/'data/GW3000_INSERT_ONLY_BACKFILL_MANIFEST.json').read_text())
rows=[json.loads(line) for line in p.open()]
assert len(rows)==m['row_counts']['source_rows']==4651
assert rows[0]['dateTime']==m['source_window']['first_source_timestamp']
assert rows[-1]['dateTime']==m['source_window']['captured_source_max']
assert len({r['dateTime'] for r in rows})==len(rows)
fields=set(m['metadata']['mapping_fields_sorted_lexically_for_hash'])
assert all(set(r)==fields for r in rows)
assert all(r['usUnits']==16 and r['interval']==5 for r in rows)
nulls={k:sum(r[k] is None for r in rows) for k in fields-{'dateTime','usUnits','interval'}}
assert nulls==m['source_null_counts_by_value_column']
digest=hashlib.sha256(p.read_bytes()).hexdigest()
expected=m['payload']['sha256']
assert digest==expected,(digest,expected)
print(json.dumps({'status':'PASS','rows':len(rows),'columns':80,'payload_sha256':digest,'null_counts_match':True,'target_writes_performed':False},indent=2))
