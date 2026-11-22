#!/usr/bin/env python3
"""Empirical comparison of CHMI daily SRA and 10-minute SRA10M, without DB access.

Tests two plausible 24-hour windows ending at the daily CSV DT and DT+24h.
This is a consistency screen only; it cannot establish official DT/TIMEFUNC
semantics or be carried back to years without overlapping subdaily data.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

STATIONS = ("0-203-0-11777", "0-203-0-11778")
UTC = timezone.utc


def parse_stamp(text: str) -> datetime:
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
        raise ValueError(f"Expected UTC timestamp: {text}")
    return dt.astimezone(UTC)


def load_10m(root: Path, station: str) -> tuple[dict[int, tuple[float | None, str, float | None]], Counter]:
    rows: dict[int, tuple[float | None, str, float | None]] = {}
    issues: Counter = Counter()
    for month in range(1, 13):
        name = f"10m-{station}-2018{month:02d}.json"
        path = root / "raw" / name
        payload = json.loads(path.read_text(encoding="utf-8"))
        values = payload["data"]["data"]["values"]
        days = calendar.monthrange(2018, month)[1]
        seen = 0
        for row in values:
            if len(row) < 6 or row[0] != station or row[1] != "SRA10M":
                continue
            dt = parse_stamp(row[2])
            if (dt.year, dt.month) != (2018, month) or dt.second or dt.microsecond or dt.minute % 10:
                raise ValueError(f"Unexpected SRA10M timestamp: {row[2]}")
            epoch = int(dt.timestamp())
            if epoch in rows:
                raise ValueError(f"Duplicate SRA10M epoch {epoch} for {station}")
            value = row[3] if isinstance(row[3], (int, float)) and math.isfinite(row[3]) else None
            flag = row[4] or ""
            quality = row[5] if isinstance(row[5], (int, float)) else None
            rows[epoch] = (value, flag, quality)
            seen += 1
            if value is None:
                issues["missing_or_non_numeric"] += 1
            if flag or quality != 0:
                issues["flag_or_nonzero_quality"] += 1
        expected = days * 144
        if seen != expected:
            issues[f"month_{month:02d}_rows_{seen}_expected_{expected}"] += 1
    return rows, issues


def load_daily(path: Path, station: str) -> list[dict]:
    out = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        needed = {"STATION", "ELEMENT", "TIMEFUNC", "DT", "VALUE", "FLAG", "QUALITY"}
        if not needed.issubset(reader.fieldnames or []):
            raise ValueError(f"Unexpected daily SRA header in {path}")
        for row in reader:
            if row["STATION"] != station or row["ELEMENT"] != "SRA":
                continue
            dt = parse_stamp(row["DT"])
            if dt.year != 2018:
                continue
            value = None
            try:
                parsed = float(row["VALUE"])
                value = parsed if math.isfinite(parsed) else None
            except (TypeError, ValueError):
                pass
            out.append({"station": station, "dt": dt, "timefunc": row["TIMEFUNC"],
                        "value": value, "flag": row["FLAG"] or "", "quality": row["QUALITY"] or "",
                        "qc_valid": not (row["FLAG"] or "") and row["QUALITY"].strip() == "0.0"})
    return out


def summarize_window(daily: dict, observations: dict, end: datetime) -> dict:
    # CHMI timestamps are expected every 10 minutes. Candidate is 144 readings
    # ending at `end`, with endpoint included: (end-24h, end].
    end_epoch = int(end.timestamp())
    epochs = list(range(end_epoch - 23 * 3600 - 50 * 60, end_epoch + 1, 600))
    if len(epochs) != 144:
        raise AssertionError("Window must contain 144 ten-minute endpoints")
    vals = [observations.get(t) for t in epochs]
    complete = all(v is not None and v[0] is not None and not v[1] and v[2] == 0 for v in vals)
    total = sum(v[0] for v in vals) if complete else None
    diff = (total - daily["value"]) if total is not None and daily["value"] is not None else None
    return {"complete_qc_window": complete, "n_bins": len(vals), "sum_mm": total,
            "daily_mm": daily["value"], "diff_mm": diff,
            "exact_to_0_1mm": diff is not None and abs(diff) < 0.051,
            "daily_flag": daily["flag"], "daily_quality": daily["quality"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subdaily", type=Path, default=Path("data/chmi-2018"))
    parser.add_argument("--daily", type=Path, default=Path("data/chmi-rain-window/raw"))
    parser.add_argument("--out", type=Path, default=Path("reports/2026-11-13-chmi-sra-window-empirical"))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    detail_path = args.out.with_name(args.out.name + ".csv")
    summary_path = args.out.with_name(args.out.name + ".summary.csv")
    detail: list[dict] = []
    for station in STATIONS:
        obs, issues = load_10m(args.subdaily, station)
        daily_rows = load_daily(args.daily / f"dly-{station}-SRA.csv", station)
        for d in daily_rows:
            record = {"station": station, "dt_utc": d["dt"].isoformat().replace("+00:00", "Z"),
                      "timefunc": d["timefunc"], "daily_qc_valid": d["qc_valid"]}
            for label, offset in (("end_at_dt", timedelta(0)), ("end_at_dt_plus_24h", timedelta(days=1))):
                result = summarize_window(d, obs, d["dt"] + offset)
                for key, value in result.items():
                    record[f"{label}_{key}"] = value
            detail.append(record)
        print(f"{station}: 2018 SRA10M bins={len(obs)}, loader_issues={dict(issues)}, daily_rows={len(daily_rows)}")
    with detail_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(detail[0]))
        w.writeheader(); w.writerows(detail)
    summary = []
    for station in STATIONS:
        subset = [r for r in detail if r["station"] == station]
        for label in ("end_at_dt", "end_at_dt_plus_24h"):
            paired = [r for r in subset if r["daily_qc_valid"] and r[f"{label}_complete_qc_window"] and r[f"{label}_daily_mm"] is not None]
            diffs = [abs(r[f"{label}_diff_mm"]) for r in paired]
            summary.append({"station": station, "window_candidate": label, "daily_rows_2018": len(subset),
                            "daily_rows_flag_blank_quality_zero": sum(r["daily_qc_valid"] for r in subset),
                            "complete_qc_windows_with_daily_value": len(paired),
                            "exact_matches_0_1mm": sum(r[f"{label}_exact_to_0_1mm"] for r in paired),
                            "wet_daily_rows": sum(r[f"{label}_daily_mm"] > 0 for r in paired),
                            "wet_rows_exact_match": sum(r[f"{label}_exact_to_0_1mm"] and r[f"{label}_daily_mm"] > 0 for r in paired),
                            "mae_mm": round(sum(diffs) / len(diffs), 6) if diffs else None,
                            "mean_signed_difference_mm": round(sum(r[f"{label}_diff_mm"] for r in paired) / len(paired), 6) if paired else None})
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader(); w.writerows(summary)
    for row in summary:
        print(row)
    print(f"detail={detail_path}; summary={summary_path}")


if __name__ == "__main__":
    main()
