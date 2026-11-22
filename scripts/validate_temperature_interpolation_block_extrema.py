#!/usr/bin/env python3
"""Validate block-extrema aggregates against seasonal masked-block inventory."""
import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
raw_path = ROOT / "reports/2026-11-13-temperature-interpolation-block-extrema.csv"
summary_path = ROOT / "reports/2026-11-13-temperature-interpolation-block-extrema-summary.csv"
seasonal_path = ROOT / "reports/2026-11-13-temperature-interpolation-seasonal-blocks.csv"

def rows(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))

raw = rows(raw_path)
summary = rows(summary_path)
seasonal = rows(seasonal_path)
assert len(raw) == 24, f"expected 24 quarter/horizon rows, got {len(raw)}"
assert len({(r['period'], r['block_type']) for r in raw}) == 24, "duplicate quarter/horizon key"
assert len(summary) == 3 and {r['horizon'] for r in summary} == {'1h','6h','24h'}
expected = {'1h': (16528,15509,3600), '6h': (2615,2404,21600), '24h': (571,494,86400)}
for horizon, (n, clean, block_seconds) in expected.items():
    group = [r for r in raw if r['block_type'] == horizon]
    assert len(group) == 8, f"{horizon}: expected 8 quarters"
    assert sum(int(r['complete_blocks']) for r in group) == n
    assert sum(int(r['clean_reference_blocks']) for r in group) == clean
    assert all(int(r['clean_reference_blocks']) <= int(r['complete_blocks']) for r in group)
    assert all(int(r['masked_targets']) == int(r['complete_blocks']) * block_seconds // 300 for r in group)
    s = next(r for r in summary if r['horizon'] == horizon)
    assert int(s['complete_blocks']) == n and int(s['clean_reference_blocks']) == clean
    for e in ('max','min'):
        for sample in ('all','clean'):
            suffix = 'all' if sample == 'all' else 'clean'
            denom = n if sample == 'all' else clean
            mae = sum(float(r[f'interp_{e}_abs_{suffix}']) for r in group) / denom
            rmse = math.sqrt(sum(float(r[f'interp_{e}_sq_{suffix}']) for r in group) / denom)
            bias = sum(float(r[f'interp_{e}_bias_{suffix}']) for r in group) / denom
            for col, value in ((f'interp_{e}_mae_{sample}',mae),(f'interp_{e}_rmse_{sample}',rmse),(f'interp_{e}_bias_{sample}',bias)):
                assert abs(float(s[col])-value) < 1e-9, f"{horizon} {col} does not reconcile"
# The base seasonal score inventory is the authoritative block count.
for h, expected_count in (('1h',16528),('6h',2615),('24h',571)):
    observed = sum(int(r['complete_blocks']) for r in seasonal if int(r['block_hours']) == int(h[:-1]))
    assert observed == expected_count, f"seasonal score count mismatch for {h}: {observed}"
# The observed interpolation signature is attenuation of extrema, increasingly severe with duration.
for h in ('1h','6h','24h'):
    s = next(r for r in summary if r['horizon'] == h)
    assert float(s['interp_max_bias_clean']) < 0, f"expected negative max bias for {h}"
    assert float(s['interp_min_bias_clean']) > 0, f"expected positive min bias for {h}"
assert float(next(r for r in summary if r['horizon']=='24h')['interp_max_mae_clean']) > 6
print('PASS: 24 quarter/horizon rows reconcile with 19,714 seasonal blocks; extrema attenuation reproduced')
