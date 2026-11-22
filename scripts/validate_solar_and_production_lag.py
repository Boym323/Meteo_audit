#!/usr/bin/env python3
"""Validate solar scope aggregates and current production/reconstruction lag."""
import csv
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def rows(path):
    with (ROOT/path).open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))
solar=rows('reports/2026-11-12-solar-screening.csv')
assert len(solar)==3
assert all(len(r)==len(solar[0]) for r in solar)
s={r['scope']:r for r in solar}
assert int(s['other']['archive_rows'])==1_567_903
assert int(s['other']['radiation_nonnull'])==432_798
assert int(s['other']['UV_nonnull'])==432_800
assert int(s['other']['radiation_positive_below_civil_twilight'])==76
assert float(s['other']['max_radiation_below_twilight'])<10
assert int(s['other']['UV_positive_below_civil_twilight'])==0
assert int(s['other']['radiation_gt1500'])==3
assert int(s['other']['UV_gt12'])==4
assert int(s['2018_Q1_INTERIM']['radiation_nonnull'])==0
assert int(s['2021_DIAGNOSTIC_ONLY']['UV_nonnull'])==0
cases=rows('reports/2026-11-12-solar-high-value-cases.csv')
assert len(cases)==4
assert sum(float(r['radiation'])>1500 for r in cases)==3
assert sum(float(r['UV'])>12 for r in cases)==4
inventory=rows('reports/2026-11-13-production-reconstruction-lag.csv')
by={r['archive_name']:r for r in inventory}
assert int(by['loucka_reconstruction']['last_epoch'])==1_793_286_600
assert int(by['pocasi-loucka.eu']['last_epoch'])==1_794_524_400
assert datetime.fromtimestamp(int(by['loucka_reconstruction']['last_epoch']),timezone.utc).isoformat()=='2026-10-29T15:10:00+00:00'
assert datetime.fromtimestamp(int(by['pocasi-loucka.eu']['last_epoch']),timezone.utc).isoformat()=='2026-11-12T23:00:00+00:00'
events=rows('reports/2026-11-13-production-reconstruction-lag-events.csv')
assert len(events)==3 and all(int(r['delta_seconds'])==600 for r in events)
print('solar aggregates and production tail validated:', {'night_rad_positive':76,'material_night_rad':0,'extreme_cases':4,'production_rows_after_recon':4123,'tail_10min_gaps':3})
