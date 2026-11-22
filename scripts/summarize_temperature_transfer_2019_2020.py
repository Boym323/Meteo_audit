#!/usr/bin/env python3
"""Summarize SQL sufficient statistics for a blocked 2019-2020 holdout."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def read_csv(name: str) -> list[dict[str, str]]:
    with (REPORTS / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def number(row: dict[str, str], key: str) -> float:
    return float(row[key] or 0)


def main() -> None:
    train = read_csv("2026-11-13-temperature-transfer-2019-2020-training.csv")
    test = read_csv("2026-11-13-temperature-transfer-2019-2020-sufficient-stats.csv")
    assert len(train) == 4 and {r["utc_quarter"] for r in train} == {"Q1", "Q2", "Q3", "Q4"}
    assert sum(int(r["all_pairs"]) for r in train) == 235_135
    assert len(test) == 14
    assert sum(int(r["all_pairs"]) for r in test) == 192_235
    assert sum(int(r["suspect_reference_zero_hot_pairs"]) for r in test) == 959

    dimensions: list[tuple[str, callable]] = [
        ("ALL", lambda r: True),
        ("FREEZE", lambda r: r["temperature_group"] == "FREEZE"),
        ("NONFREEZE", lambda r: r["temperature_group"] == "NONFREEZE"),
    ]
    scopes: list[tuple[str, callable]] = []
    for year in ("ALL", "2019", "2020"):
        scopes.extend((f"{year}_{group}", lambda r, y=year, g=predicate: (y == "ALL" or r["utc_year"] == y) and g(r))
                      for group, predicate in dimensions)
    for quarter in ("Q1", "Q2", "Q3", "Q4"):
        scopes.append((f"ALL_{quarter}", lambda r, q=quarter: r["utc_quarter"] == q))

    output: list[dict[str, object]] = []
    for scope, predicate in scopes:
        selected = [r for r in test if predicate(r)]
        if not selected:
            continue
        n = sum(int(r["all_pairs"]) for r in selected)
        suspicious = sum(int(r["suspect_reference_zero_hot_pairs"]) for r in selected)
        clean = n - suspicious
        result: dict[str, object] = {"scope": scope, "pairs": n,
                                     "reference_zero_hot_flagged": suspicious,
                                     "sensitivity_pairs": clean}
        for model in ("0", "1", "2"):
            abs_sum = sum(number(r, f"abs{model}") for r in selected)
            sq_sum = sum(number(r, f"sq{model}") for r in selected)
            bias_sum = sum(number(r, f"bias{model}") for r in selected)
            result[f"M{model}_base_MAE"] = round(abs_sum / n, 6)
            result[f"M{model}_base_RMSE"] = round(math.sqrt(sq_sum / n), 6)
            result[f"M{model}_base_bias"] = round(bias_sum / n, 6)
            s_abs = sum(number(r, f"sens_abs{model}") for r in selected)
            s_sq = sum(number(r, f"sens_sq{model}") for r in selected)
            s_bias = sum(number(r, f"sens_bias{model}") for r in selected)
            result[f"M{model}_sensitivity_MAE"] = round(s_abs / clean, 6) if clean else ""
            result[f"M{model}_sensitivity_RMSE"] = round(math.sqrt(s_sq / clean), 6) if clean else ""
            result[f"M{model}_sensitivity_bias"] = round(s_bias / clean, 6) if clean else ""
        output.append(result)

    dest = REPORTS / "2026-11-13-temperature-transfer-2019-2020-summary.csv"
    fields = list(output[0])
    with dest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    print(f"Wrote {len(output)} aggregate scopes to {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
