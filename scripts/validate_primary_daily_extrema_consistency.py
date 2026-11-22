#!/usr/bin/env python3
"""Validate bounded annual/monthly daily extrema and timestamp-lookup aggregates."""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARS = {'outHumidity', 'rain', 'windSpeed', 'windGust'}
WINDOW = '2026-11-13T04:37:37Z–04:37:41Z'

def load(name: str, window: str = WINDOW):
    with (ROOT / name).open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    assert rows, f'{name}: empty result'
    assert {r['query_window_utc'] for r in rows} == {window}, f'{name}: window mismatch'
    return rows

annual = load('reports/2026-11-13-primary-daily-extrema-consistency-annual.csv')
monthly = load('reports/2026-11-13-primary-daily-extrema-consistency-2026-monthly.csv')
times = load('reports/2026-11-13-primary-daily-extrema-times-2026.csv', '2026-11-13T04:38:16Z–04:38:17Z')
assert len(annual) == 72
assert {(int(r['local_year']), r['variable']) for r in annual} == {(y, v) for y in range(2009, 2027) for v in VARS}
assert all(sum(int(r['summary_days']) for r in annual if r['variable'] == v) == 6103 for v in VARS)
# Historical exact equality includes matching NULL availability; 2021 is diagnostic only.
assert all(int(r[k]) == 0 for r in annual if int(r['local_year']) <= 2025 for k in ('min_null_mismatch', 'min_numeric_mismatch', 'max_null_mismatch', 'max_numeric_mismatch'))
assert len(monthly) == 44
assert {(r['local_month'], r['variable']) for r in monthly} == {(f'2026-{m:02d}', v) for m in range(1, 12) for v in VARS}
assert all(int(r[k]) == 0 for r in monthly for k in ('min_null_mismatch', 'max_null_mismatch'))
latest = {r['variable']: r for r in annual if int(r['local_year']) == 2026}
expected = {
    'outHumidity': (165, 163, 29, 22),
    'rain': (0, 0, 1, 0),
    'windSpeed': (158, 158, 0, 0),
    'windGust': (203, 203, 0, 0),
}
for v, want in expected.items():
    r = latest[v]
    assert int(r['summary_days']) == 316
    assert int(r['raw_extrema_null_days']) == 0
    assert int(r['min_null_mismatch']) == int(r['max_null_mismatch']) == 0
    got = tuple(int(r[k]) for k in ('min_numeric_mismatch', 'min_gt_0_1', 'max_numeric_mismatch', 'max_gt_0_1'))
    assert got == want, f'{v}: expected {want}, got {got}'
assert len(times) == 4 and {r['variable'] for r in times} == VARS
assert all(int(r['days']) == 316 for r in times)
assert {(r['variable'], int(r['mintime_absent']), int(r['maxtime_absent'])) for r in times} == {
    ('outHumidity',225,233),('rain',230,172),('windSpeed',229,0),('windGust',232,231)}
print('PASS: 72 annual, 44 monthly, and 4 timestamp groups reconcile to the documented 6,103-day scope and 2026 anomalies')
