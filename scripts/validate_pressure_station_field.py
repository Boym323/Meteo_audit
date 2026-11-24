#!/usr/bin/env python3
"""Read-only physical comparison of Loucka station pressure with CHMI station P."""
from __future__ import annotations

import argparse
import configparser
import csv
import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

G = 9.80665
RD = 287.05
QUALITY_OK = {"0", "0.0"}
STATIONS = {"H": ("0-20000-0-11774", 222.25), "M": ("0-20000-0-11782", 252.8)}


def transport_station_pressure(pressure_hpa: float, out_temp_c: float, target_height_m: float,
                               site_height_m: float = 425.0) -> float:
    """Dry-air hypsometric transport; diagnostic only, not a calibration."""
    if not math.isfinite(pressure_hpa) or pressure_hpa <= 0:
        raise ValueError("pressure must be finite and positive")
    if not -80 <= out_temp_c <= 60:
        raise ValueError("outTemp outside physical input envelope")
    return pressure_hpa * math.exp(G * (site_height_m - target_height_m) /
                                   (RD * (out_temp_c + 273.15)))


def quantile(values, p):
    xs = sorted(values)
    if not xs:
        return None
    x = (len(xs) - 1) * p
    i = int(x)
    return xs[i] + (xs[min(i + 1, len(xs) - 1)] - xs[i]) * (x - i)


def metrics(errors):
    if not errors:
        return {"n": 0, "mae_hpa": None, "median_bias_hpa": None, "mad_hpa": None,
                "p95_abs_error_hpa": None}
    bias = statistics.median(errors)
    return {"n": len(errors), "mae_hpa": statistics.fmean(abs(x) for x in errors),
            "median_bias_hpa": bias, "mad_hpa": statistics.median(abs(x - bias) for x in errors),
            "p95_abs_error_hpa": quantile([abs(x) for x in errors], .95)}


def block_bootstrap_ci(month_errors, seed=26024, replicates=2000):
    """95% percentile interval for MAE, resampling whole UTC months, not rows."""
    keys = sorted(month_errors)
    if len(keys) < 3:
        return {"low_hpa": None, "high_hpa": None, "blocks": len(keys), "replicates": 0}
    rng = random.Random(seed)
    vals = []
    for _ in range(replicates):
        picked = [rng.choice(keys) for _ in keys]
        sample = [abs(e) for key in picked for e in month_errors[key]]
        vals.append(statistics.fmean(sample))
    return {"low_hpa": quantile(vals, .025), "high_hpa": quantile(vals, .975),
            "blocks": len(keys), "replicates": replicates, "block_unit": "UTC calendar month"}


