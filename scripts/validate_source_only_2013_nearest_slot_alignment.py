#!/usr/bin/env python3
"""Validate the frozen 2013 nearest-slot alignment aggregation."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/source_only_2013_nearest_slot_alignment.json').read_text())
t=d['total']
assert t['source_rows']==t['distinct_projected_slots']==2025
assert t['offgrid_source_rows']==2022 and t['exact_grid_source_rows']==3
assert t['projected_slot_collisions']==0 and t['projected_reconstruction_rows']==2021 and t['projected_reconstruction_absent']==4
assert t['source_unit_interval_rows_usUnits17_interval5']==2025
assert t['projected_pocasi_eu_rows']==t['projected_gw1000_rows']==2021 and t['projected_pocasi_eu_old_rows']==5
groups=d['offset_groups']
assert [x['signed_offset_seconds'] for x in groups]==[-120,-60,0,60,120]
assert [x['source_rows'] for x in groups]==[57,548,3,971,446]
assert all(x['source_rows']==x['projected_slots'] for x in groups)
assert all(all(n==x['source_rows'] for n in x['copy_equal_primary_fields'].values()) for x in groups)
assert d['all_group_diagnostic_matches']=={'outTemp_direct':2010,'outHumidity_direct':2014,'rain_divide_10':1463,'rainRate_divide_10':2019,'windSpeed_multiply_3_6':1557,'denominator_source_rows':2025}
assert sum(x['disposition']=='RESTORED_PROPOSED_ACTIVE_2013_PILOT' for x in d['candidate_slot_dispositions'])==3
assert sum(x['disposition']=='REVIEW_REQUIRED_OFF_GRID_NO_SUPPORTED_SHIFT' for x in d['candidate_slot_dispositions'])==1
assert d['safety']=={'database_writes':0,'staging':False,'application':False,'publication':False}
print('PASS: 2,025 source rows; mixed offsets, no projected collisions; 4 absent targets; no global shift')
