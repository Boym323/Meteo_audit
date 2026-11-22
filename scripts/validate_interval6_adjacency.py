#!/usr/bin/env python3
"""Validate compact exact predecessor/successor aggregates for interval=6 rows."""
import csv
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'reports/2026-11-12-interval6-adjacency.csv'
with P.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
assert len(rows)==18 and [int(r['utc_year']) for r in rows]==list(range(2009,2027))
expect={'interval6_rows':2090,'rows_with_prev':2090,'rows_with_next':2090,
'prev_delta_300':1703,'prev_delta_360':0,'prev_delta_matches_prev_interval':1703,
'prev_delta_matches_interval6':0,'next_delta_300':2020,'next_delta_360':0,
'next_delta_matches_interval6':0,'next_delta_matches_next_interval':2020}
for k,v in expect.items():
 got=sum(int(r[k]) for r in rows)
 assert got==v,(k,got,v)
print('interval=6 adjacency reconciled:',expect)
