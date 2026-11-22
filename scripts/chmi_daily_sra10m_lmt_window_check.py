#!/usr/bin/env python3
"""Test CHMI SRA10M windows using the official 07:00 local mean solar time.

Uses only cached CHMI files. The metadata says daily SRA is measured at 07:00
local mean solar time and assigned to the preceding day; it does not define how
the CSV DT field encodes that day. Candidate mapping variants are therefore
compared, not selected as an official convention.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import hashlib
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from chmi_daily_sra10m_window_check import load_10m, load_daily, summarize_window

UTC = timezone.utc
STATIONS = ("0-203-0-11777", "0-203-0-11778")


def nearest_10m(dt: datetime) -> datetime:
    seconds = round(dt.timestamp() / 600) * 600
    return datetime.fromtimestamp(seconds, UTC)


def load_longitudes(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for row in payload["stations"]:
        station = row["chmi_dataset_id"]
        if station not in STATIONS:
            continue
        match = re.match(r"\s*(-?\d+(?:\.\d+)?)", row["metadata"]["x"])
        if not match:
            raise ValueError(f"Cannot parse longitude for {station}")
        out[station] = float(match.group(1))
    if set(out) != set(STATIONS):
        raise ValueError(f"Station metadata missing: {set(STATIONS) - set(out)}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subdaily", type=Path, default=Path("data/chmi-2018"))
    parser.add_argument("--daily", type=Path, default=Path("data/chmi-rain-window/raw"))
    parser.add_argument("--station-metadata", type=Path,
                        default=Path("data/chmi-2013-context/station_metadata.json"))
    parser.add_argument("--out", type=Path, default=Path("reports/2026-11-13-chmi-sra-lmt-offset"))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    longitudes = load_longitudes(args.station_metadata)
    detail: list[dict] = []
    for station, longitude in longitudes.items():
        obs, issues = load_10m(args.subdaily, station)
        daily_rows = load_daily(args.daily / f"dly-{station}-SRA.csv", station)
        for d in daily_rows:
            dt = d["dt"]
            midnight = datetime(dt.year, dt.month, dt.day, tzinfo=UTC)
            lmt_clock_utc = timedelta(hours=7.0 - longitude / 15.0)
            # Interpretation A: DT labels assigned day; reading follows next morning.
            assigned_day_lmt = nearest_10m(midnight + timedelta(days=1) + lmt_clock_utc)
            # Interpretation B: DT labels measurement date; reading is that morning.
            measurement_day_lmt = nearest_10m(midnight + lmt_clock_utc)
            ends = {
                "dt_minus_10m": dt - timedelta(minutes=10),
                "dt": dt,
                "dt_plus_23h40m": dt + timedelta(hours=23, minutes=40),
                "dt_plus_23h50m": dt + timedelta(hours=23, minutes=50),
                "dt_plus_24h": dt + timedelta(days=1),
                "assigned_day_07_lmt_nearest_10m": assigned_day_lmt,
                "measurement_day_07_lmt_nearest_10m": measurement_day_lmt,
            }
            row = {"station": station, "dt_utc": dt.isoformat().replace("+00:00", "Z"),
                   "timefunc": d["timefunc"], "longitude_deg_e": longitude,
                   "lmt_07_utc_decimal_hour": round(7.0 - longitude / 15.0, 6),
                   "daily_qc_valid": d["qc_valid"]}
            for label, end in ends.items():
                result = summarize_window(d, obs, end)
                for key, value in result.items():
                    row[f"{label}_{key}"] = value
                row[f"{label}_end_utc"] = end.isoformat().replace("+00:00", "Z")
            detail.append(row)
        print(f"{station}: SRA10M rows={len(obs)}, loader_issues={dict(issues)}, daily_rows={len(daily_rows)}")

    detail_path = args.out.with_name(args.out.name + ".csv")
    with detail_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(detail[0]))
        writer.writeheader(); writer.writerows(detail)

    summary: list[dict] = []
    labels = ("dt_minus_10m", "dt", "dt_plus_23h40m", "dt_plus_23h50m", "dt_plus_24h",
              "assigned_day_07_lmt_nearest_10m", "measurement_day_07_lmt_nearest_10m")
    for station in longitudes:
        subset = [r for r in detail if r["station"] == station]
        for label in labels:
            paired = [r for r in subset if r["daily_qc_valid"] and
                      r[f"{label}_complete_qc_window"] and r[f"{label}_daily_mm"] is not None]
            diffs = [abs(r[f"{label}_diff_mm"]) for r in paired]
            summary.append({"station": station, "candidate": label,
                "longitude_deg_e": longitudes[station],
                "lmt_07_utc_decimal_hour": round(7-longitudes[station]/15,6),
                "qc_pairs": len(paired),
                "matches_within_0_05mm": sum(r[f"{label}_exact_to_0_1mm"] for r in paired),
                "wet_qc_rows": sum(r[f"{label}_daily_mm"] > 0 for r in paired),
                "wet_matches_within_0_05mm": sum(r[f"{label}_exact_to_0_1mm"] and r[f"{label}_daily_mm"] > 0 for r in paired),
                "mae_mm": round(sum(diffs)/len(diffs),6) if diffs else None,
                "mean_signed_difference_mm": round(sum(r[f"{label}_diff_mm"] for r in paired)/len(paired),6) if paired else None})
    summary_path = args.out.with_name(args.out.name + ".summary.csv")
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    source_paths = [args.station_metadata]
    source_paths += [args.daily / f"dly-{station}-SRA.csv" for station in STATIONS]
    source_paths += [args.subdaily / "manifest.json"]
    for station in STATIONS:
        source_paths += sorted((args.subdaily / "raw").glob(f"10m-{station}-2018*.json"))
    output_paths = [detail_path, summary_path]
    def digest(path: Path) -> dict:
        raw = path.read_bytes()
        return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    manifest = {
        "analysis": "CHMI daily SRA versus SRA10M; 07:00 local mean solar time endpoint test",
        "created_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "scope": {"year": 2018, "stations": list(STATIONS), "daily_qc": "blank FLAG and QUALITY=0",
                  "subdaily_window": "144 10-minute endpoints, all numeric, unflagged, QUALITY=0",
                  "match_tolerance_mm": 0.05},
        "station_metadata": digest(args.station_metadata),
        "source_files": [digest(p) for p in source_paths],
        "script": digest(Path(__file__).resolve()),
        "outputs": [digest(p) for p in output_paths],
    }
    manifest_path = args.out.with_name(args.out.name + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"detail={detail_path}; summary={summary_path}")
    for row in summary: print(row)


if __name__ == "__main__":
    main()
