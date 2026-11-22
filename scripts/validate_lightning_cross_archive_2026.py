#!/usr/bin/env python3
"""Validate bounded lightning field cross-archive counts and samples."""
import csv
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'reports'
r={x['source']:x for x in csv.DictReader((R/'2026-11-13-lightning-field-cross-archive.csv').open(newline='',encoding='utf-8'))}
assert set(r)=={'pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old','weewx_WH1080'}
a=r['pocasi-loucka.eu']; assert tuple(int(a[k]) for k in ('target_n','matched_rows','disturber_nonnull','disturber_exact_matches','noise_nonnull','noise_equals_strike'))==(47599,47599,47599,47599,179,179)
g=r['pocasi-loucka.eu_GW1000']; assert tuple(int(g[k]) for k in ('target_n','matched_rows','disturber_nonnull','noise_nonnull'))==(47599,46745,0,0)
for s in ('pocasi-loucka.eu_old','weewx_WH1080'):
 assert int(r[s]['matched_rows'])==0
samples=list(csv.DictReader((R/'2026-11-13-lightning-field-examples-2026.csv').open(newline='',encoding='utf-8')))
assert len(samples)==3
assert [int(x['dateTime']) for x in samples]==[1778525100,1778525400,1778525700]
assert all(int(x['lightning_disturber_count'])>int(x['dateTime']) for x in samples)
assert all(x['lightning_strike_count']==x['lightning_noise_count'] for x in samples)
print('PASS: four archive comparisons and three representative lightning examples')
