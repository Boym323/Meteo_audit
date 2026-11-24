#!/usr/bin/env python3
"""Aggregate a temporary read-only WH1080 hourly export against CHMI station P."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

STATIONS = {"0-20000-0-11774": ("H", 222.25), "0-20000-0-11782": ("M", 252.8)}
G, RD = 9.80665, 287.05


def quantile(xs, p):
    if not xs:
        return None
    a = sorted(xs)
    x = (len(a) - 1) * p
    i = int(x)
    return a[i] + (a[min(i + 1, len(a) - 1)] - a[i]) * (x - i)


def summary(errors):
    if not errors:
        return {"n": 0, "mae_hpa": None, "median_bias_hpa": None,
                "mad_hpa": None, "p95_abs_error_hpa": None}
    bias = statistics.median(errors)
    return {"n": len(errors), "mae_hpa": statistics.fmean(abs(x) for x in errors),
            "median_bias_hpa": bias,
            "mad_hpa": statistics.median(abs(x - bias) for x in errors),
            "p95_abs_error_hpa": quantile([abs(x) for x in errors], .95)}


def load_references(cache: Path):
    manifest_path = cache / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    references = defaultdict(dict)
    expected = {(sid, element, month) for sid in STATIONS
                for element in ("P",) for month in range(1, 13)}
    found = set()
    for item in manifest["items"]:
        if (item.get("availability") != "available" or item.get("kind") != "hourly_csv"
                or item.get("period", "")[:4] != "2018" or item.get("element") != "P"
                or item.get("station_id") not in STATIONS):
            continue
        month = int(item["period"][-2:])
        found.add((item["station_id"], "P", month))
        path = cache / "raw" / item["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("ČHMÚ file SHA-256 mismatch: " + item["path"])
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row["STATION"] != item["station_id"] or row["ELEMENT"] != "P":
                    raise ValueError("Unexpected station/element in " + item["path"])
                if row["QUALITY"] not in ("0", "0.0") or not row["VALUE"]:
                    continue
                if not row["DT"].endswith("Z"):
                    raise ValueError("ČHMÚ timestamp is not explicit UTC")
                ts = int(datetime.fromisoformat(row["DT"].replace("Z", "+00:00")).timestamp())
                references[(item["station_id"], ts)]["P"] = float(row["VALUE"])
    if found != expected:
        raise ValueError(f"Incomplete hourly CHMI P files: {len(found)}/{len(expected)}")
    return references, hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def evaluate(export_csv: Path, references):
    groups = defaultdict(list)
    counts = {"source_rows": 0, "target_pressure_missing": 0,
              "target_pressure_present": 0, "missing_outTemp": 0,
              "matched_hole_sov": 0, "matched_mosnov": 0}
    with export_csv.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"dateTime_utc", "target_pressure_hpa", "target_outTemp_c",
                    "source_usUnits", "source_interval_minutes", "source_pressure_hpa"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("Unexpected temporary export column set")
        for row in reader:
            counts["source_rows"] += 1
            ts = int(row["dateTime_utc"])
            if ts % 3600 or not 1514764800 <= ts < 1546300800:
                raise ValueError("Source row is not an exact UTC hour in 2018")
            if row["source_usUnits"] != "17" or row["source_interval_minutes"] != "5":
                raise ValueError("Unexpected WH1080 source unit/interval")
            bucket = "missing" if row["target_pressure_hpa"] in ("", "NULL", "None") else "present"
            counts["target_pressure_missing" if bucket == "missing" else "target_pressure_present"] += 1
            if row["target_outTemp_c"] in ("", "NULL", "None"):
                counts["missing_outTemp"] += 1
                continue
            temp = float(row["target_outTemp_c"])
            if not -80 <= temp <= 60:
                raise ValueError("outTemp outside physical envelope")
            pressure = float(row["source_pressure_hpa"])
            for sid, (label, height) in STATIONS.items():
                ref = references.get((sid, ts), {}).get("P")
                if ref is None:
                    continue
                adjusted = pressure * math.exp(G * (425.0 - height) /
                                               (RD * (temp + 273.15)))
                groups[(label, bucket)].append(adjusted - ref)
                counts["matched_hole_sov" if label == "H" else "matched_mosnov"] += 1
    return counts, {f"{station}_{bucket}": summary(values)
                    for (station, bucket), values in sorted(groups.items())}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--export", required=True, type=Path,
                    help="temporary CSV from sql/readonly/pressure_wh1080_hourly_chmi_2018.sql")
    ap.add_argument("--chmi-cache", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    refs, manifest_sha = load_references(args.chmi_cache)
    counts, groups = evaluate(args.export, refs)
    result = {"schema": "loucka-wh1080-pressure-chmi-hourly-2018-v1",
              "mode": "AGGREGATE_ONLY_NO_REPLACEMENT_VALUES",
              "method": "Exact UTC hours, CHMI quality 0, WH pressure transported from 425 m to station height using same-time outTemp; no fitted offset",
              "source_sql": "sql/readonly/pressure_wh1080_hourly_chmi_2018.sql",
              "chmi_manifest_sha256": manifest_sha, "counts": counts, "groups": groups,
              "limitations": ["CHMI station pressure and local 5-minute archive values have different temporal support.",
                              "outTemp approximates mean column temperature; 425 m is an owner-supplied elevation assumption.",
                              "A historical copy match is not independent physical validation.",
                              "This hourly result cannot validate five-minute restoration values.",
                              "No local SQL export or meteorological values are written by this script."]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "READ_ONLY_AGGREGATE_DONE", "counts": counts,
                      "groups": len(groups), "output": str(args.out)}))


if __name__ == "__main__":
    main()
