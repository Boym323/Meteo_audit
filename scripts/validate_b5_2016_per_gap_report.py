#!/usr/bin/env python3
"""Validate 2016 B5 per-gap archive-availability artifacts."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2016_per_gap_availability.json').read_text())
assert len(d['records'])==135 and len({x['gap_id'] for x in d['records']})==135
assert d['database_mode']=='READ_ONLY_SELECT_ONLY' and d['correction_proposals']==0
assert d['state_counts']=={'LEGACY_ROWS_EQUAL_COUNTS_ROW_LEVEL_MATCH_NOT_TESTED':135}
expected={'reconstruction':(0,0,0,0),'eu':(0,0,0,0),'gw1000':(0,0,0,0),'eu_old':(67,72,66,0),'old_weewx':(135,5381,70,2),'wh1080':(135,5381,5381,5313)}
for a,e in expected.items():
 s=d['per_archive_summary'][a]
 assert (s['gaps_with_rows'],s['rows'],s['outTemp_nonnull'],s['outTemp_zero'])==e,(a,s)
assert all(not r['source_copy_identity_or_quality_proven'] for r in d['records'])
with (R/'reports/2026-11-14-B5-2016-per-gap-availability.csv').open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
assert len(rows)==135 and len({x['gap_id'] for x in rows})==135
sqls=list((R/'sql/readonly/b5_2016_gap_availability').glob('*.sql'))
assert len(sqls)==18
for p in sqls:
 s=p.read_text().upper();assert 'READ-ONLY' in s and 'SELECT' in s and not any(x in s for x in ('UPDATE ','INSERT ','DELETE '))
raws=list((R/'data/b5_2016_gap_per_archive_raw_chunks').glob('*.json'))
assert len(raws)==18
print(json.dumps({'status':'PASS','gap_events':135,'no_source_rows':0,'legacy_rows_equal_counts':135,'source_rows_old_and_WH_each':5381,'WH1080_outTemp_zero':5313,'eu_old_rows':72,'proposals':0}))
