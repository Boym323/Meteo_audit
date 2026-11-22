#!/usr/bin/env python3
"""Offline structural validation for the frozen 2017 per-gap availability report."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=json.loads((R/'data/b5_2017_per_gap_availability.json').read_text())
assert p['year']==2017 and len(p['records'])==263
assert p['database_mode']=='READ_ONLY_SELECT_ONLY'
assert p['query_execution_timestamp_utc']=='NOT_CAPTURED_BY_WEATHER_MCP'
assert p['correction_proposals']==0 and p['source_row_sum_non_additive'] is True
assert p['state_counts']=={'LEGACY_ROWS_EQUAL_COUNTS_ROW_LEVEL_MATCH_NOT_TESTED':263}
assert len({r['gap_id'] for r in p['records']})==263
for r in p['records']:
 assert 3600<=r['gap_seconds']<86400
 assert r['source_copy_identity_or_quality_proven'] is False
 assert r['per_archive']['old_weewx']['row_count']==r['per_archive']['wh1080']['row_count']>0
for a in ('reconstruction','eu','gw1000'):
 assert p['per_archive_summary'][a]['rows']==0
assert p['per_archive_summary']['old_weewx']['rows']==8359
assert p['per_archive_summary']['wh1080']['rows']==8359
assert p['per_archive_summary']['eu_old']['rows']==45
assert len(list((R/'sql/readonly/b5_2017_gap_availability').glob('*.sql')))==36
assert len(list((R/'data/b5_2017_gap_per_archive_raw_chunks').glob('*.json')))==36
with (R/'reports/2026-11-14-B5-2017-per-gap-availability.csv').open(newline='') as f:
 rows=list(csv.DictReader(f))
assert len(rows)==263
for name in ('reports/2026-11-14-B5-2017-per-gap-availability.md','reports/2026-11-14-B5-2017-per-gap-availability.csv'):
 assert (R/name).is_file()
print('PASS: 263 gaps, 36 SQL/raw query outputs, archive totals and non-claims validated offline')
