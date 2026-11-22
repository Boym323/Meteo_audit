#!/usr/bin/env python3
"""Compare interval-aware annual outTemp results for highlighted years."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
import zlib
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data/historical_value_concordance.sqlite"
TZ = ZoneInfo("Europe/Prague")
YEARS = ("2010", "2024")
B_CATEGORIES = {"SOURCE_MATCHED", "RECOVERED_SOURCE", "RESTORED"}

import sys
sys.path.insert(0, str(ROOT / "src"))
from meteo_audit.interval_period_stats import summarize_clipped_nonoverlapping


def epoch(local: dt.datetime) -> int:
    return int(local.replace(tzinfo=TZ).timestamp())


def month_bounds(label: str) -> tuple[int, int]:
    y, m = map(int, label.split("-"))
    start = dt.datetime(y, m, 1)
    end = dt.datetime(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return epoch(start), epoch(end)


def main() -> None:
    target_months = {f"{year}-{m:02d}" for year in YEARS for m in range(1, 13)}
    spans: dict[tuple[str, str], list[tuple[int, int, str]]] = defaultdict(list)
    db = sqlite3.connect(f"file:{DB_PATH.resolve()}?mode=ro", uri=True)
    db.execute("PRAGMA query_only=ON")
    # The concordance records a 5–75 minute interval range. The bounded
    # one-hour left padding captures intervals crossing the first period edge.
    lo = min(month_bounds(f"{year}-01")[0] for year in YEARS) - 3600
    hi = max(month_bounds(f"{year}-12")[1] for year in YEARS)
    query = """SELECT dateTime,target_interval,comparison_zlib
               FROM timestamp_evidence WHERE dateTime>=? AND dateTime<?
               ORDER BY dateTime"""
    scanned = 0
    for ts, interval, blob in db.execute(query, (lo, hi)):
        scanned += 1
        ts, interval = int(ts), int(interval or 0)
        if interval <= 0 or interval > 1440:
            continue
        local = dt.datetime.fromtimestamp(ts, TZ)
        this_month = local.strftime("%Y-%m")
        prev_month_date = local.replace(day=1) - dt.timedelta(days=1)
        possible = (this_month, prev_month_date.strftime("%Y-%m"))
        fields = None
        for month in possible:
            if month not in target_months:
                continue
            start, end = month_bounds(month)
            if ts <= start or ts - interval * 60 >= end:
                continue
            if fields is None:
                fields = json.loads(zlib.decompress(blob))
            item = fields.get("outTemp", {})
            value = item.get("target_value")
            if value is None:
                continue
            spans[(month, "E_FULL_CURRENT_ARCHIVE")].append(
                (ts - interval * 60, ts, str(value))
            )
            if item.get("provenance_category") in B_CATEGORIES:
                spans[(month, "B_DOCUMENTED_SOURCE_AND_RECOVERY")].append(
                    (ts - interval * 60, ts, str(value))
                )
    db.close()

    canonical_path = ROOT / "ANNUAL_REPRESENTATIVENESS_REVIEW.json"
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    annual_rows = {}
    with (ROOT / "data/STATISTICAL_VARIANTS_ANNUAL.csv").open(encoding="utf-8", newline="") as f:
        import csv
        for row in csv.DictReader(f):
            if row["period"] in YEARS and row["variable"] == "outTemp" and row["variant"] in {
                "B_DOCUMENTED_SOURCE_AND_RECOVERY", "E_FULL_CURRENT_ARCHIVE"
            }:
                annual_rows[(row["period"], row["variant"])] = row

    results = []
    for year in YEARS:
        months = []
        for m in range(1, 13):
            label = f"{year}-{m:02d}"
            start, end = month_bounds(label)
            row = {"period": label, "period_seconds": end - start}
            for variant in ("B_DOCUMENTED_SOURCE_AND_RECOVERY", "E_FULL_CURRENT_ARCHIVE"):
                summary = summarize_clipped_nonoverlapping(spans[(label, variant)], start, end)
                row[variant] = summary
            bmean = row["B_DOCUMENTED_SOURCE_AND_RECOVERY"]["weighted_mean"]
            emean = row["E_FULL_CURRENT_ARCHIVE"]["weighted_mean"]
            row["E_minus_B_interval_mean_C"] = float(emean) - float(bmean) if bmean and emean else None
            months.append(row)
        for variant in ("B_DOCUMENTED_SOURCE_AND_RECOVERY", "E_FULL_CURRENT_ARCHIVE"):
            total_seconds = sum(x[variant]["covered_seconds"] for x in months)
            total_weighted = sum(
                (float(x[variant]["weighted_mean"]) * x[variant]["covered_seconds"]
                 for x in months if x[variant]["weighted_mean"] is not None), 0.0
            )
            annual_rows[(year, variant)]["interval_aware_mean"] = (
                total_weighted / total_seconds if total_seconds else None
            )
        old = next(x for x in canonical["years"] if x["year"] == year)
        results.append({
            "year": year,
            "months": months,
            "annual": {
                variant: {
                    "interval_aware_mean_C": annual_rows[(year, variant)]["interval_aware_mean"],
                    "slot_based_mean_C": float(annual_rows[(year, variant)]["mean_time_weighted"]),
                    "interval_aware_covered_seconds": sum(x[variant]["covered_seconds"] for x in months),
                    "period_seconds": sum(x["period_seconds"] for x in months),
                    "interval_aware_time_coverage": sum(x[variant]["covered_seconds"] for x in months) / sum(x["period_seconds"] for x in months),
                    "overlap_excluded_intervals": sum(x[variant]["overlap_excluded_intervals"] for x in months),
                    "longest_monthly_gap_seconds": max(x[variant]["longest_gap_seconds"] for x in months),
                }
                for variant in ("B_DOCUMENTED_SOURCE_AND_RECOVERY", "E_FULL_CURRENT_ARCHIVE")
            },
            "existing_slot_based_review": {
                "B_coverage": old["B_coverage"],
                "months_B_coverage_ge_95": old["months_B_coverage_ge_95"],
                "months_with_mean_screen_days_pass": old["months_with_mean_screen_days_pass"],
                "worst_gap_month": old["worst_gap_month"],
                "worst_monthly_gap_seconds": old["worst_monthly_gap_seconds"],
            },
        })
    result = {
        "schema": "loucka-interval-aware-annual-temperature-review-v1",
        "snapshot_id": hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
        "years": results,
        "source_rows_scanned": scanned,
        "method": "For each Europe/Prague civil month, clip archive-end spans (end-interval,end] to month bounds. Duration-weight retained values; exclude an entire later span when it overlaps an already retained span. Annual mean and time coverage aggregate the disjoint monthly segments. B includes only SOURCE_MATCHED, RECOVERED_SOURCE, RESTORED. E includes all non-NULL target values. This is a temporal robustness review, not a changed publication decision.",
        "limitations": [
            "Interval means are treated as representative over their recorded interval; raw sub-interval measurements are unavailable here.",
            "Overlapping later intervals are excluded wholesale because their aggregate value cannot be safely split.",
            "High temporal coverage does not resolve provenance, sensor epoch, or regional representativeness.",
            "No historical data or publication state was changed.",
        ],
    }
    out = ROOT / "ANNUAL_INTERVAL_AWARE_TEMPERATURE_REVIEW.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "years": [
        {"year": y["year"], "B": y["annual"]["B_DOCUMENTED_SOURCE_AND_RECOVERY"],
         "E": y["annual"]["E_FULL_CURRENT_ARCHIVE"]} for y in results
    ]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
