#!/usr/bin/env python3
"""Deterministic consistency checks for the compact rainRate ratio report."""

SCOPES = {
    "2018_Q1_INTERIM": {
        "rows_total": 18523, "rain_null": 10091, "rate_null": 10080,
        "rain_positive": 86, "rate_positive": 303, "both_positive": 86,
        "rain_pos_rate_zero": 0, "rain_zero_rate_pos": 217,
        "ratio_lt_0_5": 81, "ratio_0_5_0_9": 3, "ratio_0_9_1_1": 2,
        "ratio_1_1_2": 0, "ratio_gt_2": 0, "ratio_within_2pct": 1,
    },
    "2021_DIAGNOSTIC_ONLY": {
        "rows_total": 103464, "rain_null": 298, "rate_null": 251,
        "rain_positive": 1764, "rate_positive": 4567, "both_positive": 990,
        "rain_pos_rate_zero": 774, "rain_zero_rate_pos": 3573,
        "ratio_lt_0_5": 487, "ratio_0_5_0_9": 222, "ratio_0_9_1_1": 45,
        "ratio_1_1_2": 86, "ratio_gt_2": 150, "ratio_within_2pct": 8,
    },
}

for scope, values in SCOPES.items():
    assert sum(values[k] for k in ("ratio_lt_0_5", "ratio_0_5_0_9", "ratio_0_9_1_1", "ratio_1_1_2", "ratio_gt_2")) == values["both_positive"], scope
    assert values["ratio_within_2pct"] <= values["ratio_0_9_1_1"], scope
    assert values["both_positive"] <= values["rain_positive"]
    assert values["both_positive"] <= values["rate_positive"]

assert SCOPES["2018_Q1_INTERIM"]["rows_total"] == 18523
assert SCOPES["2021_DIAGNOSTIC_ONLY"]["rows_total"] == 103464
print("rainRate interval-ratio aggregate checks: OK (2 scopes)")
