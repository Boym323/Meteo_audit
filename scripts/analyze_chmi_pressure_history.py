#!/usr/bin/env python3
"""Numerically compare Loucka archive pressure to official CHMI pressure.

All SQL is inside an explicit read-only transaction. Generated reports and
diagnostic exports are evidence only; no source values are written to SQL.
"""
from __future__ import annotations

import argparse
import configparser
import csv
import hashlib
import json
import math
import statistics
import zlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pymysql
from pymysql.cursors import DictCursor

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/chmi-pressure-2009-2026"
OUT = ROOT / "reports/parallel-audit/pressure-chmi-numeric-2009-2026"
MANIFEST = DATA / "manifest.json"
STATION_IDS = ("0-20000-0-11774", "0-20000-0-11782")
QUALITY_OK = {"0", "0.0"}
G = 9.80665
RD = 287.05


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantile(values, q):
    if not values:
        return None
    xs = sorted(values); p = (len(xs) - 1) * q; i = int(p); j = min(i + 1, len(xs) - 1)
    return xs[i] + (xs[j] - xs[i]) * (p - i)


def robust(values):
    if not values:
        return {"n": 0, "mean": None, "median": None, "mad": None, "sd": None, "p05": None, "p95": None}
    med = statistics.median(values)
    return {"n": len(values), "mean": statistics.fmean(values), "median": med,
            "mad": statistics.median(abs(x - med) for x in values),
            "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
            "p05": quantile(values, .05), "p95": quantile(values, .95)}


def load_reference():
    doc = json.loads(MANIFEST.read_text(encoding="utf-8")); hourly = defaultdict(dict); daily = defaultdict(dict)
    qc = Counter(); flags = Counter(); coverage = defaultdict(Counter); schemas = Counter(); errors = []
    for item in doc["items"]:
        if item.get("availability") != "available":
            continue
        # Manifest raw paths are relative to the cache root; docs are separate.
        path = DATA / "raw" / item["path"]
        if sha(path) != item["sha256"]:
            raise ValueError(f"SHA mismatch: {item['path']}")
        sid = item.get("station_id")
        if item["kind"] == "daily_csv":
            with path.open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f); schemas[str(reader.fieldnames)] += 1
                for row in reader:
                    if row.get("STATION") != sid or row.get("ELEMENT") != "P": continue
                    try: val = float(row["VALUE"])
                    except (ValueError, TypeError): val = None
                    func = str(row.get("TIMEFUNC", "")); key = (sid, row["DT"][:10], func); q = str(row.get("QUALITY", "")); flag = str(row.get("FLAG", ""))
                    qc[("daily", q)] += 1; flags[("daily", flag)] += 1; coverage[(sid, "daily")]["all"] += 1
                    daily[key]["P"] = {"value": val, "quality": q, "flag": flag, "timefunc": func, "dt": row.get("DT")}
        elif item["kind"] == "hourly_csv":
            with path.open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f); schemas[str(reader.fieldnames)] += 1
                for row in reader:
                    if row.get("STATION") != sid or row.get("ELEMENT") != item["element"]: continue
                    stamp = row["DT"]
                    if not stamp.endswith("Z"): errors.append({"file": item["path"], "dt": stamp, "error": "timestamp is not explicit UTC Z"}); continue
                    try: val = float(row["VALUE"])
                    except (ValueError, TypeError): val = None
                    key = (sid, stamp)
                    if item["element"] in hourly[key]: errors.append({"file": item["path"], "dt": stamp, "error": "duplicate station-element timestamp"})
                    hourly[key][item["element"]] = {"value": val, "quality": str(row.get("QUALITY", "")), "flag": str(row.get("FLAG", ""))}
                    qc[("hourly", str(row.get("QUALITY", "")))] += 1; flags[("hourly", str(row.get("FLAG", "")))] += 1
                    coverage[(sid, f"hourly_{item['element']}")][stamp[:7]] += 1
        elif item["kind"] in ("recent_json", "recent_daily_json"):
            raw = json.loads(path.read_text(encoding="utf-8")); values = raw["data"]["data"]["values"]
            schemas["recent_json:data.data.values[six-field tuple]"] += 1
            for r in values:
                if len(r) < 6 or r[0] != sid or r[1] not in ("P", "P_hm"): continue
                stamp = r[2]
                if not stamp.endswith("Z"): errors.append({"file": item["path"], "dt": stamp, "error": "timestamp is not explicit UTC Z"}); continue
                key = (sid, stamp)
                hourly[key][r[1]] = {"value": float(r[3]) if r[3] not in (None, "") else None, "flag": str(r[4] or ""), "quality": str(r[5])}
                qc[("recent", str(r[5]))] += 1; flags[("recent", str(r[4] or ""))] += 1
                coverage[(sid, f"recent_{r[1]}")][stamp[:7]] += 1
    return hourly, daily, {"quality_counts": {f"{a}:{b}": n for (a,b),n in sorted(qc.items())},
                           "flag_counts": {f"{a}:{b}": n for (a,b),n in sorted(flags.items())},
                           "schemas": dict(schemas), "parse_errors": errors,
                           "reference_coverage": {f"{s}:{e}": dict(c) for (s,e),c in sorted(coverage.items())}}


