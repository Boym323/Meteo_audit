#!/usr/bin/env python3
"""2018 WH1080 source-vs-CHMI pressure diagnostic, SELECT-only.

Uses the pre-downloaded and SHA-256-verified ČHMÚ CSV reference files
from PR #89. Computes only aggregate diagnostics; NEVER proposes or
writes replacement values to a database.
"""
from __future__ import annotations

import argparse
import configparser
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/chmi-pressure-2009-2026"
OUT = ROOT / "reports/parallel-audit/pressure-wh1080-chmi-pilot-2018"
IDS = ("0-20000-0-11774", "0-20000-0-11782")
STATION_HEIGHT = {"0-20000-0-11774": 222.25, "0-20000-0-11782": 252.8}
G = 9.80665
RD = 287.05
START_2018 = 1514764800
END_2018 = 1546300800


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_chmi_2018(manifest_path: Path = DATA / "manifest.json", raw_root: Path = DATA / "raw") -> dict:
    """Read official hourly P and P_hm, fail-closed on missing/mismatched caches."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = [i for i in manifest["items"] if i.get("kind") == "hourly_csv"
             and str(i.get("period", "")).startswith("2018-")
             and i.get("station_id") in IDS and i.get("element") in ("P", "P_hm")]
    expected = {(sid, element, month) for sid in IDS for element in ("P", "P_hm") for month in range(1, 13)}
    included = {(i["station_id"], i["element"], int(i["period"][-2:])) for i in items
                if i.get("availability") == "available"}
    if included != expected:
        raise ValueError(f"2018 reference coverage incomplete: {len(included)}/{len(expected)} datasets")
    refs = defaultdict(dict)
    counts = Counter()
    for item in items:
        if item.get("availability") != "available":
            continue
        path = raw_root / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise ValueError(f"Missing or SHA256-mismatched ČHMÚ file: {item['path']}")
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"STATION", "ELEMENT", "DT", "VALUE", "FLAG", "QUALITY"}
            if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
                raise ValueError(f"Unexpected ČHMÚ CSV schema: {item['path']}")
            for row in reader:
                if row["STATION"] != item["station_id"] or row["ELEMENT"] != item["element"]:
                    raise ValueError(f"Unexpected station/element in {item['path']}")
                stamp = row["DT"]
                if not stamp.endswith("Z"):
                    raise ValueError(f"Reference is not explicitly UTC Z: {stamp}")
                dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                if dt.year != 2018:
                    raise ValueError(f"Unexpected year in reference: {stamp}")
                value = row["VALUE"]
                quality = str(row["QUALITY"])
                counts[f"{item['element']}:{quality}"] += 1
                if quality not in ("0", "0.0") or not value:
                    continue
                key = (item["station_id"], int(dt.timestamp()))
                if item["element"] in refs[key]:
                    raise ValueError(f"Duplicate good-quality hour: {key} {item['element']}")
                refs[key][item["element"]] = float(value)
    return {"references": refs, "quality_counts": dict(counts), "reference_manifest_sha256": sha256(manifest_path)}


def to_other_elevation(pressure_hpa: float, out_temp_c: float, dest_height_m: float) -> float:
    """Diagnostic dry-air hydrostatic transport from Loučka 425 m."""
    if not -80 <= out_temp_c <= 60:
        raise ValueError("Temperature outside validation envelope")
    return pressure_hpa * math.exp(G * (425.0 - dest_height_m) / (RD * (out_temp_c + 273.15)))


def prepare_comparisons(rows: list[dict], refs: dict) -> tuple[list[dict], dict]:
    """Compute independent comparisons, never replacement values."""
    measurements = []
    counts = Counter()
    for r in rows:
        ts = int(r["dateTime"])
        if not (START_2018 <= ts < END_2018 and ts % 3600 == 0):
            raise ValueError(f"Not an exact 2018 UTC hour: {ts}")
        if int(r["usUnits"]) != 16 or int(r["wh_usUnits"]) != 17:
            raise ValueError(f"Unexpected WeeWX target/source units at {ts}")
        wh = r["wh_pressure"]
        if wh is None or not 850 < float(wh) < 1100:
            raise ValueError(f"Invalid WH source pressure at {ts}")
        bucket = "target_pressure_NULL" if r["pressure"] is None else "target_pressure_present"
        counts[bucket] += 1
        month = datetime.fromtimestamp(ts, timezone.utc).month
        for sid in IDS:
            refer = refs.get((sid, ts), {})
            base = {"utc_year": 2018, "month": month, "station_id": sid, "bucket": bucket}
            if refer.get("P") is not None and r["outTemp"] is not None:
                transported_wh = to_other_elevation(float(wh), float(r["outTemp"]), STATION_HEIGHT[sid])
                measurements.append({**base, "metric": "WH_pressure_height_adjusted_minus_CHMI_P",
                                     "difference_hpa": transported_wh - refer["P"]})
                if r["pressure"] is not None:
                    transported_target = to_other_elevation(float(r["pressure"]), float(r["outTemp"]), STATION_HEIGHT[sid])
                    measurements.append({**base, "metric": "target_pressure_height_adjusted_minus_CHMI_P",
                                         "difference_hpa": transported_target - refer["P"]})
            if refer.get("P_hm") is not None and r["barometer"] is not None:
                measurements.append({**base, "metric": "target_barometer_minus_CHMI_P_hm",
                                     "difference_hpa": float(r["barometer"]) - refer["P_hm"]})
        if r["pressure"] is not None:
            measurements.append({"utc_year": 2018, "month": month, "station_id": "LOCAL",
                                 "bucket": bucket, "metric": "WH_minus_target_pressure",
                                 "difference_hpa": float(wh) - float(r["pressure"])})
    return measurements, dict(counts)


def robust(values: list[float]) -> dict:
    m = statistics.median(values)
    xs = sorted(values)
    def quantile(q):
        p = (len(xs)-1)*q
        i = int(p)
        return xs[i]+(xs[min(i+1,len(xs)-1)]-xs[i])*(p-i)
    return {"n": len(values), "median_hpa": m,
            "mad_hpa": statistics.median(abs(x-m) for x in values),
            "mean_hpa": statistics.fmean(values),
            "p05_hpa": quantile(0.05), "p95_hpa": quantile(0.95)}


def group_statistics(measurements: list[dict], monthly: bool) -> list[dict]:
    vals = defaultdict(list)
    for r in measurements:
        key = (r["utc_year"],r["month"] if monthly else 0,r["station_id"],r["bucket"],r["metric"])
        vals[key].append(r["difference_hpa"])
    return [dict(utc_year=k[0],month=k[1],station_id=k[2],bucket=k[3],metric=k[4],**robust(v))
            for k,v in sorted(vals.items())]


def collect_rows(cnf: Path) -> tuple[list[dict], dict]:
    import pymysql
    from pymysql.cursors import DictCursor
    cfg = configparser.ConfigParser()
    if not cfg.read(cnf):
        raise ValueError("Existing readonly cnf not found")
    section = cfg["client"] if cfg.has_section("client") else cfg[cfg.sections()[0]]
    if section.get("user") != "loucka_web_ro":
        raise PermissionError("This audit must use only the existing low-privilege loucka_web_ro SQL account")
    conn = pymysql.connect(host=section.get("host"),port=int(section.get("port",3306)),user=section.get("user"),
                           password=section.get("password"),database="loucka_reconstruction",
                           cursorclass=DictCursor,autocommit=False,connect_timeout=15,read_timeout=120)
    try:
        with conn.cursor() as c:
            c.execute("START TRANSACTION READ ONLY")
            c.execute("SELECT @@hostname AS host, @@server_id AS server_id, CURRENT_USER() AS account")
            identity = c.fetchone()
            if (identity["host"] != "lo-infra-db-mariadb01" or int(identity["server_id"]) != 1
                    or identity["account"] != "loucka_web_ro@192.168.0.131"):
                raise RuntimeError("Unexpected database server/account identity")
            c.execute("""SELECT r.dateTime, r.usUnits, r.pressure, r.barometer, r.outTemp,
                               w.usUnits AS wh_usUnits, w.pressure AS wh_pressure
                        FROM loucka_reconstruction.archive AS r
                        INNER JOIN weewx_WH1080.archive AS w ON w.dateTime=r.dateTime
                        WHERE r.dateTime >= %s AND r.dateTime < %s
                          AND MOD(r.dateTime,3600)=0 AND w.pressure IS NOT NULL
                        ORDER BY r.dateTime""",(START_2018,END_2018))
            rows = c.fetchall()
            return rows, identity
    finally:
        conn.rollback()
        conn.close()


def save_csv(path: Path, records: list[dict]):
    if not records:
        raise ValueError("No comparison statistics to save")
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cnf",required=True,type=Path,help="existing loucka_web_ro cnf; never logged")
    args=ap.parse_args()
    source = load_chmi_2018()
    rows, identity = collect_rows(args.cnf)
    observations,buckets=prepare_comparisons(rows,source["references"])
    if buckets.get("target_pressure_NULL",0)<100 or len(observations)<100:
        raise RuntimeError("Insufficient source coverage; no output generated")
    annual=group_statistics(observations,monthly=False)
    monthly=group_statistics(observations,monthly=True)
    OUT.mkdir(parents=True,exist_ok=True)
    save_csv(OUT/"wh_chmi_annual_groups.csv",annual)
    save_csv(OUT/"wh_chmi_monthly_groups.csv",monthly)
    info={"schema":"wh1080-chmi-pressure-2018-source-comparison-v1", "created_at_utc":datetime.now(timezone.utc).isoformat(),
          "mode":"READ_ONLY_SOURCE_DIAGNOSTICS_NO_APPROVED_REPLACEMENTS",
          "year":2018,"database_identity":identity,"source_rows":len(rows),"target_buckets":buckets,
          "chmi_manifest_sha256":source["reference_manifest_sha256"],"chmi_quality_counts":source["quality_counts"],
          "comparison_points":len(observations),"annual_groups":len(annual),"monthly_groups":len(monthly),
          "interpretation":"WH source is not independently validated by old_weewx duplication; compare with CHMI P and P_hm with altitude adjustment. This is NOT a per-field write manifest.",
          "caveats":["Hourly SYNOP and WeeWX 5-min point have different temporal support",
                     "Dry-air altitude transport uses contemporaneous local outTemp; not calibration ground truth",
                     "Historical GW1000-named archive is not an independent GW1000 hardware source before its installation",
                     "Protected Q1 2018 and production archive untouched; no SQL writes"]}
    (OUT/"evidence.json").write_text(json.dumps(info,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"READ_ONLY_DONE","groups":len(monthly),"source_rows":len(rows),
                      "target_buckets":buckets,"annual_stats":annual,
                      "out_dir":str(OUT)},indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
