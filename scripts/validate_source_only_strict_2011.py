#!/usr/bin/env python3
"""Deterministic consistency checks for the strict 2011 source-only cohort."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
groups=json.loads((root/'data/source_only_2009_2020_cross_archive_grouped.json').read_text())
sel=[x for x in groups if x['utc_year']==2011 and x['interval_min']==5 and x['usUnits']==17 and x['on_5m_grid']==1 and x['both_copies']==1 and x['concordance']=='ALL_PRIMARY_EQUAL']
assert len(sel)==1 and sel[0]['timestamp_count']==1201
for field in ('old_temp_present','wh_temp_present','old_rh_present','wh_rh_present','old_rain_present','wh_rain_present','old_rainrate_present','wh_rainrate_present','old_wind_present','wh_wind_present'):
    assert sel[0][field]==1, field
e=json.loads((root/'data/source_only_strict_2011_cohort.json').read_text())
assert e['aggregate']['timestamp_count']==1201
assert e['aggregate']['outTemp_positive']==1201 and e['aggregate']['outTemp_zero']==0 and e['aggregate']['outTemp_negative']==0
assert e['aggregate']['rain_positive']==1201 and e['aggregate']['rainRate_positive']==0
assert e['restored']==0 and e['estimated']==0 and e['review_required']==1201 and e['missing']==0
assert e['aggregate']['first_epoch']==1312023900 and e['aggregate']['last_epoch']==1313531700
for f in ['reports/2026-11-13-source-only-strict-2011-cohort.md','sql/readonly/source_only_strict_2011_concordant_cohort.sql']:
    assert (root/f).is_file() and (root/f).stat().st_size>100
print('PASS: 2011 aggregate group, field availability, live evidence snapshot, disposition and reproducibility files reconcile')
