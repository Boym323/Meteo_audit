#!/usr/bin/env python3
"""Validate saved row-level 2017 strict source-only review (no DB access)."""
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'data/source_only_strict_2017_cohort.json'
d=json.loads(p.read_text()); rows=d['targets']
assert d['count']==10 and len(rows)==10 and d['neighbor_rows_requested']==100
assert d['findings']=={'zero_outTemp':10,'null_outHumidity':10,'exact_copies':10,'change_events':0,'third_archive_rows':0}
assert len({r['ts'] for r in rows})==10
assert all(r['old_usUnits']==17 and r['wh_usUnits']==17 and r['old_interval']==5 and r['wh_interval']==5 for r in rows)
assert all(r['old_outTemp']==r['wh_outTemp']==0 for r in rows)
assert all(r['old_outHumidity'] is None and r['wh_outHumidity'] is None for r in rows)
assert all(r['old_rain']==r['wh_rain'] and r['old_rainRate']==r['wh_rainRate'] and r['old_windSpeed']==r['wh_windSpeed'] for r in rows)
assert all(r['change_events']==0 and not r['has_pocasi_main'] and not r['has_gw1000'] and not r['has_pocasi_old'] for r in rows)
assert all(r['neighbor_rows_10min']==5 and r['neighbor_min_outTemp'] is not None and r['neighbor_max_outTemp'] is not None for r in rows)
print('PASS: 10 target rows, exact copies, zero temperatures, RH NULL, target/history absence, and 10-minute context')
