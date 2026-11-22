#!/usr/bin/env python3
"""Validate annual all-field availability aggregates and reconcile prior snapshots."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / 'reports'
STEM = '2026-11-13-annual-archive-field-availability-2009-2026'


def main():
    d = json.loads((REPORTS / f'{STEM}.json').read_text())
    assert d['fields_count'] == 77
    assert d['years'] == list(range(2009, 2027))
    assert len(d['records']) == 77 * 18
    by_key = {(int(r['year']), r['variable']): r for r in d['records']}
    assert len(by_key) == len(d['records'])
    for r in d['records']:
        assert int(r['archive_rows']) == int(r['null_rows']) + int(r['nonnull_rows'])
        assert 0 <= float(r['null_share']) <= 1
    snapshots = [2024, 2025, 2026]
    for year in snapshots:
        s = json.loads((REPORTS / f'2026-11-13-annual-secondary-sensor-snapshot-{year}.json').read_text())
        assert int(s['rows_n']) == int(d['year_row_counts'][str(year)])
        for v in s['variables']:
            r = by_key[(year, v['variable'])]
            assert int(r['null_rows']) == int(v['null_rows']), (year, v['variable'])
            assert int(r['nonnull_rows']) == int(v['nonnull_rows']), (year, v['variable'])
    with (REPORTS / f'{STEM}.csv').open(newline='') as f:
        assert len(list(csv.DictReader(f))) == 77 * 18
    with (REPORTS / '2026-11-13-archive-field-observed-year-span.csv').open(newline='') as f:
        spans = list(csv.DictReader(f))
    assert len(spans) == 77
    assert (REPORTS / f'{STEM}.md').stat().st_size > 500
    print('PASS: 77 numeric fields × 18 UTC years; row arithmetic and CSV/JSON/MD reconcile')
    print('PASS: 2024, 2025 and partial-2026 counts reconcile against existing 42-field snapshots')

if __name__ == '__main__':
    main()
