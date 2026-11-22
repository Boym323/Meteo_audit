#!/usr/bin/env python3
"""Deterministic local validation for corrected UTC quarter bins and 2018 off-grid screen."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT / name).read_text())

quarter = load('data/source_only_year_quarter_interval_utc.json')
annual = load('data/source_only_2009_2020_cross_archive_grouped_utc.json')
screen = load('data/source_only_2018_q2_q4_offgrid_row_screen.json')
summary = load('data/source_only_2018_q2_q4_offgrid_summary.json')
interval6 = load('data/source_only_2018_q2_q4_interval6_probe.json')
history = load('data/source_only_2018_q2_q4_nearest_target_history.json')
sql = (ROOT / 'sql/readonly/source_only_year_quarter_interval_utc.sql').read_text().upper()
sql_code = '\n'.join(line.split('--', 1)[0] for line in sql.splitlines())
assert len(quarter['groups']) == 65
assert sum(x['timestamps'] for x in quarter['groups']) == 207182
assert quarter['scope']['source_only_union_unique'] == 207182
assert 'FROM_UNIXTIME(' not in sql_code and 'UNIX_TIMESTAMP(' not in sql_code
assert "'2018-Q1'" in sql
q = {}
for row in quarter['groups']:
    q[row['utc_year_quarter']] = q.get(row['utc_year_quarter'], 0) + row['timestamps']
annual_sum = {}
for row in annual:
    year = str(row['utc_year'])
    annual_sum[year] = annual_sum.get(year, 0) + row['timestamp_count']
quarter_sum = {}
for key, n in q.items():
    year = key[:4]
    quarter_sum[year] = quarter_sum.get(year, 0) + n
assert annual_sum == quarter_sum and len(annual_sum) == 12
assert q['2018-Q1'] == 8072 and q['2018-Q2'] == 212 and q['2018-Q3'] == 17 and q['2018-Q4'] == 193
rows = screen['rows']
assert len(rows) == screen['summary']['row_count'] == 421
assert screen['summary']['nearest_target_present'] == 421
assert screen['summary']['distinct_nearest_slots'] == 421
assert screen['summary']['third_archive_present'] == 421
assert sum(summary['utc_quarter_counts'].values()) == 421
assert interval6['dateTime'] == 1534221780 and interval6['nearest_target']['dateTime'] == 1534221900
assert interval6['disposition'] == 'REVIEW_REQUIRED_TIME_SHIFT_OR_DUPLICATE'
assert history['event_rows'] == len(history['events']) == 17
assert all(e['variable'] == 'rainRate' and e['state'] == 'applied' for e in history['events'])
assert all(e['target_time'] == e['source_time'] for e in history['events'])
result = {
    'status':'PASS', 'quarter_groups':65, 'source_only_unique':207182,
    'annual_reconciliations':12, 'annual_differences':0,
    'utc_2018_quarters':{k:v for k,v in q.items() if k.startswith('2018-')},
    'offgrid_interval5_rows':421, 'interval6_rows':1,
    'nearest_target_collisions':0, 'nearest_target_rainrate_history_events':17,
    'disposition':'422 REVIEW_REQUIRED_OFFGRID_TIME_SHIFT_OR_DUPLICATE; no corrections generated',
    'database_writes':0, 'protected_q1_proposals':0, 'year_2021_included':False
}
(ROOT/'data/source_only_2018_utc_review_validation.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
