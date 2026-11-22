#!/usr/bin/env python3
"""Validate fixed-UTC source-only aggregate against the preserved prior snapshot."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
new = json.loads((ROOT / 'data/source_only_2009_2020_cross_archive_grouped_utc.json').read_text())
old = json.loads((ROOT / 'data/source_only_2009_2020_cross_archive_grouped.json').read_text())
boundary = json.loads((ROOT / 'data/source_only_utc_window_boundary_reconciliation.json').read_text())
assert sum(int(x['timestamp_count']) for x in new) == 207182
assert len(new) == 158
assert all(2009 <= int(x['utc_year']) <= 2020 for x in new)
assert all(int(x['utc_year']) == int(x['utc_year']) for x in new)
def by_year(rows):
    c = Counter()
    for row in rows:
        c[int(row['utc_year'])] += int(row['timestamp_count'])
    return c
new_years, old_years = by_year(new), by_year(old)
assert sum(new_years.values()) == sum(old_years.values())
assert boundary['session_timezone']=='SYSTEM'
assert boundary['prior_boundaries_utc_epoch_seconds']['offset_from_fixed_utc']==-3600
assert all(v==0 for source in boundary['symmetric_difference_archive_row_counts'].values() for v in source.values())
assert boundary['source_only_timestamp_set_reconciliation'].startswith('IDENTICAL')
assert new_years == Counter({2009:3811,2010:1989,2011:5016,2012:8424,2013:2025,2014:11698,2015:48778,2016:75547,2017:39082,2018:8494,2019:818,2020:1500})
out = {'status':'PASS','records':207182,'groups':len(new),'previous_snapshot_total':sum(old_years.values()),
       'utc_year_counts':dict(sorted(new_years.items())),
       'previous_year_counts':dict(sorted(old_years.items())),
       'year_count_delta':{str(y):new_years[y]-old_years[y] for y in sorted(new_years) if new_years[y]!=old_years[y]},
       'prior_utc_window_membership':'Exact source-only timestamp set is identical: the only possible symmetric-difference bands are one hour at each boundary (old SYSTEM/CET bounds were -3600s), and raw source archives contain zero rows in all four bands.',
       'scope':'Fixed UTC epoch window [2009-01-01T00:00Z, 2021-01-01T00:00Z); row-set equality follows from verified zero raw source rows in the symmetric-difference boundary bands.'}
(ROOT/'data/source_only_utc_grouping_validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':'PASS','records':207182,'groups':len(new),'year_count_delta':out['year_count_delta']}))
