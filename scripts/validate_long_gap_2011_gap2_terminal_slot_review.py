#!/usr/bin/env python3
"""Validate the frozen terminal-key evidence for 2011 long-gap event 2."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/long_gap_2011_gap2_terminal_slot_review.json').read_text())
assert d['cohort_context']['old_weewx_rows']==d['cohort_context']['weewx_WH1080_rows']==910
assert d['cohort_context']['grid_aligned_source_rows']==909 and d['cohort_context']['offgrid_source_rows']==1
r={x['timestamp']:x for x in d['terminal_keys']}
assert set(r)=={1312296300,1312296600,1312296840,1312296900}
missing=r[1312296600]
assert all(v is False for v in missing['presence'].values())
assert missing['change_events']==0 and missing['disposition']=='MISSING_REVIEW_REQUIRED_NO_SOURCE_VALUE'
offgrid=r[1312296840]
assert offgrid['grid_remainder_seconds']==240 and offgrid['outTemp']['old_weewx']==offgrid['outTemp']['weewx_WH1080']==24.7
end=r[1312296900]
assert end['presence']['loucka_reconstruction'] and end['outTemp']['loucka_reconstruction']==24.7
assert d['safety']=={'database_writes':0,'staging':False,'application':False,'publication':False}
assert 'No restoration or estimation proposal' in d['decision']
print('PASS: 2011 gap-2 terminal slot absent in all six archives; off-grid key not shifted; no proposal')
