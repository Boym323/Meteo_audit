#!/usr/bin/env python3
"""Validate vapor-pressure RH holdout aggregates and physical-range flags."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "reports/2026-11-13-rh-vapor-pressure-transfer-holdout.csv"
REPORT = ROOT / "reports/2026-11-13-rh-vapor-pressure-transfer-holdout.md"


def main() -> None:
    with CSV.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    def row(method: str, split: str = "test_2017") -> dict[str, str]:
        return next(r for r in rows if r["method"] == method and r["split"] == split)
    water = row("same_vapor_pressure_water_phase")
    cold_water = row("both_station_t_below_0C_water_phase", "test_2017_cold")
    cold_ice = row("both_station_t_below_0C_ice_phase", "test_2017_cold")
    assert int(water["n"]) == 51462 and int(water["out_of_range_predictions"]) == 906
    assert abs(float(water["mae_pp"]) - 47.2975) < 1e-4
    assert abs(float(water["rmse_pp"]) - 47.8229) < 1e-4
    assert int(cold_water["n"]) == int(cold_ice["n"]) == 3629
    assert int(cold_ice["out_of_range_predictions"]) == 134
    assert abs(float(cold_ice["mae_pp"]) - 45.5707) < 1e-4
    report = REPORT.read_text(encoding="utf-8")
    for term in ("47,2975", "906 predikcí", "3 629", "ER-26", "WMO Guide"):
        assert term in report, term
    print("RH vapor-pressure transfer holdout: OK (51,462 test pairs; 3,629 cold pairs)")


if __name__ == "__main__":
    main()
