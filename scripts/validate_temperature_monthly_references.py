#!/usr/bin/env python3
"""Compare monthly temperature candidates to exact-UTC CHMI 10-minute data."""
from __future__ import annotations
import csv, hashlib, json, math, re, sqlite3, statistics, zlib
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = DATA / "historical_value_concordance.sqlite"
TZ = ZoneInfo("Europe/Prague")
STEP = 600

def quantile(values, q):
    if not values: return None
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo, hi = int(pos), min(int(pos) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)

def period_bounds(period):
    y, m = map(int, period.split("-"))
    lo = int(datetime(y, m, 1, tzinfo=TZ).timestamp())
    y2, m2 = (y + 1, 1) if m == 12 else (y, m + 1)
    hi = int(datetime(y2, m2, 1, tzinfo=TZ).timestamp())
    return lo, hi

def adjacent_paths(relpath):
    path = ROOT / relpath
    match = re.match(r"^(.*?)(\d{6})(\.(?:json|csv))$", path.name)
    result = [path]
    if not match: return result
    prefix, yymm, suffix = match.groups()
    year, month = int(yymm[:4]), int(yymm[4:])
    for delta in (-1, 1):
        yy, mm = year, month + delta
        if mm == 0: yy, mm = yy - 1, 12
        elif mm == 13: yy, mm = yy + 1, 1
        candidate = path.with_name(f"{prefix}{yy:04d}{mm:02d}{suffix}")
        if candidate.is_file(): result.append(candidate)
    return result

def parse_reference(path, expected_station):
    rows = {}
    quality_counts, flag_counts = Counter(), Counter()
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                element = row.get("ELEMENT")
                if element not in ("T", "TA"): continue
                station = row.get("STATION")
                if station != expected_station:
                    raise ValueError(f"Station mismatch in {path}: {station} != {expected_station}")
                stamp = (row.get("DT") or "").replace("Z", "+00:00")
                try:
                    ts = int(datetime.fromisoformat(stamp).timestamp())
                    value = float(row.get("VALUE") or row.get("VAL"))
                except (ValueError, TypeError):
                    continue
                quality = str(row.get("QUALITY", "")); flag = str(row.get("FLAG", ""))
                quality_counts[quality] += 1; flag_counts[flag] += 1
                rows[ts] = {"value": value, "quality": quality, "flag": flag}
    else:
        raw = json.loads(path.read_text(encoding="utf-8"))
        data = raw["data"]["data"]
        for station, element, stamp, value, flag, quality in data["values"]:
            if element not in ("T", "TA"): continue
            if station != expected_station:
                raise ValueError(f"Station mismatch in {path}: {station} != {expected_station}")
            try:
                ts = int(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp())
                value = float(value)
            except (ValueError, TypeError):
                continue
            q, fl = str(quality), str(flag or "")
            quality_counts[q] += 1; flag_counts[fl] += 1
            rows[ts] = {"value": value, "quality": q, "flag": fl}
    return rows, quality_counts, flag_counts

