#!/usr/bin/env python3
"""External validation and separate, unapproved station-pressure estimates (Jan–Jul 2022).

Does not update SQL or create a database approval manifest. The preview is a
local CSV, only for months meeting the predeclared dual-station hourly gate.
"""
from __future__ import annotations

import argparse
import configparser
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from validate_pressure_station_field import load_chmi, metrics, transport_station_pressure, STATIONS

ROOT = Path(__file__).resolve().parents[1]
START, END = 1640995200, 1659312000
G, RD = 9.80665, 287.05


def load_model(path):
    m = json.loads(path.read_text(encoding="utf-8"))
    if m["schema"] != "loucka-pressure-shadow-model-2022-v1" or m["mode"] != "FROZEN_DIAGNOSTIC_ESTIMATES_NO_APPLY":
        raise ValueError("Wrong frozen model")
    if m["training"]["site_height_m"] != 425 or m["training"]["units"] != 16:
        raise ValueError("Unexpected site height or units")
    return m


def prediction(barometer, temp, model):
    if barometer is None or temp is None:
        return None
    b, t = float(barometer), float(temp)
    d = model["training_domain"]
    if not (math.isfinite(b) and math.isfinite(t)
            and d["barometer_hpa"][0] <= b <= d["barometer_hpa"][1]
            and d["outTemp_c"][0] <= t <= d["outTemp_c"][1]):
        return None
    p = model["parameters"]
    value = b * math.exp(-G * model["training"]["site_height_m"] / (RD * (t + 273.15)))
    value += p["offset_hpa"] + p["temperature_slope_hpa_per_c"] * (t - p["temperature_center_c"])
    return value if math.isfinite(value) and 900 <= value <= 1050 else None


def read_rows(cnf):
    import pymysql
    from pymysql.cursors import DictCursor
    cfg = configparser.ConfigParser(interpolation=None)
    if not cfg.read(cnf) or cfg.get("client", "user", fallback="") != "loucka_web_ro":
        raise PermissionError("Use the existing read-only client config")
    conn = pymysql.connect(read_default_file=str(cnf), read_default_group="client",
                           database="loucka_reconstruction", cursorclass=DictCursor,
                           autocommit=False, connect_timeout=15, read_timeout=120)
    try:
        with conn.cursor() as c:
            c.execute("START TRANSACTION READ ONLY")
            c.execute("SELECT @@hostname AS host, @@server_id AS server_id, CURRENT_USER() AS account")
            ident = c.fetchone()
            if (ident["host"], int(ident["server_id"]), ident["account"]) != ("lo-infra-db-mariadb01", 1, "loucka_web_ro@192.168.0.131"):
                raise RuntimeError("Unexpected database identity")
            c.execute("""SELECT dateTime, usUnits, pressure, barometer, outTemp
                         FROM loucka_reconstruction.archive
                         WHERE dateTime >= %s AND dateTime < %s
                         ORDER BY dateTime""", (START, END))
            return list(c.fetchall()), ident
    finally:
        conn.rollback()
        conn.close()


