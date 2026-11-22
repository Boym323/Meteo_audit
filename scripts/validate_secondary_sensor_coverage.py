#!/usr/bin/env python3
"""Check observed-epoch sensor coverage aggregation and protected-year exclusion."""
import csv
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=list(csv.DictReader((root/'reports/2026-11-12-monthly-sensor-null-coverage.csv').open(newline='')))
output=list(csv.DictReader((root/'reports/2026-11-13-secondary-sensor-coverage-by-observed-epoch.csv').open(newline='')))
expected={'pressure':('2009-03','2026-10',1391420,1586426),'windSpeed':('2009-03','2026-10',1560724,1586426),'radiation':('2022-08','2026-10',432798,443091),'UV':('2022-08','2026-10',432800,443091),'pm25':('2022-08','2026-10',414486,443091),'soilMoist1':('2022-08','2026-10',387955,443091),'lightning_distance':('2022-09','2026-03',1569,373272)}
assert len(output)==11
by={r['variable']:r for r in output}
assert len(by)==len(output)
for v,(first,last,available,eligible) in expected.items():
 r=by[v]
 assert (r['first_observed_utc_month'],r['last_observed_utc_month'])==(first,last)
 assert int(r['non_null_rows_excluding_2021'])==available
 assert int(r['eligible_archive_rows_excluding_2021'])==eligible
 calc=100*available/eligible
 assert abs(float(r['archive_row_availability_pct'])-calc)<0.0001
 # Reconcile exact month aggregation with 2021 excluded.
 source_rows=[x for x in source if first<=x['utc_month']<=last and x['utc_month'][:4]!='2021']
 assert sum(int(x['rows_n'])-int(x[f'{v}_null']) for x in source_rows)==available
 assert sum(int(x['rows_n']) for x in source_rows)==eligible
assert by['lightning_distance']['archive_row_availability_pct']=='0.4203'
print('PASS: 11 observed-epoch channels; counts and percentages reconcile; 2021 excluded')
