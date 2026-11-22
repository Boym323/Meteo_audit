#!/usr/bin/env python3
"""Validate 2026 soilTemp5/6 extreme-case summary from bounded selected rows."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'reports'
d=json.loads((R/'2026-11-13-soil-temperature-extremes-summary-2026.json').read_text(encoding='utf-8'))
r=list(csv.DictReader((R/'2026-11-13-soil-temperature-extremes-2026.csv').open(newline='',encoding='utf-8')))
assert len(r)==31 and d['case_rows']==31
assert d['soilTemp5_below_minus40_count']==10 and d['soilTemp6_below_minus40_count']==21
assert d['both_below_minus40_count']==0 and d['main_archive_exact_matches']==31
assert d['adjacent_300_second_case_pairs']==0 and d['case_gap_min_seconds']==7800 and d['case_gap_median_seconds']==398400 and d['case_gap_max_seconds']==3616500
assert all(x['outTemp'] and x['soilTemp1'] and x['soilTemp3'] and x['soilTemp4'] for x in r)
assert all(not x['soilTemp2'] for x in r)
print('PASS: 31 soil extreme contexts, inter-arrival stats, source-copy and context counts')
