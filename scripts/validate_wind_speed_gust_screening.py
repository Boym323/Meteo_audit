#!/usr/bin/env python3
"""Validate annual/scope aggregates for the wind speed/gust triage screen."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'reports/2026-11-12-wind-speed-gust-screening.csv'
with path.open(newline='', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 3
by = {r['scope']: r for r in rows}
assert int(by['other']['rows_n']) == 1_567_903
assert int(by['other']['gust_below_speed_n']) == 226
assert int(by['other']['gap_gt_0_01']) == 29
assert int(by['other']['gap_gt_1']) == 29
assert int(by['other']['gap_gt_5']) == 21
assert int(by['other']['zero_gust_speed_gt_1']) == 6
assert int(by['other']['old_exact_rows']) == 3
assert int(by['other']['old_match_converted']) == 2
assert int(by['2018_Q1_INTERIM']['gap_gt_0_01']) == 0
assert int(by['2021_DIAGNOSTIC']['gap_gt_0_01']) == 0
assert int(by['2021_DIAGNOSTIC']['gust_below_speed_n']) == 92
annual_path = ROOT / 'reports/2026-11-12-wind-speed-gust-annual.csv'
with annual_path.open(newline='', encoding='utf-8') as f:
    annual = {r['calendar_year']: r for r in csv.DictReader(f)}
assert sum(int(r['gap_gt_0_01_kmh']) for r in annual.values()) == 29
assert int(annual['2014']['gust_below_speed_n']) == 6
assert int(annual['2016']['gust_below_speed_n']) == 18
assert int(annual['2017']['gust_below_speed_n']) == 5
print('wind speed/gust scope aggregates validated:', {'other_strict_cases':226,'meaningful_cases':29,'gap_gt_5':21,'Q1_2018_meaningful':0,'2021_meaningful':0})