def connect_readonly(cnf_path: Path):
    parser = configparser.ConfigParser(); parser.read(cnf_path)
    section = parser["client"] if parser.has_section("client") else parser[parser.sections()[0]]
    conn = pymysql.connect(host=section.get("host", "localhost"), port=int(section.get("port", 3306)),
                           user=section.get("user"), password=section.get("password"), database="loucka_reconstruction",
                           cursorclass=DictCursor, connect_timeout=15, read_timeout=120, write_timeout=30, autocommit=False)
    cur = conn.cursor(); cur.execute("START TRANSACTION READ ONLY")
    cur.execute("SELECT @@hostname host, @@server_id server_id, CURRENT_USER() account"); identity = cur.fetchone()
    if identity["host"] != "lo-infra-db-mariadb01" or identity["server_id"] != 1:
        conn.rollback(); conn.close(); raise RuntimeError("Unexpected database identity")
    cur.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",("loucka_reconstruction","archive"))
    cols = {r["COLUMN_NAME"] for r in cur.fetchall()}
    wanted = [x for x in ("dateTime", "usUnits", "interval", "pressure", "barometer", "outTemp", "inTemp") if x in cols]
    if "dateTime" not in wanted or "pressure" not in wanted or "barometer" not in wanted:
        raise RuntimeError("Required archive columns absent")
    sql = "SELECT " + ",".join(f"`{c}`" for c in wanted) + " FROM loucka_reconstruction.archive WHERE dateTime >= 1230768000 AND dateTime < 1798761600 ORDER BY dateTime"
    cur.execute(sql); rows = cur.fetchall()
    conn.rollback(); conn.close()
    return identity, wanted, rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cnf",type=Path,required=True,help="path to an already-existing SELECT-only MySQL client file; contents are never printed")
    args=parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    hourly, daily, ref_stats = load_reference()
    identity, columns, rows = connect_readonly(args.cnf)
    local = {}
    for r in rows:
        ts = int(r["dateTime"]); dt = datetime.fromtimestamp(ts, timezone.utc)
        local[ts] = {**r, "utc": dt.isoformat().replace("+00:00", "Z"), "year": dt.year, "month": dt.month}
    # Exact UTC hourly matches to station P and sea-level P_hm.
    pair_rows = []
    for (sid, stamp), elems in hourly.items():
        try: dt = datetime.fromisoformat(stamp.replace("Z", "+00:00")); ts = int(dt.timestamp())
        except ValueError: continue
        if ts not in local: continue
        l = local[ts]
        for el, item in elems.items():
            if item["quality"] not in QUALITY_OK or item["value"] is None: continue
            if el not in ("P", "P_hm"): continue
            for field in ("pressure", "barometer"):
                value = l.get(field)
                if value is not None:
                    pair_rows.append({"timestamp_utc": stamp, "year": l["year"], "month": l["month"], "station_id": sid,
                                      "chmi_element": el, "chmi_hpa": float(item["value"]), "loucka_field": field,
                                      "loucka_value": float(value), "loucka_minus_chmi_hpa": float(value)-float(item["value"]),
                                      "quality": item["quality"], "flag": item["flag"], "outTemp_c": l.get("outTemp")})
    # Pair rows are only held in memory for robust summaries; never persist
    # row-level target SQL measurements in the repository.
    # Daily trend summaries: compare robust monthly medians after temporal averaging,
    # with separate fields and no naive same-day instant pairing.
    daily_series = defaultdict(list)
    for (sid, day, func), elems in daily.items():
        item = elems.get("P")
        if not item or item["quality"] not in QUALITY_OK or item["value"] is None: continue
        daily_series[(sid, day[:4], day[5:7], func)].append((day, item["value"], item["quality"], item["flag"], item["timefunc"]))
    # hourly exact-match statistics by calendar year/station/element/Loucka field
    stats = defaultdict(list)
    corrected_station = defaultdict(list)
    monthly_stats = defaultdict(list)
    for r in pair_rows:
        stats[(r["year"], r["station_id"], r["chmi_element"], r["loucka_field"])].append(r["loucka_minus_chmi_hpa"])
        monthly_stats[(r["year"], r["month"], r["station_id"], r["chmi_element"], r["loucka_field"])].append(r["loucka_minus_chmi_hpa"])
        if r["chmi_element"] == "P" and r["loucka_field"] == "pressure" and r["outTemp_c"] is not None:
            elev = 222.25 if r["station_id"].endswith("11774") else 252.8
            dz = 425.0 - elev
            tk = float(r["outTemp_c"]) + 273.15
            adjusted = r["loucka_value"] * math.exp(G * dz / (RD * tk))
            corrected_station[(r["year"], r["station_id"])].append(adjusted - r["chmi_hpa"])
    year_rows=[]
    for key, diffs in sorted(stats.items()):
        d=robust(diffs);year_rows.append({"utc_year":key[0],"station_id":key[1],"element":key[2],"loucka_field":key[3],**d})
    with (OUT/"hourly_annual_stats.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(year_rows[0]) if year_rows else ["utc_year"]);w.writeheader();w.writerows(year_rows)
    month_rows=[]
    for key,diffs in sorted(monthly_stats.items()):
        d=robust(diffs); month_rows.append({"utc_year":key[0],"month":key[1],"station_id":key[2],"element":key[3],"loucka_field":key[4],**d})
    with (OUT/"hourly_monthly_stats.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(month_rows[0]) if month_rows else ["utc_year"]);w.writeheader();w.writerows(month_rows)
    corrected_rows=[]
    for key,vals in sorted(corrected_station.items()):
        corrected_rows.append({"utc_year":key[0],"station_id":key[1],**robust(vals),"method":"P station-pressure comparison; pressure transported from Loucka 425 m to time-valid CHMI station elevation with exp(g*dz/(Rd*T_out)); diagnostic model"})
    with (OUT/"hourly_station_pressure_height_adjusted.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(corrected_rows[0]) if corrected_rows else ["utc_year"]);w.writeheader();w.writerows(corrected_rows)
    # Daily station pressure monthly median diagnostics for 2009-2017 (not exact UTC pairing).
    drows=[]
    for (sid, year, month, func), vals in sorted(daily_series.items()):
        drows.append({"utc_label_year":year,"month":month,"station_id":sid,"timefunc":func,"n_daily":len(vals),"quality_zero":sum(x[2] in QUALITY_OK for x in vals),
                      "median_P_hpa":statistics.median(x[1] for x in vals if x[1] is not None and x[2] in QUALITY_OK) if any(x[1] is not None and x[2] in QUALITY_OK for x in vals) else None,
                      "timefunc_counts":json.dumps(dict(Counter(x[4] for x in vals)),ensure_ascii=False),
                      "first_date":min(x[0] for x in vals),"last_date":max(x[0] for x in vals)})
    with (OUT/"daily_monthly_stats.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(drows[0]) if drows else ["utc_label_year"]);w.writeheader();w.writerows(drows)
    # Aggregate monthly target archive pressure coverage by UTC year/month.
    target_month = defaultdict(lambda: {"counts": Counter(), "pressure": [], "barometer": [], "outTemp": []})
    for r in rows:
        ts=int(r["dateTime"]); dt=datetime.fromtimestamp(ts,timezone.utc); m=target_month[(dt.year,dt.month)]; c=m["counts"]
        c["rows"] += 1
        for field in ("pressure","barometer"):
            c[field+"_valid"] += r.get(field) is not None
            c[field+"_null"] += r.get(field) is None
            if r.get(field) is not None:m[field].append(float(r[field]))
        if r.get("outTemp") is not None:m["outTemp"].append(float(r["outTemp"]))
        c["usUnits_"+str(r.get("usUnits"))] += 1
    with (OUT/"loucka_monthly_coverage.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["utc_year","month","archive_rows","pressure_valid","pressure_null","barometer_valid","barometer_null","usUnits_counts"]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for (year,month),m in sorted(target_month.items()):
            c=m["counts"]
            w.writerow({"utc_year":year,"month":month,"archive_rows":c["rows"],"pressure_valid":c["pressure_valid"],"pressure_null":c["pressure_null"],"barometer_valid":c["barometer_valid"],"barometer_null":c["barometer_null"],"usUnits_counts":json.dumps({k[8:]:v for k,v in c.items() if k.startswith("usUnits_")},sort_keys=True)})
    # Coarse monthly context for years without hourly SYNOP references.
    # Daily AVG dates are kept as source labels; no exact UTC-day alignment is claimed.
    daily_avg = defaultdict(list)
    for (sid, day, func), elems in daily.items():
        item=elems.get("P")
        if func=="AVG" and item and item["quality"] in QUALITY_OK and item["value"] is not None:
            daily_avg[(sid,int(day[:4]),int(day[5:7]))].append(float(item["value"]))
    coarse=[]
    for (sid,year,month), vals in sorted(daily_avg.items()):
        lm=target_month.get((year,month))
        if not lm:continue
        pmed=statistics.median(lm["pressure"]) if lm["pressure"] else None
        bmed=statistics.median(lm["barometer"]) if lm["barometer"] else None
        tmed=statistics.median(lm["outTemp"]) if lm["outTemp"] else 15.0
        station_h=222.25 if sid.endswith("11774") else 252.8
        dz=425.0-station_h; corr=math.exp(G*dz/(RD*(tmed+273.15)))
        chmi=statistics.median(vals)
        coarse.append({"year":year,"month":month,"station_id":sid,"chmi_daily_avg_rows":len(vals),"chmi_P_daily_avg_median_hpa":chmi,
                       "loucka_archive_rows":lm["counts"]["rows"],"loucka_pressure_median_hpa":pmed,"loucka_barometer_median_hpa":bmed,
                       "pressure_transported_to_station_height_median_hpa":pmed*corr if pmed is not None else None,
                       "height_adjusted_pressure_minus_chmi_P_hpa":pmed*corr-chmi if pmed is not None else None,
                       "barometer_minus_chmi_station_P_hpa":bmed-chmi if bmed is not None else None,
                       "temperature_used_c":tmed,"status":"coarse monthly context only; daily TIMEFUNC=AVG source support is not exact UTC archive-day support"})
    with (OUT/"daily_chmi_monthly_context.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(coarse[0]) if coarse else ["year"]);w.writeheader();w.writerows(coarse)
    doc={"schema":"loucka-pressure-chmi-numeric-validation-v1","created_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"),
         "database_identity":identity,"database_query":"One START TRANSACTION READ ONLY; SELECT archive dateTime/usUnits/interval/pressure/barometer/outTemp/inTemp over [2009-01-01,2027-01-01). No other archive/database inventory repeated.",
         "database_rows":len(rows),"database_columns":columns,
         "reference_manifest_sha256":sha(MANIFEST),"yearly_stats_csv_sha256":sha(OUT/"hourly_annual_stats.csv"),"monthly_stats_csv_sha256":sha(OUT/"hourly_monthly_stats.csv"),"height_adjusted_csv_sha256":sha(OUT/"hourly_station_pressure_height_adjusted.csv"),"coarse_daily_context_sha256":sha(OUT/"daily_chmi_monthly_context.csv"),
         "reference_parse":ref_stats,"hourly_pair_rows":len(pair_rows),"hourly_statistics_groups":len(year_rows),"hourly_monthly_statistics_groups":len(month_rows),"daily_month_groups":len(drows),"coarse_daily_monthly_groups":len(coarse),
         "methods":{"timestamp":"Exact matching of explicit UTC Z hourly timestamps; archive dateTime interpreted Unix UTC.","hourly_quality":"Only CHMI QUALITY 0/0.0 enters numeric comparisons; flags retained and distributions reported.",
                    "field_semantics":"Loucka pressure treated as site pressure and barometer as sea-level reduced only as hypotheses; no relabeling. CHMI P is station pressure; P_hm is reduced pressure.",
                    "elevation":"Loucka site 425m per task; station elevation/coordinates taken from time-valid official meta1 JSON. Difference between station pressures is not treated as calibration error.",
                    "station_pressure_height_model":"Only diagnostic: P adjusted from Loucka 425m to CHMI station height using observed Loucka outTemp as a representative column temperature and dry-air hypsometric equation; it is not an independent measurement or replacement candidate.",
                    "limitations":"No hourly CHMI before 2018. Daily CSV has a different temporal support and TIMEFUNC; annual daily comparisons are trend context only, never exact-hour pairs."}}
    (OUT/"analysis.json").write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"rows":len(rows),"hourly_pairs":len(pair_rows),"stats_groups":len(year_rows),"daily_month_groups":len(drows),"db":identity},indent=2))


if __name__=="__main__": main()
