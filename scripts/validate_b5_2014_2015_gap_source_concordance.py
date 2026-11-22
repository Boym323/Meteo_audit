#!/usr/bin/env python3
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2014_2015_gap_source_concordance.json').read_text());s=json.loads((R/'data/b5_2014_2015_gap_source_concordance_summary.json').read_text())
assert len(d['records'])==65 and len({x['gap_no'] for x in d['records']})==65
assert s['by_year']['2014']['gap_events']==36 and s['by_year']['2014']['source_union_timestamps']==794
assert s['by_year']['2015']['gap_events']==29 and s['by_year']['2015']['source_union_timestamps']==1050
assert s['combined']['source_union_timestamps']==s['combined']['paired_timestamps']==1844
assert s['combined']['old_only']==s['combined']['wh1080_only']==s['combined']['unit_interval_conflicts']==0
assert s['combined']['fields']['altimeter']['conflict']==1704
for y,expected in [(2014,(36,794)),(2015,(29,1050))]:
 rows=[x for x in d['records'] if x['year_utc']==y]
 assert (len(rows),sum(x['source_union_timestamps'] for x in rows))==expected
 for f,stats in s['by_year'][str(y)]['fields'].items():
  for k in ['paired_nonnull','equal','conflict','null_asymmetry']:
   assert stats[k]==sum(x['fields'][f][k] for x in rows)
assert len(list(csv.DictReader((R/'reports/2026-11-14-B5-2014-2015-gap-source-concordance.csv').open())))==20
assert d['database_mode']=='READ_ONLY_SELECT_ONLY' and d['writes']==0
print('PASS: 65 gaps; 1,844 exact source timestamp pairs; 2014/2015 partitions and ten-field aggregates reconcile; no proposal.')