def summarize_period(period, candidate, ref):
    lo, hi = period_bounds(period)
    expected = list(range(((lo // STEP) + 1) * STEP, hi + 1, STEP))
    # Same-UTC-timestamp pairing only. No interpolation or cadence conversion.
    expected_set = set(expected)
    valid_ref = {ts: r["value"] for ts, r in ref.items()
                 if ts in expected_set and r["quality"] in ("0", "0.0") and math.isfinite(r["value"])}
    pairs = [(ts, float(candidate[ts]), valid_ref[ts]) for ts in sorted(valid_ref) if ts in candidate]
    differences = [rv - lv for _, lv, rv in pairs]
    n = len(pairs)
    ref_values = [rv for _, _, rv in pairs]
    local_values = [lv for _, lv, _ in pairs]
    if n:
        bias = statistics.mean(differences)
        mae = statistics.mean(abs(x) for x in differences)
        rmse = math.sqrt(statistics.mean(x*x for x in differences))
        mx, my = statistics.mean(local_values), statistics.mean(ref_values)
        den = math.sqrt(sum((x-mx)**2 for x in local_values) * sum((y-my)**2 for y in ref_values))
        corr = sum((x-mx)*(y-my) for x, y in zip(local_values, ref_values)) / den if den else None
    else:
        bias = mae = rmse = corr = None
    daily = defaultdict(lambda: [[], []])
    diurnal = defaultdict(list)
    for ts, lv, rv in pairs:
        local_dt = datetime.fromtimestamp(ts, TZ)
        daily[local_dt.date().isoformat()][0].append(lv)
        daily[local_dt.date().isoformat()][1].append(rv)
        diurnal[f"{local_dt.hour//6*6:02d}-{local_dt.hour//6*6+5:02d}"].append(rv-lv)
    daily_diffs = [statistics.mean(v[1])-statistics.mean(v[0]) for v in daily.values()]
    return {
        "expected_10_minute_slots_in_local_civil_month": len(expected),
        "valid_reference_slots_in_month": len(valid_ref),
        "matched_pairs": n,
        "unmatched_valid_reference_slots": len(valid_ref)-n,
        "loucka_slots_without_valid_reference": sum(ts in candidate for ts in expected_set)-n,
        "matched_coverage_of_valid_reference": n/len(valid_ref) if valid_ref else 0.0,
        "reference_slot_coverage_of_expected": len(valid_ref)/len(expected) if expected else 0.0,
        "loucka_available_at_expected_reference_slots": sum(ts in candidate for ts in expected_set),
        "loucka_candidate_monthly_mean": candidate.get("candidate_monthly_mean"),
        "loucka_paired_sample_mean_C": statistics.mean(local_values) if n else None,
        "reference_paired_sample_mean_C": statistics.mean(ref_values) if n else None,
        "paired_sample_mean_difference_reference_minus_loucka_C": bias,
        "bias_reference_minus_loucka_C": bias, "mae_C": mae, "rmse_C": rmse,
        "correlation": corr,
        "difference_quantiles_C": {"p05": quantile(differences, .05), "p50": quantile(differences, .50), "p95": quantile(differences, .95)},
        "daily_mean_comparison": {
            "days_with_pairs": len(daily_diffs),
            "mean_daily_bias_reference_minus_loucka_C": statistics.mean(daily_diffs) if daily_diffs else None,
            "mae_of_daily_mean_differences_C": statistics.mean(abs(x) for x in daily_diffs) if daily_diffs else None,
            "rmse_of_daily_mean_differences_C": math.sqrt(statistics.mean(x*x for x in daily_diffs)) if daily_diffs else None},
        "six_hour_local_time_bias_C": {k: statistics.mean(v) for k, v in sorted(diurnal.items())},
        "paired_difference_sample_count": len(differences)
    }

def main():
    availability = json.loads((ROOT / "TEMPERATURE_REFERENCE_AVAILABILITY.json").read_text())
    candidates = {x["period"]: x for x in availability["candidates"] if x["reference_status"] == "SAME_MONTH_SUBDAILY_AVAILABLE"}
    candidate_values = {x["period"]: x["value"] for x in availability["candidates"]}
    db = sqlite3.connect(f"file:{DB.resolve()}?mode=ro", uri=True)
    out = []
    for month, candidate in sorted(candidates.items()):
        lo, hi = period_bounds(month)
        expected_period_timestamps = set(range(((lo // STEP) + 1) * STEP, hi + 1, STEP))
        local = {}
        for ts, blob in db.execute("SELECT dateTime,comparison_zlib FROM timestamp_evidence WHERE dateTime>? AND dateTime<=? ORDER BY dateTime", (lo, hi)):
            value = json.loads(zlib.decompress(blob))["outTemp"].get("target_value")
            if value is not None: local[int(ts)] = float(value)
        local["candidate_monthly_mean"] = candidate_values.get(month)
        # Resolve immediate neighboring UTC month files to cover the local civil-month UTC edges.
        for base in candidate["references"]:
            if base.get("cadence") != "10-minute": continue
            station = base["station_id"]
            # Distinct files were collected by base; retain only this station's direct and adjacent files.
            paths = adjacent_paths(base["path"])
            merged = {}
            quality, flags = Counter(), Counter()
            for path in paths:
                parsed, qc, fc = parse_reference(path, station)
                merged.update(parsed); quality.update(qc); flags.update(fc)
            result = summarize_period(month, local, merged)
            in_period_quality = Counter(r["quality"] for ts, r in merged.items()
                                        if ts in expected_period_timestamps)
            result.update({
                "period": month, "variable": "outTemp", "station_id": station,
                "reference_path": base["path"], "reference_sha256": hashlib.sha256((ROOT/base["path"]).read_bytes()).hexdigest(),
                "reference_files_used": [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
                "quality_counts": dict(in_period_quality),
                "quality_counts_all_loaded_files": dict(quality), "flag_counts_all_loaded_files": dict(flags),
                "quality_zero_count_in_local_period": sum(1 for ts in range(((lo//STEP)+1)*STEP, hi+1, STEP) if ts in merged and merged[ts]["quality"] in ("0", "0.0")),
                "cadence": "10-minute exact UTC timestamp; no interpolation",
                "reference_time_function_semantics": "CHMI publishes 10-minute timestamped temperature; whether each value is instantaneous or an interval mean is not established by the metadata checked in this audit.",
                "temporal_structure": "Bias is additionally summarized by six-hour Europe/Prague bins; seasonal/local differences remain regional context, not calibration.",
                "interpretation": "Regional plausibility and temporal behavior only; not proof of Loucka sensor identity, calibration, siting equivalence, or measurement truth."
            })
            out.append(result)
    db.close()
    doc = {
        "schema": "loucka-monthly-temperature-reference-validation-v2",
        "snapshot_id": hashlib.sha256(DB.read_bytes()).hexdigest(),
        "candidate_month_count": len(candidates), "station_month_results": out,
        "method_limits": ["Exact UTC timestamps only; no interpolation.", "CHMI quality codes other than zero are excluded from pairs and counted separately.", "Where cached, the adjacent UTC month file is included to cover Europe/Prague month edges.", "A CHMI 10-minute sample is not assumed to be time-functionally identical to a WeeWX archive interval."]
    }
    (ROOT / "MONTHLY_TEMPERATURE_REFERENCE_VALIDATION.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    january = [{k:r.get(k) for k in ("station_id", "matched_pairs", "matched_coverage_of_valid_reference", "correlation", "bias_reference_minus_loucka_C")}
               for r in out if r["period"] == "2026-01"]
    print(json.dumps({"candidate_months": len(candidates), "station_month_results": len(out),
                      "matched_pairs_total": sum(x["matched_pairs"] for x in out),
                      "january_2026_station_results": january}, indent=2))

if __name__ == "__main__": main()
