#!/usr/bin/env python3
import json
from pathlib import Path
d=json.loads((Path(__file__).resolve().parents[1]/'data/source_only_2016_sep19_zero_episode_context.json').read_text())
r=d['episode_source_rows']; assert len(r)==6 and all(x['WH1080_outTemp_c']==0 for x in r)
assert [x['old_weewx_outTemp_c'] for x in r]==[None,None,0,0,None,None]
assert [x['LuhaMet_temp_c'] for x in r]==[14.9,14.9,14.9,14.9,14.9,15.0]
assert d['all_six_archive_presence_at_two_targets']=={'loucka_reconstruction':0,'pocasi-loucka.eu':0,'pocasi-loucka.eu_GW1000':0,'pocasi-loucka.eu_old':0,'old_weewx':2,'weewx_WH1080':2}
assert d['disposition']=='REVIEW_REQUIRED; SOURCE_SENSOR_STUCK_SUSPECTED'
print('PASS: six-point regional-context review remains REVIEW_REQUIRED; no restoration emitted.')
