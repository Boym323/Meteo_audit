#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/'data/b5_2009_2013_gap_per_archive_availability.json').read_text())
assert d['gap_count']==163 and d['archive_gap_cells']==978
assert len(d['results'])==978 and len(d['alignment_results'])==92
a=d['alignment_summary']; assert (a['source_rows'],a['exact_wh1080_key_matches'],a['exact_eu_old_key_matches'],a['exact_reconstruction_key_matches'],a['source_projection_collisions'],a['rows_projecting_to_occupied_reconstruction_slots'],a['on_300s_grid'],a['off_300s_grid'])==(192,192,192,0,0,92,100,92)
assert a['field_conflicts']['outTemp']=={'old_vs_wh':1,'old_vs_euold':1}
assert a['field_conflicts']['usUnits']=={'old_vs_wh':0,'old_vs_euold':192}
assert a['field_conflicts']['rain']=={'old_vs_wh':0,'old_vs_euold':128}
assert a['field_conflicts']['pressure']=={'old_vs_wh':191,'old_vs_euold':190}
by={(r['year'],r['gap_id'],r['archive']):r for r in d['results']}
for g in d['gaps']:
 y=int(g['prev_utc'][:4]);old=by[(y,g['gap_id'],'old_weewx')]
 matches=[r for r in d['alignment_results'] if r['year']==y and r['gap_id']==g['gap_id']]
 if old['source_rows']:
  assert len(matches)==1 and int(matches[0]['old_source_rows'])==old['source_rows']
  a=matches[0]
  assert int(a['exact_wh1080_matches'])==old['source_rows']
  assert int(a['exact_eu_old_matches'])==old['source_rows']
  assert int(a['exact_reconstruction_matches'])==0 and int(a['source_projection_collisions'])==0
 else: assert not matches
assert all(r['source_rows']==0 for r in d['results'] if r['archive'] in ('reconstruction','eu','gw1000'))
assert d['safety']['writes']==0 and d['safety']['staging'] is False and d['safety']['application'] is False
assert d['safety']['excluded_years']==[2018,2021]
print('PASS: 163 B5 events × six archives; counts, exact-key and field-concordance aggregates reconcile; projection and safety checks pass.')
