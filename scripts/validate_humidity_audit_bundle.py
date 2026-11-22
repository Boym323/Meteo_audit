#!/usr/bin/env python3
"""Reconcile the saved aggregate evidence cited by HUMIDITY_AUDIT."""
from __future__ import annotations
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(name):
    with (ROOT/'reports'/name).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def eqclose(a,b,tol=1e-4): assert abs(float(a)-b)<=tol,(a,b)

conf=read('2026-11-12-rh-source-conflict-problem-cases.csv')
assert len(conf)==6 and all(int(x['old_interval'])==int(x['wh_interval'])==5 for x in conf)
assert all(x['old_outTemp']==x['wh_outTemp'] for x in conf)
assert min(float(x['abs_rh_difference']) for x in conf)>39 and max(float(x['abs_rh_difference']) for x in conf)<56
availability=read('2026-11-13-rh-luhamet-exact-source-availability-2015-2017.csv')
assert len(availability)==3
assert sum(int(x['archive_rows']) for x in availability)==265994
assert sum(int(x['target_rh_null']) for x in availability)==40802
assert sum(int(x['null_target_valid_exact_reference_no_rh_history']) for x in availability)==38582
assert all(x['reference_quality_status']=='reference_only' and x['source_resolution']=='5min' for x in availability)

hold=read('2026-11-13-rh-luhamet-blocked-transfer-holdout.csv')
train=next(x for x in hold if x['split']=='train_2015_2016')
test={x['model']:x for x in hold if x['split']=='test_2017' and x['season']=='all'}
assert int(train['n'])==137481 and int(test['direct']['n'])==51493
assert set(test)=={'direct','global_offset','quarter_offset'}
eqclose(test['direct']['mae_pp'],46.1789);eqclose(test['global_offset']['mae_pp'],13.1442);eqclose(test['quarter_offset']['rmse_pp'],14.9050)
vapor=read('2026-11-13-rh-vapor-pressure-transfer-holdout.csv')
vp={x['method']:x for x in vapor if x['split']=='test_2017'}
assert {int(x['n']) for x in vp.values()}=={51462}
eqclose(vp['same_vapor_pressure_water_phase']['mae_pp'],47.2975)
assert int(vp['same_vapor_pressure_water_phase']['out_of_range_predictions'])==906

cascade=read('2026-11-13-derived-rh-cascade-all-history.csv')
assert {x['change_type']:int(x['target_count']) for x in cascade}=={'changed_nonnull':7586,'cleared_to_null':288,'filled_from_null':12838}
assert all(int(x['current_matches_latest_new'])==int(x['target_count']) for x in cascade)
cleared=next(x for x in cascade if x['change_type']=='cleared_to_null')
filled=next(x for x in cascade if x['change_type']=='filled_from_null')
assert all(int(cleared[k])==288 for k in ('dewpoint_present','heatindex_present','humidex_present','cloudbase_present','outHumAbs_present'))
assert all(int(filled[k])==11 for k in ('dewpoint_present','heatindex_present','humidex_present','cloudbase_present','outHumAbs_present'))
dp=read('2026-11-13-derived-dewpoint-rh-change-followup.csv')
assert len(dp)==3 and all(int(x['with_dewpoint_history'])==0 for x in dp)
assert sum(int(x['compared_rows']) for x in dp)==7514
history=read('2026-11-12-humidity-202204-decision-history-reconciliation.csv')
assert sum(int(x['decision_rows']) for x in history)==3734
assert sum(int(x['latest_applied_event']) for x in history)==3578
plateau=read('2026-11-12-temperature-humidity-long-plateaus-2019-2020.csv')
context=read('2026-11-12-temperature-humidity-long-plateaus-2019-2020-reference-context.csv')
assert len(plateau)==len(context)==8 and {x['variable'] for x in plateau}=={'outHumidity'}
assert all(int(x['exact_luhamet_pairs'])==int(x['local_rows']) for x in context)
assert all((ROOT/'reports'/f).is_file() for f in ('HUMIDITY_AUDIT.md','MODEL_VALIDATION_REPORT.md'))
print('PASS: source conflicts, 2015-2017 reference availability/holdouts, derived RH history and long plateau aggregates reconcile')
