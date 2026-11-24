#!/usr/bin/env python3
"""Reproduce fixed-alternative 2022 pressure shadow diagnostics (read-only only)."""
from __future__ import annotations
import argparse, configparser, json, math, statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from validate_pressure_station_field import STATIONS, load_chmi, metrics, transport_station_pressure

START, END = 1640995200, 1659312000
G, RD = 9.80665, 287.05


def gate_pass(hours, coverage, scores, gate):
    return (hours >= gate["min_common_hours_per_month"]
            and coverage >= gate["min_common_coverage"]
            and all(s["mae_hpa"] is not None
                    and s["mae_hpa"] <= gate["max_mae_hpa"]
                    and s["p95_abs_error_hpa"] <= gate["max_p95_absolute_hpa"]
                    and abs(s["median_bias_hpa"]) <= gate["max_abs_median_bias_hpa"]
                    for s in scores.values()))


def read_missing(cnf: Path):
    import pymysql
    from pymysql.cursors import DictCursor
    cfg = configparser.ConfigParser(interpolation=None)
    if not cfg.read(cnf) or cfg.get("client", "user", fallback="") != "loucka_web_ro":
        raise PermissionError("Use the existing loucka_web_ro read-only config")
    conn = pymysql.connect(read_default_file=str(cnf), read_default_group="client",
                           database="loucka_reconstruction", cursorclass=DictCursor,
                           autocommit=False, connect_timeout=15, read_timeout=120)
    try:
        with conn.cursor() as c:
            c.execute("START TRANSACTION READ ONLY")
            c.execute("SELECT @@hostname host, @@server_id server_id, CURRENT_USER() account")
            identity = c.fetchone()
            if (identity["host"], int(identity["server_id"]), identity["account"]) != (
                    "lo-infra-db-mariadb01", 1, "loucka_web_ro@192.168.0.131"):
                raise RuntimeError("Unexpected database identity")
            c.execute("""SELECT dateTime, usUnits, barometer, outTemp
                         FROM loucka_reconstruction.archive
                         WHERE dateTime >= %s AND dateTime < %s AND pressure IS NULL
                           AND barometer IS NOT NULL AND outTemp IS NOT NULL
                         ORDER BY dateTime""", (START, END))
            rows = c.fetchall()
            if any(int(r["usUnits"]) != 16 for r in rows):
                raise ValueError("Unexpected archive units")
            return rows, identity
    finally:
        conn.rollback()
        conn.close()


def score_alternatives(rows, refs, model, ref_meta):
    p = model["parameters"]
    gate = model["preview"]["gate"]
    totals = defaultdict(lambda: {"eligible_exact_hours": 0, "common_reference_hours": 0})
    errors = defaultdict(list)
    for row in rows:
        ts = int(row["dateTime"])
        if ts % 3600:
            continue
        ym = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")
        totals[ym]["eligible_exact_hours"] += 1
        if any((sid, ts) not in refs for sid, _ in STATIONS.values()):
            continue
        totals[ym]["common_reference_hours"] += 1
        b, t = float(row["barometer"]), float(row["outTemp"])
        physical = b * math.exp(-G * 425 / (RD * (t + 273.15)))
        estimates = {"physical": physical,
                     "constant": physical + p["offset_hpa"],
                     "frozen_temp": physical + p["offset_hpa"] +
                     p["temperature_slope_hpa_per_c"] * (t - p["temperature_center_c"])}
        for name, estimate in estimates.items():
            for station, (sid, height) in STATIONS.items():
                error = transport_station_pressure(estimate, t, height) - float(refs[(sid, ts)])
                errors[(ym, name, station)].append(error)
    results = {}
    for ym, total in sorted(totals.items()):
        n = total["common_reference_hours"]
        coverage = n / total["eligible_exact_hours"] if total["eligible_exact_hours"] else 0
        results[ym] = {**total, "common_coverage": coverage, "models": {}}
        for name in ("physical", "constant", "frozen_temp"):
            scores = {st: metrics(errors[(ym, name, st)]) for st in ("H", "M")}
            results[ym]["models"][name] = {
                "scores": scores,
                "gate": "PASS_DIAGNOSTIC_PREVIEW_ONLY" if gate_pass(n, coverage, scores, gate)
                else "FAIL_OR_INSUFFICIENT"}
    return {"schema": "pressure-alternative-models-2022-v1",
            "state": "UNAPPROVED_DIAGNOSTIC_ONLY",
            "method": "Fixed physical, 2020-fit constant, and frozen 2020-fit/2021-selected temperature models; exact missing UTC hours; dual-station holdout; no refit on 2022",
            "reference_manifest_sha256": ref_meta["manifest_sha256"],
            "gate": gate, "months": results}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cnf", required=True, type=Path)
    ap.add_argument("--chmi-cache", required=True, type=Path)
    ap.add_argument("--model", type=Path, default=Path("models/pressure-shadow-2022-v1.json"))
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    refs, ref_meta = load_chmi(args.chmi_cache)
    rows, identity = read_missing(args.cnf)
    model = json.loads(args.model.read_text())
    result = score_alternatives(rows, refs, model, ref_meta)
    result["database_identity"] = identity
    result["missing_rows_with_inputs"] = len(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"status": "READ_ONLY_DONE", "missing_rows_with_inputs": len(rows),
                      "months": len(result["months"]), "out": str(args.out)}))


if __name__ == "__main__":
    main()
