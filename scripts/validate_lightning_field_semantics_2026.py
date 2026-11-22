#!/usr/bin/env python3
"""Validate the bounded aggregate evidence for lightning field semantics."""
import csv
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'reports/2026-11-13-lightning-field-semantics-2026.csv'
r=next(csv.DictReader(p.open(newline='',encoding='utf-8')))
assert r['snapshot_year']=='2026' and int(r['rows_n'])==86877
assert int(r['disturber_nonnull'])==47599
assert int(r['disturber_within_2026_epoch_range'])==47599
assert int(r['disturber_equals_target_epoch'])==0
assert int(r['disturber_minus_target_min_seconds'])==-3271920
assert int(r['disturber_minus_target_max_seconds'])==3540
assert int(r['disturber_equals_strike'])==0 and int(r['disturber_distinct_values'])==250
assert int(r['noise_nonnull'])==179 and int(r['noise_equals_strike'])==179
print('PASS: 2026 lightning semantic aggregate (all field counts reconciled)')
