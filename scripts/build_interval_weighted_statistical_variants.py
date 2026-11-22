#!/usr/bin/env python3
"""Build read-only clipped-interval monthly and annual variant diagnostics.

Unlike slot-based canonical variants, every retained archive value is weighted
only over its measured (end-interval, end] overlap with the civil period. The
outputs are a sidecar and do not replace or authorize existing statistics.
"""
from __future__ import annotations
import csv, datetime as dt, hashlib, json, math, sqlite3, zlib
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TZ = ZoneInfo("Europe/Prague")
VARS = ("outTemp", "outHumidity", "pressure", "barometer", "altimeter", "windSpeed", "windGust", "windDir")
VARIANTS = {
    "A_ORIGINAL_VERIFIED": set(),
    "B_DOCUMENTED_SOURCE_AND_RECOVERY": {"SOURCE_MATCHED", "RECOVERED_SOURCE", "RESTORED"},
    "C_ACCEPTED_CORRECTIONS": {"SOURCE_MATCHED", "RECOVERED_SOURCE", "RESTORED"},
    "D_EXTENDED_WITH_ESTIMATES": {"SOURCE_MATCHED", "RECOVERED_SOURCE", "RESTORED", "ESTIMATED"},
    "E_FULL_CURRENT_ARCHIVE": None,
}


def bounds(period: str) -> tuple[int, int]:
    year, month = map(int, period.split("-"))
    start = int(dt.datetime(year, month, 1, tzinfo=TZ).timestamp())
    if month == 12:
        stop = int(dt.datetime(year + 1, 1, 1, tzinfo=TZ).timestamp())
    else:
        stop = int(dt.datetime(year, month + 1, 1, tzinfo=TZ).timestamp())
    return start, stop


def month_of(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts, TZ).strftime("%Y-%m")


def new_acc():
    return {"weighted_sum": Decimal(0), "weight_seconds": 0, "sin": 0.0, "cos": 0.0,
            "retained_intervals": 0, "overlap_excluded_intervals": 0, "invalid_intervals": 0,
            "clipped_intervals": 0, "calm_direction_excluded": 0,
            "unknown_or_unavailable_speed_excluded": 0, "nonnull_values": 0,
            "last_end": None, "first_start": None, "internal_gaps": [],
            "provenance_counts": defaultdict(int)}


