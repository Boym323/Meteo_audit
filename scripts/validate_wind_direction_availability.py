#!/usr/bin/env python3
"""Validate yearly, monthly, speed-band and source-group wind direction aggregates."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name):
    with (ROOT/name).open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))
years=read('reports/2026-11-13-wind-direction-annual.csv')
assert len(years)==18
assert sum(int(r['archive_rows']) for r in years)==1_689_890
assert sum(int(r['positive_speed_missing_dir']) for r in years)==77_988
by_year={r['utc_year']:r for r in years}
assert int(by_year['2020']['positive_speed_missing_dir'])==23_439
assert int(by_year['2021_DIAGNOSTIC_ONLY']['positive_speed_missing_dir'])==44_129
assert int(by_year['2022']['positive_speed_missing_dir'])==3_529
assert int(by_year['2023']['positive_speed_missing_dir'])==0
monthly=read('reports/2026-11-13-wind-direction-monthly-cases.csv')
assert len(monthly)==14
assert sum(int(r['positive_speed_missing_dir']) for r in monthly if r['utc_month'].startswith('2020'))==23_439
assert sum(int(r['positive_speed_missing_dir']) for r in monthly if r['utc_month'].startswith('2021'))==44_129
assert sum(int(r['positive_speed_missing_dir']) for r in monthly if r['utc_month'].startswith('2022'))==3_529
bands=read('reports/2026-11-13-wind-direction-speed-bands.csv')
assert len(bands)==18
other=[r for r in bands if r['scope']=='other']
assert sum(int(r['windDir_missing']) for r in other if r['speed_band_kmh']!='zero')==33_859
assert int(next(r for r in other if r['speed_band_kmh']=='zero')['windDir_missing'])==106_576
q1=[r for r in bands if r['scope']=='2018_Q1_INTERIM']
assert sum(int(r['windDir_missing']) for r in q1 if r['speed_band_kmh']!='zero')==0
recovery=read('reports/2026-11-13-wind-direction-recovery-summary.csv')
assert len(recovery)==4
rr={r['period']:r for r in recovery}
assert int(rr['2009_2013']['both_legacy_dirs_valid_equal'])==6_652
assert int(rr['2009_2013']['both_legacy_null'])==228
assert int(rr['2014_2019']['old_valid_wh_invalid'])==11
assert int(rr['2020_2022']['positive_speed_missing_direction'])==71_097
assert int(rr['2020_2022']['old_null_wh_valid'])==7
assert int(rr['2020_2022']['both_legacy_null'])==71_089
assert sum(int(r['positive_speed_missing_direction']) for r in recovery)==77_988
print('wind direction aggregates validated:', {'positive_speed_missing':77_988,'early_dual_source_equal':6_652,'2020_22_unavailable':71_097,'diagnostic_2021':44_129})
