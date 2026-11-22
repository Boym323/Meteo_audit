#!/usr/bin/env python3
"""Validate the bounded 2014 B5 six-archive availability overlay."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_2014_gap_per_archive_availability.json').read_text())
assert d['database_mode']=='READ_ONLY_SELECT_ONLY' and d['correction_proposals']==0
assert len(d['records'])==37 and d['new_subhour_or_1h_24h_scope_count']==36
assert d['state_counts']=={'NO_SOURCE_ROW_OBSERVED_IN_SIX_ARCHIVES':16,'LEGACY_COPIES_HAVE_ROWS_AND_EQUAL_COUNTS_ROW_LEVEL_MATCH_NOT_TESTED_HERE':21}
expected={'reconstruction':(0,0,0),'eu':(0,0,0),'gw1000':(0,0,0),'eu_old':(12,12,11),'old_weewx':(21,794,131),'wh1080':(21,794,794)}
for a,(gaps,rows,temp) in expected.items():
 s=d['per_archive_summary'][a]
 assert (s['gaps_with_rows'],s['rows'],s['outTemp_nonnull'])==(gaps,rows,temp),(a,s)
assert d['per_archive_summary']['old_weewx']['outTemp_zero']==120
assert d['per_archive_summary']['wh1080']['outTemp_zero']==783
assert sum(r['already_in_ge24h_review'] for r in d['records'])==1
assert all(r['source_copy_identity_or_quality_proven'] is False for r in d['records'])
for r in d['records']:
 assert all(r['per_archive'][a]['row_count']>=0 for a in expected)
 assert r['gap_id'].startswith('2014:')
with (R/'reports/2026-11-14-B5-2014-per-gap-source-availability.csv').open(newline='',encoding='utf-8') as f:
 rows=list(csv.DictReader(f))
assert len(rows)==37 and len({r['gap_id'] for r in rows})==37
for p in (R/'sql/readonly').glob('b5_2014_gap_availability_*.sql'):
 sql=p.read_text();assert 'READ-ONLY' in sql and 'SELECT' in sql.upper() and 'UPDATE ' not in sql.upper() and 'INSERT ' not in sql.upper() and 'DELETE ' not in sql.upper()
assert len(list((R/'sql/readonly').glob('b5_2014_gap_availability_*.sql')))==6
print(json.dumps({'status':'PASS','gaps':37,'under_24h':36,'no_rows_all_archives':16,'legacy_rows_present':21,'eu_old_rows':12,'legacy_source_rows_each':794,'outTemp_zeros_old_weewx':120,'outTemp_zeros_WH1080':783,'proposals':0,'database_access':'NONE_DURING_VALIDATION'}))
