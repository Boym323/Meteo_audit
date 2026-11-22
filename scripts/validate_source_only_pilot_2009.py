#!/usr/bin/env python3
"""Validate the bounded 2009 source-only REVIEW_REQUIRED evidence screen."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rows=json.loads((R/'data/source-only-pilot-2009-strong-copy-concordance.json').read_text())
s=json.loads((R/'data/source_only_pilot_2009_strong_copy_concordance_summary.json').read_text())
with (R/'reports/2026-11-13-source-only-pilot-2009-row-evidence.csv').open(newline='') as f:e=list(csv.DictReader(f))
assert len(rows)==len(e)==100 and s['classification_counts']=={'RESTORED':0,'ESTIMATED':0,'REVIEW_REQUIRED':100,'MISSING':0}
assert len({r['dateTime'] for r in rows})==100 and all(int(r['dateTime'])%300==0 for r in rows)
assert all(r['old_units']==17 and r['wh_units']==17 and r['old_interval']==5 and r['wh_interval']==5 for r in rows)
assert all(r['old_temp']==r['wh_temp'] and r['old_rh']==r['wh_rh'] and r['old_rain']==r['wh_rain'] and r['old_rainrate']==r['wh_rainrate'] and r['old_wind']==r['wh_wind'] for r in rows)
assert s['exact_site_old_value_matches']=={'outTemp':100,'outHumidity':100,'rain':0,'rainRate':99,'windSpeed':100}
assert [b['n'] for b in s['exact_300s_blocks']]==[14,86]
assert s['neighbor_temperature_delta_c']['max']==9.48 and s['zero_outTemp_count']==0
assert all(r['classification']=='REVIEW_REQUIRED' and 'SOURCE_LINEAGE_UNAUTHENTICATED' in r['reason_codes'] for r in e)
result={'status':'PASS','timestamp_rows':len(rows),'restored':0,'estimated':0,'review_required':100,'missing':0,'reason_codes_in_each_target':True,'database_writes':0,'q1_2018':'not queried','year_2021':'not queried'}
(R/'data/source_only_pilot_2009_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