def main():
    sqlite_path = DATA / "historical_value_concordance.sqlite"
    manifest = json.loads((DATA / "historical_value_concordance.manifest.json").read_text())
    digest = hashlib.sha256(sqlite_path.read_bytes()).hexdigest()
    if digest != manifest["sqlite_sha256_after_close"]:
        raise SystemExit("Concordance SQLite SHA-256 does not match its closed-file manifest")
    db = sqlite3.connect(f"file:{sqlite_path.resolve()}?mode=ro", uri=True)
    db.execute("PRAGMA query_only=ON")
    if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise SystemExit("Concordance SQLite integrity check failed")
    snapshot = dict(db.execute("SELECT key,value FROM snapshot_meta"))
    total_rows = 0
    metrics = defaultdict(new_acc)
    period_seen = set()
    for ts_raw, interval_raw, blob in db.execute("SELECT dateTime,target_interval,comparison_zlib FROM timestamp_evidence ORDER BY dateTime"):
        total_rows += 1
        ts = int(ts_raw)
        interval_minutes = int(interval_raw or 0)
        fields = json.loads(zlib.decompress(blob))
        local_month = month_of(ts)
        if not 1 <= interval_minutes <= 1440:
            for variable in VARS:
                item = fields[variable]
                value = item.get("target_value")
                if value is None:
                    continue
                category = item.get("provenance_category")
                for variant, allowed in VARIANTS.items():
                    if allowed is not None and category not in allowed:
                        continue
                    key = (local_month, variable, variant)
                    metrics[key]["invalid_intervals"] += 1
                    metrics[key]["nonnull_values"] += 1
                    metrics[key]["provenance_counts"][category or "UNRESOLVED"] += 1
                    period_seen.add(local_month)
            continue
        duration = interval_minutes * 60
        start = ts - duration
        touched_months = {month_of(start), month_of(ts - 1), local_month}
        for month in touched_months:
            lo_period, hi_period = bounds(month)
            lo, hi = max(start, lo_period), min(ts, hi_period)
            if lo >= hi:
                continue
            period_seen.add(month)
            for variable in VARS:
                item = fields[variable]
                value = item.get("target_value")
                if value is None:
                    continue
                category = item.get("provenance_category") or "UNRESOLVED"
                for variant, allowed in VARIANTS.items():
                    if allowed is not None and category not in allowed:
                        continue
                    key = (month, variable, variant)
                    acc = metrics[key]
                    acc["nonnull_values"] += 1
                    acc["provenance_counts"][category] += 1
                    if variable == "windDir":
                        speed_item = fields["windSpeed"]
                        speed = speed_item.get("target_value")
                        speed_category = speed_item.get("provenance_category") or "UNRESOLVED"
                        if speed is None or (allowed is not None and speed_category not in allowed):
                            acc["unknown_or_unavailable_speed_excluded"] += 1
                            continue
                        if Decimal(str(speed)) <= 0:
                            acc["calm_direction_excluded"] += 1
                            continue
                    if acc["last_end"] is not None and lo < acc["last_end"]:
                        acc["overlap_excluded_intervals"] += 1
                        continue
                    if acc["last_end"] is not None and lo > acc["last_end"]:
                        acc["internal_gaps"].append(lo - acc["last_end"])
                    if acc["first_start"] is None:
                        acc["first_start"] = lo
                    acc["last_end"] = hi
                    acc["retained_intervals"] += 1
                    if lo != start or hi != ts:
                        acc["clipped_intervals"] += 1
                    weight = hi - lo
                    acc["weight_seconds"] += weight
                    if variable == "windDir":
                        angle = math.radians(float(value))
                        acc["sin"] += math.sin(angle) * weight
                        acc["cos"] += math.cos(angle) * weight
                    else:
                        acc["weighted_sum"] += Decimal(str(value)) * weight
        if total_rows % 250000 == 0:
            print(json.dumps({"rows": total_rows, "last_timestamp": ts}), flush=True)
    db.close()

    canonical = {}
    with (DATA / "STATISTICAL_VARIANTS_MONTHLY.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            canonical[(row["period"], row["variable"], row["variant"])] = row

    monthly = []
    annual_acc = defaultdict(lambda: {"weighted_sum": Decimal(0), "weight_seconds": 0, "sin": 0.0, "cos": 0.0,
                                      "covered_seconds": 0, "period_seconds": 0, "retained_intervals": 0,
                                      "overlap_excluded_intervals": 0, "invalid_intervals": 0,
                                      "clipped_intervals": 0, "calm_direction_excluded": 0,
                                      "unknown_or_unavailable_speed_excluded": 0,
                                      "nonnull_values": 0, "provenance_counts": defaultdict(int),
                                      "longest_gap_seconds": 0})
    target_meta = json.loads(snapshot["target"])
    first_local = dt.datetime.fromtimestamp(int(target_meta["min_timestamp"]), TZ)
    last_local = dt.datetime.fromtimestamp(int(target_meta["max_timestamp"]), TZ)
    first_ordinal = first_local.year * 12 + first_local.month - 1
    last_ordinal = last_local.year * 12 + last_local.month - 1
    all_months = []
    for ordinal in range(first_ordinal, last_ordinal + 1):
        year, month_index = divmod(ordinal, 12)
        all_months.append(f"{year:04d}-{month_index + 1:02d}")
    for month in all_months:
        start, stop = bounds(month)
        year = month[:4]
        for variable in VARS:
            for variant in VARIANTS:
                key = (month, variable, variant)
                acc = metrics[key]
                weight = acc["weight_seconds"]
                if variable == "windDir":
                    mean = math.degrees(math.atan2(acc["sin"], acc["cos"])) % 360 if weight else None
                    resultant = math.hypot(acc["sin"], acc["cos"]) / weight if weight else None
                else:
                    mean = float(acc["weighted_sum"] / weight) if weight else None
                    resultant = None
                covered = weight
                edge_gaps = []
                if acc["first_start"] is not None:
                    edge_gaps = [acc["first_start"] - start, stop - acc["last_end"]]
                longest_gap = max(acc["internal_gaps"] + edge_gaps, default=stop - start)
                row = {
                    "period": month, "variable": variable, "variant": variant,
                    "unit": canonical.get(key, {}).get("unit", ""),
                    "expected_unique_slots": int(canonical.get(key, {}).get("expected_unique_slots") or 0),
                    "slot_observed_values": int(canonical.get(key, {}).get("variant_on_grid_values") or 0),
                    "slot_coverage": float(canonical.get(key, {}).get("coverage") or 0),
                    "interval_mean": mean, "interval_resultant": resultant,
                    "weight_seconds": weight, "period_seconds": stop - start,
                    "time_coverage": covered / (stop - start),
                    "longest_uncovered_gap_seconds": longest_gap,
                    "retained_intervals": acc["retained_intervals"],
                    "overlap_excluded_intervals": acc["overlap_excluded_intervals"],
                    "invalid_intervals": acc["invalid_intervals"],
                    "clipped_intervals": acc["clipped_intervals"],
                    "calm_direction_excluded": acc["calm_direction_excluded"],
                    "unknown_or_unavailable_speed_excluded": acc["unknown_or_unavailable_speed_excluded"],
                    "nonnull_values": acc["nonnull_values"],
                    "provenance_counts": json.dumps(dict(sorted(acc["provenance_counts"].items())), sort_keys=True),
                    "methodology": "Archive-end intervals are clipped to Europe/Prague civil-month boundaries; overlapping intervals are excluded wholesale; scalar values are duration-weighted; wind direction uses duration-weighted circular vectors and same-variant positive windSpeed; off-grid values are retained if their interval is valid.",
                }
                monthly.append(row)
                ya = annual_acc[(year, variable, variant)]
                ya["weighted_sum"] += acc["weighted_sum"]
                ya["weight_seconds"] += weight
                ya["sin"] += acc["sin"]
                ya["cos"] += acc["cos"]
                ya["covered_seconds"] += covered
                ya["period_seconds"] += stop - start
                for name in ("retained_intervals", "overlap_excluded_intervals", "invalid_intervals", "clipped_intervals", "calm_direction_excluded", "unknown_or_unavailable_speed_excluded", "nonnull_values"):
                    ya[name] += acc[name]
                ya["longest_gap_seconds"] = max(ya["longest_gap_seconds"], longest_gap)
                for category, count in acc["provenance_counts"].items():
                    ya["provenance_counts"][category] += count
    annual = []
    def exact_year_gap(year: str, variable: str, variant: str) -> int:
        year_start, year_end = bounds(year + "-01")
        last_end = None
        longest = 0
        for month in all_months:
            if month[:4] != year:
                continue
            acc = metrics[(month, variable, variant)]
            longest = max(longest, max(acc["internal_gaps"], default=0))
            if acc["first_start"] is None:
                continue
            gap_start = year_start if last_end is None else last_end
            longest = max(longest, acc["first_start"] - gap_start)
            last_end = acc["last_end"]
        if last_end is None:
            return year_end - year_start
        return max(longest, year_end - last_end)

    for (year, variable, variant), acc in sorted(annual_acc.items()):
        weight = acc["weight_seconds"]
        if variable == "windDir":
            mean = math.degrees(math.atan2(acc["sin"], acc["cos"])) % 360 if weight else None
            resultant = math.hypot(acc["sin"], acc["cos"]) / weight if weight else None
        else:
            mean = float(acc["weighted_sum"] / weight) if weight else None
            resultant = None
        annual.append({
            "period": year, "variable": variable, "variant": variant,
            "unit": canonical.get((year + "-01", variable, variant), {}).get("unit", ""),
            "interval_mean": mean, "interval_resultant": resultant,
            "weight_seconds": weight, "period_seconds": acc["period_seconds"],
            "time_coverage": acc["covered_seconds"] / acc["period_seconds"] if acc["period_seconds"] else 0,
            "longest_uncovered_gap_seconds": exact_year_gap(year, variable, variant),
            "retained_intervals": acc["retained_intervals"],
            "overlap_excluded_intervals": acc["overlap_excluded_intervals"],
            "invalid_intervals": acc["invalid_intervals"], "clipped_intervals": acc["clipped_intervals"],
            "calm_direction_excluded": acc["calm_direction_excluded"],
            "unknown_or_unavailable_speed_excluded": acc["unknown_or_unavailable_speed_excluded"],
            "nonnull_values": acc["nonnull_values"],
            "provenance_counts": json.dumps(dict(sorted(acc["provenance_counts"].items())), sort_keys=True),
            "methodology": "Annual result combines all civil-month-clipped intervals in the calendar year; the longest gap is the maximum monthly uncovered span (cross-month gaps are not reconstructed by this summary).",
        })

    out_month = DATA / "INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MONTHLY.csv"
    out_year = DATA / "INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_ANNUAL.csv"
    for path, rows in ((out_month, monthly), (out_year, annual)):
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    meta = {
        "schema": "loucka-interval-weighted-statistical-variants-v1",
        "snapshot_sha256": digest, "source_rows_read": total_rows,
        "source_snapshot_utc": snapshot.get("snapshot_utc"),
        "monthly_rows": len(monthly), "annual_rows": len(annual),
        "period_count": len(all_months), "publication_authorized": False,
        "rain_excluded": True,
        "methodology": "Civil-period means weighted by exact overlap of each archive interval; overlaps excluded; off-grid intervals included; time coverage capped at 100% by overlap exclusion.",
        "annual_gap_note": "Annual longest_uncovered_gap_seconds is recomputed across consecutive month boundaries; annual coverage is exact under the calendar-year partition.",
        "canonical_variants_replaced": False,
    }
    (DATA / "INTERVAL_WEIGHTED_STATISTICAL_VARIANTS_MANIFEST.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"snapshot_sha256": digest, "rows_read": total_rows, "monthly_rows": len(monthly), "annual_rows": len(annual), "periods": len(all_months), "max_time_coverage": max((r["time_coverage"] for r in monthly), default=0), "overlap_excluded": sum(r["overlap_excluded_intervals"] for r in monthly)}, indent=2))


if __name__ == "__main__":
    main()
