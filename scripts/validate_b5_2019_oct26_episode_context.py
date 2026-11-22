#!/usr/bin/env python3
"""Offline validation of bounded 2019-10-26 source episode context."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=json.loads((R/'data/b5_2019_oct26_episode_source_context.json').read_text())
rows=p['rows'];assert len(rows)==14
inside=[x for x in rows if 1572134100<x['target_time']<1572138000]
ends={x['target_time']:x for x in rows if x['target_time'] in (1572134100,1572138000)}
assert len(inside)==12 and all(x['old_outTemp']==x['wh_outTemp'] for x in inside)
assert all(x['old_units']==x['wh_units']==17 and x['old_interval']==x['wh_interval']==5 for x in rows)
assert all(x['reconstruction_row'] is None and x['change_events']==0 and x['outTemp_events']==0 for x in inside)
assert ends[1572134100]['reconstruction_outTemp']==11.0 and ends[1572134100]['old_outTemp']==ends[1572134100]['wh_outTemp']==11.7
assert ends[1572138000]['reconstruction_outTemp']==10.7 and ends[1572138000]['old_outTemp']==ends[1572138000]['wh_outTemp']==11.55
assert sum(x['change_events'] for x in rows)==0
assert p['query_execution_timestamp_utc']=='NOT_CAPTURED_BY_WEATHER_MCP'
print('PASS: 12 exact source outTemp rows held; endpoint conflict and empty current history validated offline')
