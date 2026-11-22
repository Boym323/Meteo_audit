#!/usr/bin/env python3
"""Validate per-field availability comparison and observed 2026 onsets."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'reports'
r=list(csv.DictReader((R/'2026-11-13-secondary-sensor-availability-2025-2026.csv').open(newline='',encoding='utf-8')))
d=json.loads((R/'2026-11-13-secondary-sensor-availability-2025-2026.json').read_text(encoding='utf-8'))
assert len(r)==42 and d['variables']==42 and d['rows_2025']==102946 and d['rows_2026_partial']==86877
assert (d['lower_null_share_in_2026'],d['higher_null_share_in_2026'],d['same_null_share'])==(18,23,1)
assert len(d['newly_nonnull_2026'])==10 and d['all_null_2026']==['lightning_energy']
first={x['variable']:x['first_nonnull_utc'] for x in csv.DictReader((R/'2026-11-13-sensor-field-first-last-nonnull-2026.csv').open(newline='',encoding='utf-8'))}
assert len(first)==10
assert first['soilad1']=='2026-03-08T12:15:00.000Z'
for x in ('wh26_rssi','wh31_ch1_rssi','wh40_rssi','wh41_ch1_rssi','wh51_ch1_rssi','wh57_rssi','ws80_rssi'):
 assert first[x]=='2026-03-08T12:25:00.000Z',x
assert first['lightning_noise_count']==first['lightning_disturber_count']=='2026-05-11T18:45:00.000Z'
assert 'do not infer installation' in d['scope']
print('PASS: 42-field 2025/2026 comparison, NULL transitions and first observed epochs')
