#!/usr/bin/env python3
"""Validate seasonal aggregate masked-block scores and binned point quantiles."""
import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
reports = ROOT / "reports"
with (reports / "2026-11-13-temperature-interpolation-seasonal-blocks.csv").open(newline="") as f:
    metric_rows = list(csv.DictReader(f))
with (reports / "2026-11-13-temperature-interpolation-seasonal-error-histogram.csv").open(newline="") as f:
    hist_rows = list(csv.DictReader(f))
with (reports / "2026-11-13-temperature-interpolation-seasonal-point-quantiles.csv").open(newline="") as f:
    quant_rows = list(csv.DictReader(f))
assert len(metric_rows) == 24
assert len(hist_rows) == 18856
assert len(quant_rows) == 198
assert {(r["period"], int(r["block_hours"])) for r in metric_rows} == {
    (f"{y}Q{q}", h) for y in (2019, 2020) for q in range(1, 5) for h in (1, 6, 24)
}
expected = {
    1: (198336, 187971, 946, 16528),
    6: (188280, 178337, 927, 2615),
    24: (164448, 155146, 592, 571),
}
for hours, (targets, matched, flagged, blocks) in expected.items():
    rows = [r for r in metric_rows if int(r["block_hours"]) == hours]
    assert sum(int(r["masked_target_n"]) for r in rows) == targets
    assert sum(int(r["exact_reference_n"]) for r in rows) == matched
    assert sum(int(r["zero_hot_n"]) for r in rows) == flagged
    assert sum(int(r["complete_blocks"]) for r in rows) == blocks

hist = defaultdict(dict)
for r in hist_rows:
    key = (r["period"], r["block_type"], r["group"], r["method"])
    hist[key][int(r["absolute_error_decic_bucket"])] = int(r["count"])
quant_lookup = {
    (r["period"], r["block_type"], r["group"], r["method"]): r for r in quant_rows
}
metric_lookup = {(r["period"], f'{int(r["block_hours"])}h'): r for r in metric_rows}
for key, buckets in hist.items():
    n = sum(buckets.values())
    period, block, group, method = key
    mr = metric_lookup[(period, block)]
    expected_n = int(mr["exact_reference_n"])
    if group == "nonflag":
        expected_n = int(mr["nonflag_n"])
    elif group == "freeze_nonflag":
        expected_n = int(mr["freeze_nonflag_n"])
    assert n == expected_n
    row = quant_lookup[key]
    assert int(row["n"]) == n
    for p in (50, 90, 95):
        rank = math.ceil(n * p / 100)
        cumulative = 0
        for bucket, count in sorted(buckets.items()):
            cumulative += count
            if cumulative >= rank:
                midpoint = (bucket + 0.5) / 10
                assert math.isclose(float(row[f"p{p}_bin_mid_C"]), midpoint, abs_tol=1e-12)
                break
    assert math.isclose(float(row["max_bin_upper_C"]), (max(buckets) + 1) / 10, abs_tol=1e-12)

for hours, expected_mae in ((1, 0.2249609027), (6, 0.9143999010), (24, 3.0361222153)):
    rows = [r for r in metric_rows if int(r["block_hours"]) == hours]
    n = sum(int(r["exact_reference_n"]) for r in rows)
    mae = sum(int(r["exact_reference_n"]) * float(r["interpolation_paired_mae"]) for r in rows) / n
    assert abs(mae - expected_mae) < 1e-8
for hours in (1, 6):
    rows = [r for r in metric_rows if int(r["block_hours"]) == hours]
    assert len(rows) == 8
    assert all(
        float(r["interpolation_paired_mae"]) < float(r["direct_reference_mae"])
        and float(r["interpolation_paired_mae"]) < float(r["harmonic_ols_mae"])
        for r in rows
    )
daily = [r for r in metric_rows if int(r["block_hours"]) == 24]
assert len(daily) == 8
assert sum(
    float(r["interpolation_paired_mae"]) < min(float(r["direct_reference_mae"]), float(r["harmonic_ols_mae"]))
    for r in daily
) == 0
print("PASS: 8 quarters x 3 horizons; 19,714 blocks; histograms and quantiles reconcile")
