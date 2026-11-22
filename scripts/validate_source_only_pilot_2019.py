#!/usr/bin/env python3
"""Validate strict 2019 source-only candidate cohort, still lineage-review only."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rows=json.loads((R/'data/source-only-pilot-2019-strict-copy-concordance.json').read_text())
s=json.loads((R/'data/source_only_pilot_2019_validation.json').read_text())
with (R/'reports/2026-11-13-source-only-pilot-2019-row-evidence.csv').open(newline='') as f:e=list(csv.DictReader(f))
assert len(rows)==len(e)==233 and s['classification_counts']=={'RESTORED':0,'ESTIMATED':0,'REVIEW_REQUIRED':233,'MISSING':0}
assert len({r['dateTime'] for r in rows})==233 and all(int(r['dateTime'])%300==0 for r in rows)
assert all(r['old_units']==17 and r['wh_units']==17 and r['old_interval']==5 and r['wh_interval']==5 for r in rows)
assert all(r['old_temp']==r['wh_temp'] and r['old_rh']==r['wh_rh'] and r['old_rain']==r['wh_rain'] and r['old_rainrate']==r['wh_rainrate'] and r['old_wind']==r['wh_wind'] for r in rows)
assert s['third_archive_exact_rows']==0 and [b['n'] for b in s['blocks']]==[40,192,1]
assert s['neighbor_temperature_delta_c']['max']==2.533 and s['neighbor_temperature_delta_c']['count_gt_5c']==0
assert all(r['classification']=='REVIEW_REQUIRED' and 'SOURCE_LINEAGE_UNAUTHENTICATED' in r['reason_codes'] for r in e)
result={'status':'PASS','timestamp_rows':233,'restored':0,'estimated':0,'review_required':233,'missing':0,'blocks':[40,192,1],'copy_matches_all_five_fields':True,'db_writes':0,'q1_2018':'not queried','year_2021':'not queried'}
(R/'data/source_only_pilot_2019_validation_result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
