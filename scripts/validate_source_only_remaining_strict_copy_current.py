#!/usr/bin/env python3
"""Cross-check the bounded ten-row strict-copy disposition against current active proposals."""
import json
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
cohort=json.loads((R/'data/source_only_remaining_strict_copy_cohorts_current.json').read_text())
registry=json.loads((R/'config/active_proposal_registry.json').read_text())
rows=cohort['records'];assert len(rows)==10 and len({r['ts'] for r in rows})==10
active={p['package_id']:p for p in registry['packages'] if p['status']=='ACTIVE'}
assert 'restored-source-only-2020-march-outtemp-v2' in active
assert 'restored-source-only-2020-march-outtemp' not in active
assert next(p for p in registry['packages'] if p['package_id']=='restored-source-only-2020-march-outtemp')['status']=='SUPERSEDED'
keys=defaultdict(list)
for p in active.values():
    for op in p.get('operation_keys',[]):keys[int(op['timestamp'])].append((p['package_id'],op['variable']))
counts=Counter(r['current_disposition'] for r in rows)
expected={
 'ACTIVE_2013_PILOT_EXISTING_CADENCE_RESTRICTION':3,
 'REVIEW_REQUIRED_SOURCE_SENSOR_STUCK_SUSPECTED':2,
 'RESTORED_PROPOSAL_V2_OUTTEMP_ONLY_NOT_APPROVED':4,
 'REVIEW_REQUIRED_SOURCE_LOCAL_TEMPERATURE_CONFLICT':1,
}
assert dict(counts)==expected,(counts,expected)
for r in rows:
    t=int(r['ts']);d=r['current_disposition'];ops=keys.get(t,[])
    if d=='ACTIVE_2013_PILOT_EXISTING_CADENCE_RESTRICTION':
        assert sorted(v for _,v in ops)==['outHumidity','outTemp']
        assert all(p=='restored-source-only-2013-july-pilot' for p,_ in ops)
    elif d=='RESTORED_PROPOSAL_V2_OUTTEMP_ONLY_NOT_APPROVED':
        assert ops==[('restored-source-only-2020-march-outtemp-v2','outTemp')]
    else: assert not ops,(t,d,ops)
assert active['restored-source-only-2020-march-outtemp-v2']['user_approval']=='NOT_APPROVED'
assert active['restored-source-only-2020-march-outtemp-v2']['actual_weather_mcp_dry_run']=='NOT_RUN'
assert active['restored-source-only-2020-march-outtemp-v2']['actual_application']=='NOT_APPLIED'
assert registry['database_mode']=='READ_ONLY' and registry['staging'] is False and registry['application_performed'] is False
assert not any(__import__('datetime').datetime.fromtimestamp(t,__import__('datetime').timezone.utc).year==2021 for t in keys)
assert not any(__import__('datetime').datetime.fromtimestamp(t,__import__('datetime').timezone.utc).year==2018 and __import__('datetime').datetime.fromtimestamp(t,__import__('datetime').timezone.utc).month<=3 for t in keys)
print(json.dumps({'status':'PASS','scope_rows':len(rows),'dispositions':dict(counts),'active_2013_field_operations':6,'active_2020_march_outTemp_operations':4,'held_candidates':3,'superseded_v1_preserved':True,'active_registry_operations':registry['active_operation_count'],'database_access':'NONE','writes':0},ensure_ascii=False))
