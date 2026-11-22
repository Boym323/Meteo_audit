#!/usr/bin/env python3
import json,csv,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2018_gap_source_concordance.json').read_text());s=json.loads((R/'data/b5_2018_gap_source_concordance_summary.json').read_text())
assert len(d['records'])==63 and s['gap_events']==s['protected_q1_events']==63
assert s['source_union_timestamps']==s['exact_timestamp_pairs']==4717
assert s['old_only_timestamps']==s['wh1080_only_timestamps']==s['unit_interval_conflicts']==0
assert s['wh1080_outTemp_zero_rows']==s['old_weewx_outTemp_null_rows']==4717
assert s['field_concordance']['outTemp']['paired_nonnull']==0
assert s['field_concordance']['rainRate']['equal']==4717 and s['field_concordance']['pressure']['equal']==4717
assert s['field_concordance']['altimeter']['conflict']==4717
for f,stats in s['field_concordance'].items():
 for k in ['paired_nonnull','equal','conflict','null_asymmetry']:
  assert stats[k]==sum(r['fields'][f][k] for r in d['records'])
assert d['protected_period']=='2018-Q1; diagnostic only; no proposals'
assert d['database_mode']=='READ_ONLY_SELECT_ONLY' and d['writes']==0
assert len(list(csv.DictReader((R/'reports/2026-11-14-B5-2018-gap-source-concordance.csv').open())))==10
print('PASS: protected Q1 2018; 63 gaps; 4,717 exact source key matches; no proposals.')
