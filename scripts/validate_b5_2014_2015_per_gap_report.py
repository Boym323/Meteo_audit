#!/usr/bin/env python3
"""Validate B5 2014-2015 per-gap availability outputs and frozen source aggregates."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2014_2015_per_gap_availability.json').read_text())
assert len(d['records'])==66 and len({x['gap_id'] for x in d['records']})==66
assert d['database_mode']=='READ_ONLY_SELECT_ONLY' and d['correction_proposals']==0
assert d['state_counts']=={'NO_SOURCE_ROW_OBSERVED_IN_SIX_ARCHIVES':16,'LEGACY_COPIES_HAVE_ROWS_AND_EQUAL_COUNTS_ROW_LEVEL_MATCH_NOT_TESTED_HERE':50}
expected={'reconstruction':(0,0,0,0),'eu':(0,0,0,0),'gw1000':(0,0,0,0),'eu_old':(20,20,19,0),'old_weewx':(50,1844,139,120),'wh1080':(50,1844,1844,1825)}
for a,e in expected.items():
 s=d['per_archive_summary'][a]
 assert (s['gaps_with_rows'],s['rows'],s['outTemp_nonnull'],s['outTemp_zero'])==e,(a,s)
assert sum(x['already_in_ge24h_review'] for x in d['records'])==1
assert all(not x['source_copy_identity_or_quality_proven'] for x in d['records'])
with (R/'reports/2026-11-14-B5-2014-2015-per-gap-availability.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
assert len(rows)==66 and len({x['gap_id'] for x in rows})==66
for year,count in [(2014,37),(2015,29)]:assert sum(x['gap_id'].startswith(f'{year}:') for x in d['records'])==count
sqls=list((R/'sql/readonly').glob('b5_201[45]_gap_availability_*.sql'))
assert len(sqls)==12
for p in sqls:
 q=p.read_text().upper();assert 'SELECT' in q and 'READ-ONLY' in q and not any(k in q for k in ('UPDATE ','INSERT ','DELETE '))
print(json.dumps({'status':'PASS','gap_events':66,'new_2015_events':29,'2014_long_overlap':1,'no_source_rows':16,'legacy_present':50,'rows_old_and_WH_each':1844,'eu_old_rows':20,'outTemp_zero_WH1080':1825,'proposals':0}))
