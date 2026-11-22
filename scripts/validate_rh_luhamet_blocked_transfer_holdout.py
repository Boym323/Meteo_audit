#!/usr/bin/env python3
"""Check published aggregate statistics for the RH blocked transfer holdout."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "reports/2026-11-13-rh-luhamet-blocked-transfer-holdout.csv"
REPORT = ROOT / "reports/2026-11-13-rh-luhamet-blocked-transfer-holdout.md"


def main() -> None:
    with CSV.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    train = next(r for r in rows if r["split"] == "train_2015_2016")
    global_fit = next(r for r in rows if r["model"] == "global_offset")
    qrows = [r for r in rows if r["model"] == "quarter_offset" and r["season"] != "all"]
    qtotal = next(r for r in rows if r["model"] == "quarter_offset" and r["season"] == "all")
    assert int(train["n"]) == 137481
    assert abs(float(train["train_bias_pp"]) + 33.2673) < 1e-4
    assert int(global_fit["n"]) == 51493
    assert abs(float(global_fit["mae_pp"]) - 13.1442) < 1e-4
    assert abs(float(global_fit["rmse_pp"]) - 15.0752) < 1e-4
    assert sum(int(r["n"]) for r in qrows) == 51493
    assert abs(float(qtotal["mae_pp"]) - 13.0966) < 1e-4
    assert abs(float(qtotal["rmse_pp"]) - 14.9050) < 1e-4
    assert len(qrows) == 4 and all(int(r["out_of_range_predictions"]) == 0 for r in qrows)
    report = REPORT.read_text(encoding="utf-8")
    for text in ("137 481", "51 493", "46,1789", "13,1442", "ER-26"):
        assert text in report, text
    print("RH blocked transfer holdout: OK (137,481 train / 51,493 test exact pairs)")


if __name__ == "__main__":
    main()
