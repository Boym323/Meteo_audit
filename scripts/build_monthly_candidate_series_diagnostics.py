#!/usr/bin/env python3
"""Summarize frozen target series for every priority candidate, read-only."""
import hashlib, json, sqlite3, zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data/historical_value_concordance.sqlite"
VARS = ("outTemp", "outHumidity", "pressure", "barometer", "altimeter", "windSpeed", "windGust", "windDir")

def main():
    candidates = json.loads((ROOT / "MONTHLY_PUBLICATION_CANDIDATES.json").read_text())["candidates"]
    wanted = {(x["period"], x["variable"]) for x in candidates}
    acc = {}
    for period, var in wanted:
        acc[(period, var)] = {
            "rows": 0, "null_rows": 0, "values": set(), "frequencies": Counter(),
            "sum": 0.0, "minimum": None, "maximum": None, "zero_count": 0,
            "special_count": 0, "run_value": None, "run_start": None,
            "run_last_end": None, "run_interval": None, "max_run_seconds": 0,
            "max_run_value": None, "max_run_slots": 0, "max_run_value_slots": 0,
            "barometer_pressure_differences": [], "altimeter_barometer_differences": [],
        }
    db = sqlite3.connect(f"file:{DB_PATH.resolve()}?mode=ro", uri=True)
    previous_ts = None
    for index, (ts, period, interval, blob) in enumerate(db.execute(
        "SELECT dateTime,local_month,target_interval,comparison_zlib FROM timestamp_evidence ORDER BY dateTime")):
        period_vars = [v for v in VARS if (period, v) in wanted]
        if not period_vars:
            previous_ts = ts
            continue
        fields = json.loads(zlib.decompress(blob))
        if (period, "barometer") in wanted:
            baro = fields["barometer"].get("target_value")
            pressure = fields["pressure"].get("target_value")
            altimeter = fields["altimeter"].get("target_value")
            if baro is not None and pressure is not None:
                acc[(period, "barometer")]["barometer_pressure_differences"].append(float(baro) - float(pressure))
            if altimeter is not None and baro is not None:
                acc[(period, "barometer")]["altimeter_barometer_differences"].append(float(altimeter) - float(baro))
        for var in period_vars:
            a = acc[(period, var)]
            item = fields[var]
            raw = item.get("target_value")
            iv = int(item.get("target_interval_minutes") or interval or 0)
            if raw is None:
                a["null_rows"] += 1
                a["run_value"] = None
                continue
            value = float(raw)
            a["rows"] += 1
            a["values"].add(value)
            a["frequencies"][str(raw)] += 1
            a["sum"] += value
            a["minimum"] = value if a["minimum"] is None else min(value, a["minimum"])
            a["maximum"] = value if a["maximum"] is None else max(value, a["maximum"])
            if value == 0:
                a["zero_count"] += 1
            if var == "outHumidity" and value >= 99:
                a["special_count"] += 1
            if var == "windSpeed" and value == 0:
                a["special_count"] += 1
            cadence_ok = (a["run_last_end"] is not None and previous_ts is not None and
                          ts - previous_ts <= max(1, int(max(iv, a["run_interval"] or iv) * 60 * 1.5)))
            if a["run_value"] == value and cadence_ok:
                a["run_slots"] = a.get("run_slots", 1) + 1
                a["run_last_end"] = ts
                a["run_interval"] = iv
            else:
                a["run_value"] = value
                a["run_start"] = ts
                a["run_last_end"] = ts
                a["run_interval"] = iv
                a["run_slots"] = 1
            run_seconds = ts - a["run_start"] + iv * 60
            if run_seconds > a["max_run_seconds"]:
                a["max_run_seconds"] = run_seconds
                a["max_run_value"] = value
                a["max_run_slots"] = a["run_slots"]
            if var == "outHumidity" and value >= 99:
                if a.get("special_run_value") is not None and cadence_ok:
                    a["special_run_slots"] = a.get("special_run_slots", 1) + 1
                    a["special_run_start"] = a.get("special_run_start", ts)
                else:
                    a["special_run_value"] = True
                    a["special_run_start"] = ts
                    a["special_run_slots"] = 1
                seconds = ts - a["special_run_start"] + iv * 60
                if seconds > a["max_run_value_slots"]:
                    a["max_run_value_slots"] = seconds
            else:
                a["special_run_value"] = None
        previous_ts = ts
        if index and index % 250000 == 0:
            print(f"processed_rows={index}", flush=True)
    db.close()
    records = []
    def quantile(values, q):
        if not values: return None
        ordered = sorted(values)
        pos = (len(ordered) - 1) * q
        lo, hi = int(pos), min(int(pos) + 1, len(ordered))
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)
    for (period, var), a in sorted(acc.items()):
        dominant = max(a["frequencies"].items(), key=lambda kv: (kv[1], kv[0])) if a["frequencies"] else (None, 0)
        records.append({
            "period": period, "variable": var, "target_nonnull_rows": a["rows"],
            "null_rows": a["null_rows"], "distinct_values": len(a["values"]),
            "minimum": a["minimum"], "maximum": a["maximum"],
            "arithmetic_sample_mean": a["sum"] / a["rows"] if a["rows"] else None,
            "dominant_exact_value": dominant[0], "dominant_exact_value_rows": dominant[1],
            "dominant_exact_value_fraction": dominant[1] / a["rows"] if a["rows"] else None,
            "zero_rows": a["zero_count"],
            "saturated_humidity_rows_ge_99_pct": a["special_count"] if var == "outHumidity" else None,
            "calm_wind_speed_rows": a["special_count"] if var == "windSpeed" else None,
            "longest_consecutive_exact_value_run_seconds": a["max_run_seconds"],
            "longest_run_value": a["max_run_value"], "longest_run_slots": a["max_run_slots"],
            "longest_humidity_ge_99_run_seconds": a["max_run_value_slots"] if var == "outHumidity" else None,
            "concurrent_pressure_field_offsets_hpa": ({
                "barometer_minus_pressure": {
                    "paired_rows": len(a["barometer_pressure_differences"]),
                    "median": __import__("statistics").median(a["barometer_pressure_differences"]) if a["barometer_pressure_differences"] else None,
                    "p05": quantile(a["barometer_pressure_differences"], .05),
                    "p95": quantile(a["barometer_pressure_differences"], .95),
                    "minimum": min(a["barometer_pressure_differences"]) if a["barometer_pressure_differences"] else None,
                    "maximum": max(a["barometer_pressure_differences"]) if a["barometer_pressure_differences"] else None},
                "altimeter_minus_barometer": {
                    "paired_rows": len(a["altimeter_barometer_differences"]),
                    "median": __import__("statistics").median(a["altimeter_barometer_differences"]) if a["altimeter_barometer_differences"] else None,
                    "p05": quantile(a["altimeter_barometer_differences"], .05),
                    "p95": quantile(a["altimeter_barometer_differences"], .95),
                    "minimum": min(a["altimeter_barometer_differences"]) if a["altimeter_barometer_differences"] else None,
                    "maximum": max(a["altimeter_barometer_differences"]) if a["altimeter_barometer_differences"] else None}
            } if var == "barometer" else None),
            "run_method": "adjacent archived rows with equal target value; run breaks when gap exceeds 1.5 times the larger adjacent interval; duration includes final row interval",
            "interpretation_limit": "Descriptive archive-series screening only. Repeated values, extremes, zeros and regional differences do not alone establish sensor error or a replacement value."
        })
    out = {
        "schema": "loucka-monthly-candidate-series-diagnostics-v1",
        "snapshot_id": hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
        "snapshot_sha256": hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
        "candidate_count": len(candidates), "period_variable_count": len(records),
        "series_definition": "Target values from immutable historical concordance; no candidate values or source archives modified.",
        "records": records
    }
    (ROOT / "MONTHLY_CANDIDATE_SERIES_DIAGNOSTICS.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": len(candidates), "series_records": len(records),
                      "snapshot_id": out["snapshot_id"]}, indent=2))

if __name__ == "__main__":
    main()
