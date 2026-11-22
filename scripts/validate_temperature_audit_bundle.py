#!/usr/bin/env python3
"""Reconcile the aggregated temperature evidence cited by the synthesis reports."""
from __future__ import annotations
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def read(name: str):
    with (ROOT/'reports'/name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def close(a, b, tol=1e-5):
    assert abs(float(a)-b) <= tol, (a,b)

m1920=read('2026-11-13-temperature-transfer-2019-2020-summary.csv')
r=next(x for x in m1920 if x['scope']=='ALL_ALL')
assert int(r['pairs'])==192235 and int(r['reference_zero_hot_flagged'])==959 and int(r['sensitivity_pairs'])==191276
close(r['M0_base_MAE'],1.486461); close(r['M0_base_RMSE'],2.852031)
close(r['M1_base_MAE'],1.592545); close(r['M2_base_MAE'],1.646783)
freeze=next(x for x in m1920 if x['scope']=='ALL_FREEZE')
assert int(freeze['pairs'])==21289

m2025=read('2026-11-12-temperature-transfer-2025-holdout-summary.csv')
all25={x['model']:x for x in m2025 if x['quarter']=='ALL' and x['scope']=='ALL'}
assert set(all25)=={'M0_direct','M1_global_train_bias','M2_quarterly_train_bias'}
assert {int(x['n']) for x in all25.values()}=={98681}
close(all25['M0_direct']['mae_c'],1.0238736); close(all25['M0_direct']['rmse_c'],1.3634949)
close(all25['M1_global_train_bias']['mae_c'],1.1624932); close(all25['M2_quarterly_train_bias']['rmse_c'],1.4317067)

seasonal=read('2026-11-13-temperature-interpolation-seasonal-blocks.csv')
assert len(seasonal)==24 and {x['period'] for x in seasonal}=={f'{y}Q{q}' for y in (2019,2020) for q in range(1,5)}
expected={'1':(16528,198336,187971),'6':(2615,188280,178337),'24':(571,164448,155146)}
for h,want in expected.items():
    group=[x for x in seasonal if x['block_hours']==h]
    got=tuple(sum(int(x[k]) for x in group) for k in ('complete_blocks','masked_target_n','exact_reference_n'))
    assert got==want,(h,got,want)

extrema=read('2026-11-13-temperature-interpolation-block-extrema-summary.csv')
assert len(extrema)==3
x=next(x for x in extrema if x['horizon']=='24h')
assert int(x['clean_reference_blocks'])==494
close(x['interp_max_bias_clean'],-6.221566,1e-4); close(x['interp_max_worst_block_abs'],19.56984,1e-4)

july=read('2026-11-12-outtemp-2013-july-negative-source-cases.csv')
assert len(july)==18 and all(float(x['old_outTemp'])<0 and x['old_outTemp']==x['wh_outTemp'] for x in july)
assert sum(float(x['old_outTemp'])==-0.6 for x in july)==17
assert sum(float(x['old_outTemp'])==-9.6 for x in july)==1
plateaus=read('2026-11-12-temperature-humidity-long-plateaus-2019-2020.csv')
assert len(plateaus)==8 and {x['variable'] for x in plateaus}=={'outHumidity'} and {x['value'] for x in plateaus}=={'100'}
assert all((ROOT/'reports'/f).is_file() for f in (
 'TEMPERATURE_AUDIT.md','MODEL_VALIDATION_REPORT.md',
 '2026-11-13-production-outtemp-daily-summary-consistency-annual.csv'))
print('PASS: 2019-2020/2025 transfer metrics, 24 seasonal groups, extrema attenuation, 2013 cases and RH plateau scope reconcile')
