#!/usr/bin/env python3
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/source_only_outtemp_zero_run_screen_2016_2017.json').read_text())
y={x['utc_year']:x for x in d['years']}
assert y[2016]['zero_run_episodes']==665 and y[2016]['longest_zero_run_rows']==5343
assert y[2016]['strict_source_only_zero_rows_in_multirow_runs']==5618 and y[2016]['strict_candidate_count']==5740
assert y[2017]['zero_run_episodes']==1203 and y[2017]['longest_zero_run_rows']==4810
assert y[2017]['strict_source_only_zero_rows_in_multirow_runs']==24154 and y[2017]['strict_candidate_count']==24531
assert 'do not prove' in d['interpretation']
print('PASS: 1,868 multirow zero episodes; max runs 5,343 (2016) and 4,810 (2017); overlap is review evidence only.')
