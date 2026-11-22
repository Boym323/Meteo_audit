#!/usr/bin/env python3
"""Extract small CHMI vapor-pressure/temperature context for the 2019 RH conflict.

The script uses only cached official monthly CSVs and local candidate CSV.
It never pairs hourly CHMI data to the 5-minute Loucka series; it emits exact
CHMI hourly T/E co-observations and a separate diagnostic vapor-pressure
conversion for the six Loucka source candidates.
"""
from __future__ import annotations
import argparse
import csv
import math
from pathlib import Path

STATIONS = {
    "0-203-0-11777": "Vizovice",
    "0-203-0-11778": "Kladná-Žilín",
}
TARGET_HOURS = {"2019-06-20T05:00Z", "2019-06-20T06:00Z"}
A, B = 17.625, 243.04


def rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


def es_hpa(temp_c: float) -> float:
    gamma = A * temp_c / (B + temp_c)
    return 6.112 * math.exp(gamma)


def write_csv(path: Path, data: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--cases-csv", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    hourly_e: dict[tuple[str, str], dict] = {}
    tenmin_t: dict[tuple[str, str], dict] = {}
    for sid in STATIONS:
        ep = args.data_dir / "raw" / f"1h-{sid}-E-201906.csv"
        tp = args.data_dir / "raw" / f"10m-{sid}-T-201906.csv"
        for r in rows(ep):
            dt = r["DT"]
            if dt in TARGET_HOURS:
                hourly_e[(sid, dt)] = r
        for r in rows(tp):
            dt = r["DT"]
            if dt in TARGET_HOURS:
                tenmin_t[(sid, dt)] = r

    hourly_out = []
    for sid, name in STATIONS.items():
        for dt in sorted(TARGET_HOURS):
            er, tr = hourly_e.get((sid, dt)), tenmin_t.get((sid, dt))
            if er is None or tr is None:
                raise SystemExit(f"Missing exact CHMI T/E pair for {sid} {dt}")
            if er["FLAG"] or tr["FLAG"] or float(er["QUALITY"]) != 0 or float(tr["QUALITY"]) != 0:
                raise SystemExit(f"Unexpected CHMI flag/quality for {sid} {dt}")
            t, e = float(tr["VALUE"]), float(er["VALUE"])
            es = es_hpa(t)
            hourly_out.append({
                "station_id": sid, "station": name, "dt_utc": dt,
                "temperature_10min_c": t, "temperature_flag": tr["FLAG"],
                "temperature_quality": tr["QUALITY"],
                "vapor_pressure_1hour_hpa": e, "vapor_pressure_flag": er["FLAG"],
                "vapor_pressure_quality": er["QUALITY"],
                "saturation_vapor_pressure_magnus_hpa": round(es, 4),
                "derived_relative_humidity_magnus_pct": round(100 * e / es, 2),
            })
    write_csv(args.output_dir / "chmi_hourly_vapor_pressure_context.csv", hourly_out,
              list(hourly_out[0]))

    candidates = list(rows(args.cases_csv))
    candidate_out = []
    for r in candidates:
        t = float(r["old_outTemp"])
        es = es_hpa(t)
        for source, key in (("old_weewx", "old_outHumidity"), ("weewx_WH1080", "wh_outHumidity")):
            rh = float(r[key])
            candidate_out.append({
                "target_epoch": r["target_epoch"], "target_utc": r["target_utc"],
                "source": source, "temperature_c": t, "relative_humidity_pct": rh,
                "implied_vapor_pressure_hpa": round(es * rh / 100, 4),
            })
    write_csv(args.output_dir / "loucka_conflicting_source_vapor_pressure.csv", candidate_out,
              list(candidate_out[0]))
    print(f"CHMI exact hourly T/E rows={len(hourly_out)}; Loucka source diagnostics={len(candidate_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
