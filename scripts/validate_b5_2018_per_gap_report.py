#!/usr/bin/env python3
"""Offline structural validation of 2018 per-gap availability outputs."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=json.loads((R/'data/b5_2018_per_gap_availability.json').read_text())
assert len(p['records'])==63 and len({r['gap_id'] for r in p['records']})==63
assert p['database_mode']=='READ_ONLY_SELECT_ONLY' and p['query_execution_timestamp_utc']=='NOT_CAPTURED_BY_WEATHER_MCP'
assert p['correction_proposals']==0 and p['source_row_sum_non_additive'] is True
assert p['state_counts']=={'LEGACY_ROWS_EQUAL_COUNTS_ROW_LEVEL_MATCH_NOT_TESTED':63}
assert sum(r['protected_q1_2018'] for r in p['records'])==p['protected_q1_gap_count']
for r in p['records']:
 assert 3600<=r['gap_seconds']<86400 and r['source_copy_identity_or_quality_proven'] is False
 assert r['per_archive']['old_weewx']['row_count']==r['per_archive']['wh1080']['row_count']>0
assert p['protected_q1_gap_count']+p['post_q1_gap_count']==63
for a in ('reconstruction','eu','gw1000','eu_old'):
 assert p['per_archive_summary'][a]['rows']==0
for a in ('old_weewx','wh1080'):
 assert p['per_archive_summary'][a]['rows']==4717 and p['per_archive_summary'][a]['gaps_with_rows']==63
assert p['per_archive_summary']['old_weewx']['outTemp_nonnull']==0
assert p['per_archive_summary']['wh1080']['outTemp_zero']==4717
assert len(list((R/'sql/readonly/b5_2018_gap_availability').glob('*.sql')))==12
assert len(list((R/'data/b5_2018_gap_per_archive_raw_chunks').glob('*.json')))==12
with (R/'reports/2026-11-14-B5-2018-per-gap-availability.csv').open(newline='') as f: assert len(list(csv.DictReader(f)))==63
print('PASS: 63 gap events, 12 READ-ONLY query artifacts, protected-quarter flag and source totals validated offline')
