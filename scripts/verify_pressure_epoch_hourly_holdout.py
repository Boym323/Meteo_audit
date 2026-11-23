#!/usr/bin/env python3
"""Validate frozen monthly epoch models against independently held-out CHMI hourly records.

The models are fitted and selected in the committed JSON from the monthly
backtest. This script does NOT refit, optimize, or inspect holdout labels
when choosing a model. It only evaluates each frozen model at exact UTC
CHMI synoptic hours and same-timestamp archive barometer.

DB: one START TRANSACTION READ ONLY, no DML or DDL, no new users.
All output is aggregate evidence, not a pressure replacement manifest.
"""
from __future__ import annotations

import argparse
import configparser
import csv
import hashlib
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


QUALITY_OK = {"0", "0.0"}
STATIONS = {"H": "0-20000-0-11774", "M": "0-20000-0-11782"}
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "reports/parallel-audit/pressure-epoch-monthly-holdout-20261123.json"


def med(xs):
    if not xs:
        raise ValueError("No observations")
    return statistics.median(xs)


def q(xs, p):
    if not xs:
        raise ValueError("No observations")
    a = sorted(xs)
    idx = (len(a) - 1) * p
    i = int(idx)
    return a[i] + (a[min(i + 1, len(a) - 1)] - a[i]) * (idx - i)


def summary(xs):
    if not xs:
        return {"n": 0, "mae": None, "median_bias": None, "mad": None, "p95_abs": None}
    m = med(xs)
    a = [abs(x) for x in xs]
    return {
        "n": len(xs),
        "mae": statistics.fmean(a),
        "median_bias": m,
        "mad": med([abs(x - m) for x in xs]),
        "p95_abs": q(a, .95),
    }


def ts_epoch(stamp):
    if not stamp.endswith("Z"):
        raise ValueError("CHMI timestamp missing explicit UTC Z")
    dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if dt.utcoffset().total_seconds() != 0:
        raise ValueError("non-UTC reference")
    return int(dt.timestamp())