def load_chmi(cache):
    manifest = json.loads((cache / "manifest.json").read_text(encoding="utf-8"))
    hourly = {}
    verified = 0
    for item in manifest["items"]:
        if item.get("availability") != "available" or item.get("kind") != "hourly_csv" or item.get("element") != "P":
            continue
        if item.get("station_id") not in {v[0] for v in STATIONS.values()}:
            continue
        path = cache / "raw" / item["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"ČHMÚ SHA-256 mismatch: {item['path']}")
        verified += 1
        with path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row["STATION"] != item["station_id"] or row["ELEMENT"] != "P":
                    raise ValueError(f"ČHMÚ source mismatch: {item['path']}")
                if row["QUALITY"] not in QUALITY_OK or not row["VALUE"]:
                    continue
                stamp = row["DT"]
                if not stamp.endswith("Z"):
                    raise ValueError("ČHMÚ hourly timestamp must be explicit UTC")
                ts = int(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp())
                key = (row["STATION"], ts)
                if key in hourly:
                    raise ValueError(f"Duplicate ČHMÚ station-hour {key}")
                hourly[key] = float(row["VALUE"])
    if verified < 48:
        raise ValueError(f"Incomplete hourly P reference files: {verified}")
    return hourly, {"files_sha256_verified": verified,
                    "manifest_sha256": hashlib.sha256((cache / "manifest.json").read_bytes()).hexdigest(),
                    "valid_station_hour_values": len(hourly)}


def load_local(cnf):
    import pymysql
    from pymysql.cursors import DictCursor
    cfg = configparser.ConfigParser()
    if not cfg.read(cnf):
        raise ValueError("Existing read-only SQL client config not found")
    section = cfg["client"] if cfg.has_section("client") else cfg[cfg.sections()[0]]
    if section.get("user") != "loucka_web_ro":
        raise PermissionError("Use only the existing loucka_web_ro account")
    conn = pymysql.connect(host=section.get("host"), port=int(section.get("port", 3306)),
                           user=section.get("user"), password=section.get("password"),
                           database="loucka_reconstruction", cursorclass=DictCursor,
                           autocommit=False, connect_timeout=15, read_timeout=120)
    try:
        with conn.cursor() as cur:
            cur.execute("START TRANSACTION READ ONLY")
            cur.execute("SELECT @@hostname host, @@server_id server_id, CURRENT_USER() account")
            identity = cur.fetchone()
            if (identity["host"], int(identity["server_id"]), identity["account"]) != (
                    "lo-infra-db-mariadb01", 1, "loucka_web_ro@192.168.0.131"):
                raise RuntimeError("Unexpected database identity")
            cur.execute("""SELECT `dateTime`, `usUnits`, `pressure`, `outTemp`
                           FROM `loucka_reconstruction`.`archive`
                           WHERE `dateTime` >= 1514764800 AND `dateTime` < 1735689600
                             AND MOD(`dateTime`,3600)=0 AND `pressure` IS NOT NULL
                           ORDER BY `dateTime`""")
            rows = cur.fetchall()
            if any(int(r["usUnits"]) != 16 for r in rows):
                raise ValueError("Unexpected target usUnits")
            return {int(r["dateTime"]): (float(r["pressure"]),
                                          float(r["outTemp"]) if r["outTemp"] is not None else None)
                    for r in rows}, identity
    finally:
        conn.rollback()
        conn.close()


def evaluate(reference, local):
    groups = defaultdict(lambda: {"raw": [], "transported": [], "months": defaultdict(list),
                                  "ref_slots": 0, "local_pressure_slots": 0})
    refs_by_year = defaultdict(int)
    local_by_year = defaultdict(int)
    for (sid, ts), p_ref in reference.items():
        year = datetime.fromtimestamp(ts, timezone.utc).year
        if not 2018 <= year <= 2024:
            continue
        refs_by_year[(sid, year)] += 1
        group = groups[(sid, year)]
        group["ref_slots"] += 1
        row = local.get(ts)
        if row is None:
            continue
        p_local, temp = row
        local_by_year[(sid, year)] += 1
        group["local_pressure_slots"] += 1
        error = p_local - p_ref
        group["raw"].append(error)
        if temp is not None:
            adjusted = transport_station_pressure(p_local, temp, STATIONS["H" if sid.endswith("11774") else "M"][1])
            adj_error = adjusted - p_ref
            group["transported"].append(adj_error)
            group["months"][datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")].append(adj_error)
    results = []
    for (sid, year), group in sorted(groups.items()):
        station = "H" if sid.endswith("11774") else "M"
        expected = 8784 if year % 4 == 0 else 8760
        results.append({"year": year, "station": station, "reference_valid_hours": group["ref_slots"],
                        "matched_pressure_hours": group["local_pressure_slots"],
                        "coverage_of_valid_reference": group["local_pressure_slots"] / group["ref_slots"] if group["ref_slots"] else 0,
                        "coverage_of_expected_hours": group["local_pressure_slots"] / expected,
                        "raw_pressure_minus_CHMI_P": metrics(group["raw"]),
                        "hypsometric_pressure_minus_CHMI_P": metrics(group["transported"]),
                        "hypsometric_MAE_95pct_month_block_CI": block_bootstrap_ci(group["months"]),
                        "method": "fixed dry-air hypsometric transport from 425 m using same-timestamp outTemp; diagnostic only"})
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cnf", required=True, type=Path)
    ap.add_argument("--chmi-cache", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    reference, ref_meta = load_chmi(args.chmi_cache)
    local, identity = load_local(args.cnf)
    result = {"schema": "loucka-pressure-station-field-validation-v1",
              "state": "READ_ONLY_DIAGNOSTIC_NO_APPROVED_REPLACEMENTS",
              "database_identity": identity, "local_hourly_pressure_rows": len(local),
              "reference": ref_meta, "results": evaluate(reference, local),
              "limitations": ["Exact UTC hour equality does not establish identical temporal support.",
                              "Loucka height 425 m is an input assumption; local sensor height/config history is not independently dated.",
                              "Temperature is a proxy for mean hydrostatic column temperature.",
                              "Station separation and reference measurement uncertainty remain in residuals.",
                              "No interpolation or 5-minute restoration accuracy is inferred.",
                              "Only the working archive was readable; this does not validate WH1080 candidates.",
                              "One read-only SQL transaction; no DML or DDL."]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "READ_ONLY_DONE", "local_hours": len(local),
                      "reference_hours": ref_meta["valid_station_hour_values"],
                      "result_groups": len(result["results"]), "output": str(args.out)}))


if __name__ == "__main__":
    main()
