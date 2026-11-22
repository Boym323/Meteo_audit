#!/usr/bin/env python3
import json,csv
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2016_gap_source_concordance.json').read_text());s=json.loads((R/'data/b5_2016_gap_source_concordance_summary.json').read_text())
assert len(d['records'])==135 and s['gap_events']==135
assert len({r['gap_no'] for r in d['records']})==135
assert s['source_union_timestamps']==s['exact_timestamp_pairs']==5381
assert s['old_only_timestamps']==s['wh1080_only_timestamps']==s['unit_interval_conflicts']==0
assert s['field_concordance']['outTemp']['paired_nonnull']==70 and s['field_concordance']['outTemp']['equal']==70
assert s['field_concordance']['rainRate']['equal']==5381
assert s['field_concordance']['pressure']['equal']==5381
assert s['field_concordance']['altimeter']['conflict']==5300
assert s['wh1080_outTemp_zero_rows']==5313 and s['decision'].startswith('SOURCE_AVAILABILITY')
for field,stats in s['field_concordance'].items():
 for key in ['paired_nonnull','equal','conflict','null_asymmetry']:
  assert stats[key]==sum(r['fields'][field][key] for r in d['records']),(field,key)
assert sum(r['source_union_timestamps'] for r in d['records'])==5381
assert d['database_mode']=='READ_ONLY_SELECT_ONLY' and d['writes']==0
assert len(list(csv.DictReader((R/'reports/2026-11-14-B5-2016-gap-source-concordance.csv').open())))==10
assert 'no correction proposed' in d['limitations'][2].lower()
print('PASS: 135 gap episodes; 5,381 exact source timestamp pairs; field concordance totals reconcile; no correction eligibility inferred.')
