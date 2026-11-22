#!/usr/bin/env python3
"""Reconcile the 2015-2017 training and 2019-2020 transfer holdout artifacts."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def rows(name: str) -> list[dict[str, str]]:
    with (REPORTS / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


train = rows("2026-11-13-temperature-transfer-2019-2020-training.csv")
stats = rows("2026-11-13-temperature-transfer-2019-2020-sufficient-stats.csv")
summary = rows("2026-11-13-temperature-transfer-2019-2020-summary.csv")
cases = rows("2026-11-13-temperature-transfer-2019-2020-problem-cases.csv")
assert len(train) == 4 and {row["utc_quarter"] for row in train} == {"Q1", "Q2", "Q3", "Q4"}
assert sum(int(row["all_pairs"]) for row in train) == 235_135
assert [int(row["all_pairs"]) for row in train] == [38_200, 59_202, 66_971, 70_762]
assert len(stats) == 14 and len(summary) == 13 and len(cases) == 12
assert sum(int(row["all_pairs"]) for row in stats) == 192_235
assert sum(int(row["suspect_reference_zero_hot_pairs"]) for row in stats) == 959
assert sum(int(row["sensitivity_pairs"]) for row in stats) == 191_276
assert sum(int(row["all_pairs"]) for row in stats if row["utc_year"] == "2019") == 94_395
assert sum(int(row["all_pairs"]) for row in stats if row["utc_year"] == "2020") == 97_840
assert sum(int(row["all_pairs"]) for row in stats if row["temperature_group"] == "FREEZE") == 21_289
assert all(row["utc_year"] in {"2019", "2020"} for row in stats)
assert all(row["luhamet_temp_c"] == "0" and float(row["loucka_outTemp_c"]) >= 28.7 for row in cases)
assert {row["source_resolution"] for row in cases} == {"5min"}
assert {row["quality_status"] for row in cases} == {"reference_only"}
lookup = {row["scope"]: row for row in summary}
all_row = lookup["ALL_ALL"]
assert abs(float(all_row["M0_base_MAE"]) - 1.486461) < 1e-6
assert abs(float(all_row["M0_sensitivity_RMSE"]) - 2.293884) < 1e-6
assert float(all_row["M1_base_MAE"]) > float(all_row["M0_base_MAE"])
assert float(all_row["M2_base_RMSE"]) > float(all_row["M0_base_RMSE"])
print("PASS: train/test scopes, quarterly counts, conflict sensitivity, and model summaries reconcile")