def evaluate(rows, refs, model):
    """Evaluate actual NULLs at common exact hours, separately from known controls."""
    groups = defaultdict(lambda: {"eligible": 0, "hourly": 0, "common": 0,
                                 "H": [], "M": [], "local_control": []})
    candidates = []
    seen = set()
    for r in rows:
        ts = int(r["dateTime"])
        if not START <= ts < END or ts in seen or int(r["usUnits"]) != 16:
            raise ValueError("Unexpected timestamp, duplicate or units")
        seen.add(ts)
        ym = datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")
        gr = groups[ym]
        estimated = prediction(r["barometer"], r["outTemp"], model)
        if estimated is None:
            continue
        if r["pressure"] is not None:
            gr["local_control"].append(estimated - float(r["pressure"]))
            continue
        gr["eligible"] += 1
        candidates.append((ym, ts, float(r["barometer"]), float(r["outTemp"]), estimated))
        if ts % 3600:
            continue
        gr["hourly"] += 1
        if any((sid, ts) not in refs for sid, _ in STATIONS.values()):
            continue
        ref_values = {key: float(refs[(sid, ts)]) for key, (sid, _) in STATIONS.items()}
        if not all(math.isfinite(v) and 850 <= v <= 1080 for v in ref_values.values()):
            continue
        gr["common"] += 1
        for key, (_, height) in STATIONS.items():
            # Move the prediction to the reference station elevation, consistent
            # with PR #95. The residual includes spatial and transport uncertainty.
            gr[key].append(transport_station_pressure(estimated, float(r["outTemp"]), height) - ref_values[key])
    output = {}
    gate = model["preview"]["gate"]
    for ym, g in sorted(groups.items()):
        coverage = g["common"] / g["hourly"] if g["hourly"] else 0
        scores = {k: metrics(g[k]) for k in ("H", "M")}
        passes = (g["common"] >= gate["min_common_hours_per_month"] and
                  coverage >= gate["min_common_coverage"] and
                  all(s["mae_hpa"] is not None and s["mae_hpa"] <= gate["max_mae_hpa"]
                      and s["p95_abs_error_hpa"] <= gate["max_p95_absolute_hpa"]
                      and abs(s["median_bias_hpa"]) <= gate["max_abs_median_bias_hpa"]
                      for s in scores.values()))
        output[ym] = {
            "eligible_missing": g["eligible"], "eligible_exact_hours": g["hourly"],
            "common_reference_hours": g["common"], "common_coverage": coverage,
            "reference_scores": scores, "local_control": metrics(g["local_control"]),
            "gate": "PASS_DIAGNOSTIC_PREVIEW_ONLY" if passes else "FAIL_OR_INSUFFICIENT",
            "preview_rows": g["eligible"] if passes else 0,
        }
    return output, candidates


def write_preview(path, groups, candidates, model_sha, ref_sha, local_p95):
    with path.open("x", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dateTime_utc", "field", "original_value", "estimated_value_hpa",
                    "classification", "approval_status", "source", "source_barometer_hpa",
                    "source_outTemp_c", "model_sha256", "reference_manifest_sha256",
                    "reference_hourly_p95_max_hpa", "local_holdout_p95_hpa"])
        count = 0
        for ym, ts, b, t, p in candidates:
            month = groups[ym]
            if month["gate"] != "PASS_DIAGNOSTIC_PREVIEW_ONLY":
                continue
            regional_p95 = max(s["p95_abs_error_hpa"] for s in month["reference_scores"].values())
            w.writerow([ts, "pressure", "", f"{p:.4f}", "ESTIMATED", "UNAPPROVED",
                        "loucka_reconstruction.archive:barometer+outTemp", b, t, model_sha,
                        ref_sha, f"{regional_p95:.4f}", local_p95])
            count += 1
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cnf", type=Path, required=True)
    ap.add_argument("--chmi-cache", type=Path, required=True)
    ap.add_argument("--model", type=Path, default=ROOT / "models/pressure-shadow-2022-v1.json")
    ap.add_argument("--out-dir", type=Path, required=True, help="new local directory, not a database")
    args = ap.parse_args()
    model = load_model(args.model)
    model_sha = hashlib.sha256(args.model.read_bytes()).hexdigest()
    refs, ref_meta = load_chmi(args.chmi_cache)
    rows, identity = read_rows(args.cnf)
    groups, candidates = evaluate(rows, refs, model)
    args.out_dir.mkdir(parents=True, exist_ok=False)
    preview = args.out_dir / "pressure-shadow-unapproved.csv"
    count = write_preview(preview, groups, candidates, model_sha, ref_meta["manifest_sha256"],
                          model["local_validation"]["domain_2022_jan_jul"]["p95_absolute"])
    report = {"schema": "loucka-pressure-shadow-2022-results-v1",
              "state": "UNAPPROVED_ESTIMATES_ONLY_NO_SQL_WRITE",
              "database_identity": identity, "model_sha256": model_sha,
              "reference": ref_meta, "archive_rows_read": len(rows),
              "eligible_missing": len(candidates), "preview_rows": count,
              "approved_candidates": 0, "months": groups,
              "preview_sha256": hashlib.sha256(preview.read_bytes()).hexdigest(),
              "limitations": ["Gate tests regional hourly agreement, not local five-minute truth.",
                              "The model inverts the stored barometer and can inherit its bias.",
                              "Reported P95s are empirical diagnostics, NOT per-row uncertainty bounds.",
                              "All estimates remain UNAPPROVED; do not feed to an APPLY pipeline."]}
    (args.out_dir / "evidence.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status":"READ_ONLY_DONE","eligible_missing":len(candidates),
                      "preview_rows": count, "approved_candidates":0, "months":groups}, ensure_ascii=False))


if __name__ == "__main__":
    main()
