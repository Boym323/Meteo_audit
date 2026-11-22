#!/usr/bin/env python3
"""Validate bounded 2016-2017 nonzero B5 temperature-candidate review."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
e=json.loads((R/'data/b5_2016_2017_nonzero_temperature_candidates.json').read_text())
assert e['database_mode']=='READ_ONLY_SELECT_ONLY' and e['n']==111
by=e['by_year']
assert by['2016']['rows']==68 and by['2017']['rows']==43
assert by['2016']['oldWhEqual']==68 and by['2017']['oldWhEqual']==43
assert by['2016']['oldWhConflict']==by['2017']['oldWhConflict']==0
assert by['2016']['euoldRows']==68 and by['2017']['euoldRows']==43
assert by['2016']['euoldTempNonNull']==66 and by['2017']['euoldTempNonNull']==42
assert by['2016']['gridOff']==68 and by['2017']['gridOff']==43
assert by['2016']['exactRef']==by['2017']['exactRef']==0
assert by['2016']['endpointValueMatch']==66 and by['2017']['endpointValueMatch']==40
assert by['2016']['endpointMatchWithin120s']==62 and by['2017']['endpointMatchWithin120s']==32
assert by['2016']['eventCount']==by['2017']['eventCount']==0
assert len(e['records'])==111
for x in e['records']:
 assert x['old_outTemp'] is not None and float(x['old_outTemp'])!=0
 assert float(x['old_outTemp'])==float(x['wh_outTemp'])
 assert int(x['dateTime'])%300!=0
 assert x['old_usUnits']==x['wh_usUnits']==17
 assert x['old_interval'] in (5,6) and x['wh_interval']==x['old_interval']
 assert x['outTemp_event_count'] in (0,None)
assert (R/'sql/readonly/b5_2016_2017_nonzero_temperature_candidates.sql').exists()
reg=json.loads((R/'config/active_proposal_registry.json').read_text())
nonzero_ts={int(x['dateTime']) for x in e['records']}
for p in reg['packages']:
 if p['status']!='ACTIVE':continue
 ops=json.loads((R/p['path']/'corrections.json').read_text())
 assert not any(int(x['timestamp']) in nonzero_ts and x['variable']=='outTemp' for x in ops),p['package_id']
report=(R/'reports/2026-11-14-B5-2016-2017-nonzero-temperature-review.md').read_text()
assert '13,629' in report and '106 temperatures' in report and 'No `RESTORED` or `ESTIMATED` proposal' in report
print('PASS: 111 off-grid nonzero temperatures; 106 endpoint-value matches (94 within 120s); 5 unique unresolved cases; zero proposals/events.')
