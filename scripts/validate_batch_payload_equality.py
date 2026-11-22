#!/usr/bin/env python3
"""Require exact field-operation payload equality between each active batch file and corrections.json."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
reg=json.loads((ROOT/'config/active_proposal_registry.json').read_text())
checked=[]
for pkg in reg['packages']:
 if pkg.get('status')!='ACTIVE':continue
 d=ROOT/pkg['path'];canonical=json.loads((d/'corrections.json').read_text());bp=d/'weather_mcp_batches.json'
 assert bp.exists(),f"{pkg['package_id']}: missing batch file"
 batches=json.loads(bp.read_text()); batches=batches if isinstance(batches,list) else batches.get('batches',[])
 payload=[]
 for b in batches: payload += b.get('operations',b.get('corrections',[]))
 assert payload==canonical,(pkg['package_id'],'batch payload differs from canonical corrections.json')
 assert sum(len(b.get('operations',b.get('corrections',[]))) for b in batches)==pkg['field_operations']
 assert all(len(b.get('operations',b.get('corrections',[])))<=50 for b in batches)
 checked.append({'package_id':pkg['package_id'],'operations':len(payload),'batches':len(batches),'exact_payload_equality':'PASS'})
print(json.dumps({'status':'PASS','packages':len(checked),'operations':sum(x['operations'] for x in checked),'packages_detail':checked,'database_access':'NONE'},indent=2))