def month(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")


def month_x(ts):
    dt = datetime.fromtimestamp(ts, timezone.utc)
    return (dt.year - 2000) * 12 + (dt.month - 1)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_chmi_hourly(cache):
    """Read only original P_hm hourly (historic or recent); verify manifest SHA for each file."""
    manifest_path = cache / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    hours = {}
    quality = defaultdict(int)
    files = 0
    for item in manifest["items"]:
        if item.get("availability") != "available":
            continue
        if item.get("kind") not in ("hourly_csv", "recent_json", "recent_daily_json"):
            continue
        # Historic CSV has one ELEMENT per file; recent JSON contains multiple
        # elements inside data.data.values and manifest.element is null.
        if item["kind"] == "hourly_csv" and item.get("element") != "P_hm":
            continue
        sid = item.get("station_id")
        if sid not in STATIONS.values():
            continue
        path = cache / "raw" / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise ValueError("CHMI cache missing or failed SHA256: " + item["path"])
        files += 1
        if item["kind"] == "hourly_csv":
            with path.open(encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                expected = {"STATION", "ELEMENT", "DT", "VALUE", "QUALITY"}
                if not reader.fieldnames or not expected.issubset(reader.fieldnames):
                    raise ValueError("Unexpected CHMI hourly CSV schema")
                records = ((r["STATION"], r["ELEMENT"], r["DT"], r["VALUE"], r["QUALITY"]) for r in reader)
                for station, element, dt, value, code in records:
                    if station != sid or element != "P_hm":
                        raise ValueError("Source mismatch in " + item["path"])
                    quality[str(code)] += 1
                    if str(code) not in QUALITY_OK or not value:
                        continue
                    k = (station, ts_epoch(dt))
                    if k in hours:
                        raise ValueError("Duplicate CHMI station-hour")
                    hours[k] = float(value)
        else:
            raw = json.loads(path.read_text(encoding="utf-8"))
            values = raw["data"]["data"]["values"]
            for row in values:
                if len(row) < 6:
                    raise ValueError("Unexpected CHMI recent JSON tuple")
                station, element, dt, value, flag, code = row[:6]
                if station != sid or element != "P_hm":
                    continue
                quality[str(code)] += 1
                if str(code) not in QUALITY_OK or value is None or value == "":
                    continue
                k = (station, ts_epoch(dt))
                if k in hours:
                    raise ValueError("Duplicate CHMI station-hour")
                hours[k] = float(value)
    if files < 48:
        raise ValueError("Incomplete P_hm reference coverage; no evaluation")
    return hours, {"files_verified_sha256": files, "reference_manifest_sha256": sha256(manifest_path),
                   "quality_counts": dict(quality), "valid_station_hour_values": len(hours)}


def load_site_hours(cnf):
    import pymysql
    from pymysql.cursors import DictCursor
    config = configparser.ConfigParser()
    if not config.read(cnf):
        raise ValueError("Existing read-only config file not available")
    section = config["client"] if config.has_section("client") else config[config.sections()[0]]
    if section.get("user") != "loucka_web_ro":
        raise PermissionError("Only existing loucka_web_ro is permitted")
    conn = pymysql.connect(host=section.get("host"), port=int(section.get("port", 3306)),
                           user=section.get("user"), password=section.get("password"),
                           database="loucka_reconstruction", cursorclass=DictCursor,
                           autocommit=False, connect_timeout=15, read_timeout=120)
    try:
        with conn.cursor() as cur:
            cur.execute("START TRANSACTION READ ONLY")
            cur.execute("SELECT @@hostname AS host, @@server_id AS server_id, CURRENT_USER() AS account")
            identity = cur.fetchone()
            if (identity["host"] != "lo-infra-db-mariadb01" or int(identity["server_id"]) != 1
                or identity["account"] != "loucka_web_ro@192.168.0.131"):
                raise RuntimeError("Unexpected SQL server or user identity")
            cur.execute("""
                SELECT dateTime, usUnits, barometer
                FROM loucka_reconstruction.archive
                WHERE dateTime >= 1514764800 AND dateTime < 1796083200
                  AND MOD(dateTime,3600)=0 AND barometer IS NOT NULL
                ORDER BY dateTime
            """)
            rows = cur.fetchall()
            result = {}
            for row in rows:
                if int(row["usUnits"]) != 16:
                    raise ValueError("Unexpected archive usUnits")
                result[int(row["dateTime"])] = float(row["barometer"])
        return result, identity
    finally:
        conn.rollback()
        conn.close()


def predict(params, ts):
    return float(params["intercept"]) + float(params["slope"]) * month_x(ts)


def hourly_backtest(model, reference, site):
    """Never train or select on hourly holdouts; use frozen parameters only."""
    if model["schema"] != "loucka-pressure-monthly-calibration-backtest-v1":
        raise ValueError("Unrecognized frozen monthly model")
    out = []
    for e in model["epochs"]:
        if e["type"] != "hourly" or "splits" not in e:
            continue
        hstart, hend = e["splits"]["holdout"]
        for training in ("H", "M"):
            chosen = e["references"][training]["selected"]
            params = e["references"][training]["models"][chosen]["parameters"]
            for target in ("H", "M"):
                before, after = [], []
                valid_months = set()
                for (sid, ts), chmi in reference.items():
                    if sid != STATIONS[target] or ts not in site:
                        continue
                    ym = month(ts)
                    if not hstart <= ym <= hend:
                        continue
                    bias = site[ts] - chmi
                    before.append(bias)
                    after.append(bias - predict(params, ts))
                    valid_months.add(ym)
                base = summary(before)
                corrected = summary(after)
                # Strict hour-level diagnostic criterion, NOT approval to write.
                pass_qc = (len(valid_months) >= 3 and corrected["n"] >= 200
                           and corrected["mae"] is not None and corrected["mae"] <= 2.0
                           and corrected["p95_abs"] <= 4.0
                           and corrected["mae"] <= base["mae"] * .8)
                out.append({"epoch": e["id"], "trained_on": training, "tested_on": target,
                            "selected_model": chosen, "holdout_months": [hstart, hend],
                            "n_months": len(valid_months), "raw": base, "corrected": corrected,
                            "diagnostic_hourly_gate": "PASS_NOT_APPLY" if pass_qc else "FAIL_OR_INSUFFICIENT"})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cnf", type=Path, required=True)
    ap.add_argument("--chmi-cache", type=Path, required=True)
    ap.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    frozen = json.loads(a.model.read_text(encoding="utf-8"))
    ref, chmi_meta = load_chmi_hourly(a.chmi_cache)
    site, identity = load_site_hours(a.cnf)
    scores = hourly_backtest(frozen, ref, site)
    if not scores:
        raise RuntimeError("No valid hourly holdout comparison")
    result = {"schema": "loucka-pressure-hourly-holdout-v1",
              "state": "EVIDENCE_ONLY_NO_APPROVED_VALUES",
              "method": "Frozen monthly model tested on held-out observed hourly barometer − CHMI P_hm residuals",
              "model_sha256": sha256(a.model), "chmi": chmi_meta,
              "database_identity": identity, "local_hourly_rows": len(site), "scores": scores,
              "limitations": ["No correction to station pressure field",
                              "No guarantee for interpolated 5-minute values",
                              "No calibration is an original sensor observation",
                              "Quality of matched CHMI station-hour does not guarantee equality of spatial pressure fields",
                              "No SQL writes nor prospective replacement manifests"]}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status":"READ_ONLY_DONE","reference":chmi_meta["valid_station_hour_values"],
                      "site_hourly":len(site),"diagnostic_groups":len(scores),
                      "results_file":str(a.out)},ensure_ascii=False))


if __name__ == "__main__":
    main()
