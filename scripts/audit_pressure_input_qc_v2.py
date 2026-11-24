#!/usr/bin/env python3
"""Read-only 2009-2026 barometer spike screen; never modifies archive values."""
from __future__ import annotations
import argparse, configparser, csv, hashlib, json, math, statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DATABASES = ("pocasi-loucka.eu", "loucka_reconstruction", "weewx_WH1080")
EXPECTED_UNITS = {"pocasi-loucka.eu": 16, "loucka_reconstruction": 16, "weewx_WH1080": 17}
START = int(datetime(2009, 1, 1, tzinfo=timezone.utc).timestamp())
END = int(datetime(2026, 11, 25, tzinfo=timezone.utc).timestamp())
SPIKE_HPA, RETURN_HPA, MAX_GAP_SECONDS = 3.0, 1.5, 900


def isolated_reversal(prev, cur, nxt):
    """True for a single-row ≥3 hPa reversal returning within 1.5 hPa ≤15 min."""
    if any(x is None for x in (prev, cur, nxt)) or any(x[1] is None for x in (prev, cur, nxt)):
        return False
    if not (0 < cur[0]-prev[0] <= MAX_GAP_SECONDS and 0 < nxt[0]-cur[0] <= MAX_GAP_SECONDS):
        return False
    a, b, c = prev[1], cur[1], nxt[1]
    if not all(math.isfinite(x) and 800 <= x <= 1100 for x in (a,b,c)):
        return False
    return abs(b-a) >= SPIKE_HPA and abs(c-b) >= SPIKE_HPA and (b-a)*(c-b) < 0 and abs(c-a) <= RETURN_HPA


def read_database(cnf: Path, database: str):
    import pymysql
    from pymysql.cursors import SSCursor
    cfg = configparser.ConfigParser(interpolation=None)
    if not cfg.read(cnf) or cfg.get("client", "user", fallback="") != "loucka_web_ro":
        raise PermissionError("Only existing loucka_web_ro may be used")
    con = pymysql.connect(read_default_file=str(cnf), read_default_group="client", database="loucka_reconstruction",
                          autocommit=False, connect_timeout=15, read_timeout=300)
    try:
        with con.cursor() as cur:
            cur.execute("START TRANSACTION READ ONLY")
            cur.execute("SELECT @@hostname, @@server_id, CURRENT_USER()")
            ident = cur.fetchone()
            if ident != ("lo-infra-db-mariadb01", 1, "loucka_web_ro@192.168.0.131"):
                raise RuntimeError("Unexpected database identity")
            sql = f"""SELECT `dateTime`, `usUnits`, `interval`, `barometer`
                      FROM `{database}`.`archive`
                      WHERE `dateTime` >= %s AND `dateTime` < %s
                      ORDER BY `dateTime`"""
            cur.execute(sql, (START, END))
            while True:
                batch = cur.fetchmany(20000)
                if not batch:
                    break
                for row in batch:
                    yield {"dateTime": int(row[0]), "usUnits": int(row[1]),
                           "interval": int(row[2]), "barometer": None if row[3] is None else float(row[3])}
    finally:
        con.rollback()
        con.close()


def scan(rows, expected_units):
    counts = {"rows": 0, "nonnull_barometer": 0, "null_barometer": 0, "unexpected_units": 0, "out_of_range_800_1100": 0}
    annual = defaultdict(lambda: {"rows":0,"nonnull_barometer":0,"suspected_isolated_reversal":0})
    flagged=[]; prev2=None; prev=None
    for cur in rows:
        counts["rows"] += 1
        year = datetime.fromtimestamp(cur["dateTime"], timezone.utc).year
        annual[year]["rows"] += 1
        if cur["usUnits"] != expected_units:
            counts["unexpected_units"] += 1
        v=cur["barometer"]
        if v is None:
            counts["null_barometer"] += 1
        else:
            counts["nonnull_barometer"] += 1; annual[year]["nonnull_barometer"] += 1
            if not math.isfinite(v) or not 800 <= v <= 1100:
                counts["out_of_range_800_1100"] += 1
        if prev2 is not None and isolated_reversal((prev2["dateTime"],prev2["barometer"]), (prev["dateTime"],prev["barometer"]), (cur["dateTime"],cur["barometer"])):
            pdt=datetime.fromtimestamp(prev["dateTime"],timezone.utc)
            annual[pdt.year]["suspected_isolated_reversal"] += 1
            flagged.append({"dateTime_utc":prev["dateTime"],"barometer_hpa":prev["barometer"],
                            "previous_dateTime_utc":prev2["dateTime"],"previous_barometer_hpa":prev2["barometer"],
                            "next_dateTime_utc":cur["dateTime"],"next_barometer_hpa":cur["barometer"],
                            "previous_gap_s":prev["dateTime"]-prev2["dateTime"],"next_gap_s":cur["dateTime"]-prev["dateTime"],
                            "previous_delta_hpa":prev["barometer"]-prev2["barometer"],
                            "next_delta_hpa":cur["barometer"]-prev["barometer"],
                            "return_difference_hpa":cur["barometer"]-prev2["barometer"],
                            "diagnosis":"SUSPECTED_ISOLATED_BAROMETER_SPIKE","approval_status":"DIAGNOSTIC_ONLY"})
        prev2, prev = prev, cur
    return {"counts":counts,"annual":dict(annual),"flagged":flagged}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--cnf",required=True,type=Path);ap.add_argument("--out-dir",required=True,type=Path)
    a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True);result={"schema":"pressure-barometer-input-qc-v2","state":"READ_ONLY_DIAGNOSTIC_NO_SOURCE_CHANGES","period_utc":{"start_inclusive":START,"end_exclusive":END},"rule":{"name":"isolated reversal","barometer_abs_delta_from_both_neighbors_hpa_at_least":SPIKE_HPA,"neighbor_return_difference_hpa_at_most":RETURN_HPA,"each_neighbor_gap_seconds_at_most":MAX_GAP_SECONDS,"time_basis":"UTC dateTime","expected_units_by_source":EXPECTED_UNITS,"pressure_unit_interpretation":"usUnits=16 and 17 records are hPa for barometer; screened ranges corroborate this; no conversion applied"},"sources":{}}
    for db in DATABASES:
        scan_result=scan(read_database(a.cnf,db),EXPECTED_UNITS[db]); rows=scan_result.pop("flagged")
        dest=a.out_dir/f"{db.replace('.','_')}-suspected-spikes.csv"
        with dest.open("w",newline="") as f:
            fields=list(rows[0]) if rows else ["dateTime_utc","barometer_hpa","diagnosis","approval_status"]
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
        raw=dest.read_bytes();scan_result["suspect_csv"]={"file":dest.name,"rows":len(rows),"sha256":hashlib.sha256(raw).hexdigest()}
        result["sources"][db]=scan_result
        print(json.dumps({"database":db,"rows":scan_result["counts"]["rows"],"suspected_spikes":len(rows),"csv":str(dest)}))
    out=a.out_dir/"pressure-barometer-input-qc-v2.json";out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":"READ_ONLY_DONE","summary":str(out)}))

if __name__=="__main__":main()
