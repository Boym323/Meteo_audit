#!/usr/bin/env python3
"""Validate the 2010 source-only off-grid nearest-slot disposition."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
d=json.loads((r/'data/source_only_2010_offgrid_nearest_slot_detail.json').read_text())
g=d['offset_groups'];assert [int(x['signed_offset']) for x in g]==[-120,-60,60,120]
assert [int(x['n']) for x in g]==[189,413,1322,65]
assert sum(int(x['n']) for x in g)==1989
assert sum(int(x['nearest_target_rows']) for x in g)==1989
assert sum(int(x['source_copy_all5_equal']) for x in g)==1988
assert sum(int(x['temp_exact_match']) for x in g)==1955
assert sum(int(x['rh_exact_match']) for x in g)==1962
assert sum(int(x['rain_converted_match']) for x in g)==1360
assert sum(int(x['rainRate_converted_match']) for x in g)==1982
assert sum(int(x['wind_converted_match']) for x in g)==31
assert sum(int(x['all5_converted_value_matches']) for x in g)==8
m=d['nearest_slot_summary'][0]
assert int(m['nearest_slots'])==1983 and int(m['source_rows'])==1989
assert int(m['collision_slots'])==6 and int(m['max_sources_per_slot'])==2
assert int(m['nearest_slots_without_target_row'])==0
n=d['nearest_target_field_nulls'];assert (n['source_rows'],n['nearest_target_rows'])==(1989,1989)
assert (n['outTemp'],n['outHumidity'],n['rain'],n['rainRate'],n['windSpeed'])==(0,0,3,3,0)
assert d['corrections']==0 and d['db_writes']==0
assert Path('reports/2026-11-13-source-only-2010-offgrid-cohort.md').is_file()
assert Path('sql/readonly/source_only_2010_offgrid_nearest_slot_detail.sql').is_file()
print('PASS: 1,989 off-grid rows; offsets, copy concordance, nearest slot completeness/collisions and variable null counts reconcile')
