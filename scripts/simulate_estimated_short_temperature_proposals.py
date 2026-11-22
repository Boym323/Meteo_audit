#!/usr/bin/env python3
"""SUPERSEDED: historical P3 v1 estimate simulator; not active or for checkpoint reproduction."""
raise SystemExit("SUPERSEDED P3 v1 simulator; use proposals/estimated_short_temperature_gaps_v2/simulate_v2_1.py")
import json,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'proposals/estimated_short_temperature_gaps'
s=json.loads((D/'source_snapshot.json').read_text());cs=json.loads((D/'corrections.json').read_text());ms=json.loads((D/'candidate_metadata.json').read_text())
epochs={int(o['timestamp']) for o in s['source_observations']};absent=set(s['target_timestamps_absent'])
src={(o['database'],int(o['timestamp']),o['variable']):float(o['value']) for o in s['source_observations']};seen=set()
for c,m in zip(cs,ms):
 t=int(c['timestamp']);assert t in absent and t not in seen;seen.add(t)
 assert c['operation']=='insert' and c['expected_old_value'] is None and c['us_units']==16 and c['interval_minutes']==5
 assert 1546300800<=t<1609459200 and src[(c['source_database'],int(c['source_time']),c['variable'])]==float(c['source_value'])
 l,r=m['left'],m['right'];assert int(l['t']) in epochs and int(r['t']) in epochs and l['t']<t<r['t']
 assert all(m['gates'].values()) and m['gap_s']<=3600
 assert 20<=m['context']['left']['rh']<=95 and 20<=m['context']['right']['rh']<=95
 assert m['context']['left']['rain']==m['context']['right']['rain']==0 and m['context']['left']['rate']==m['context']['right']['rate']==0
 assert m['context']['left']['wind']>=5 and m['context']['right']['wind']>=5
 v=math.floor((l['v']+(r['v']-l['v'])*(t-l['t'])/(r['t']-l['t']))*100+0.5)/100;assert math.isclose(v,c['new_value'],abs_tol=1e-9)
assert len(seen)==len(cs)==107
result={'status':'PASS_LOCAL_OFFLINE_SIMULATION','database_access':False,'source_endpoints':len(src),'candidate_inserts':len(cs),'before':{'selected_existing_endpoint_rows':len(s['source_observations']),'nonnull_outTemp':len(s['source_observations'])},'after':{'selected_endpoint_and_insert_rows':len(s['source_observations'])+len(cs),'nonnull_outTemp':len(s['source_observations'])+len(cs)},'batches':3,'max_batch_size':50,'target_conflicts':0,'interpolation_reproduced':True,'other_fields_on_insert':'NULL; no derived calculations','scope':'selected endpoints and proposed inserts only','uncertainty':'empirical masked 2019-2020 p50/p90/p95 absolute error 0.15/0.55/0.75 C; limitations retained'}
(D/'simulation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
