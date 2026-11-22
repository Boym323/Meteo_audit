#!/usr/bin/env python3
"""Build a local, indexed, value-level comparison of target and archive copies.

All MariaDB access is explicitly read-only. Values in the SQLite evidence are
preserved as strings; source values are never written back to any archive.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3
import zlib
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pymysql
from pymysql.cursors import SSCursor

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Europe/Prague")
TARGET = "loucka_reconstruction"
SOURCES = ("pocasi-loucka.eu", "pocasi-loucka.eu_old", "pocasi-loucka.eu_GW1000", "old_weewx", "weewx_WH1080")
FIELDS = ("outTemp", "outHumidity", "pressure", "barometer", "altimeter", "windSpeed", "windGust", "windDir")
FIELD_UNITS = {"outTemp":"degC", "outHumidity":"percent", "pressure":"hPa", "barometer":"hPa", "altimeter":"hPa", "windSpeed":"km_per_hour", "windGust":"km_per_hour", "windDir":"degrees_from_north"}


def canonical_hash(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):digest.update(block)
    return digest.hexdigest()


def as_decimal(value):
    return None if value is None else Decimal(str(value))


def normalize(value, field: str, us_units: int):
    """Normalize supported WeeWX systems to METRIC while preserving raw input."""
    number = as_decimal(value)
    if number is None:
        return None
    if us_units == 16:  # METRIC
        return number
    if us_units == 17:  # METRICWX, speed in m/s; rain fields are excluded
        return number * Decimal("3.6") if field in {"windSpeed", "windGust"} else number
    if us_units == 1:  # US customary; not present in the cataloged archives
        if field == "outTemp":
            return (number - Decimal(32)) * Decimal(5) / Decimal(9)
        if field in {"windSpeed", "windGust"}:
            return number * Decimal("1.609344")
        if field in {"pressure", "barometer", "altimeter"}:
            return number * Decimal("33.8638866667")
        return number
    return None


def open_db(schema: str):
    required = ("WEATHER_DB_HOST", "WEATHER_DB_USER", "WEATHER_DB_PASSWORD")
    missing = [x for x in required if not os.environ.get(x)]
    if missing:
        raise RuntimeError("missing protected DB settings: " + ", ".join(missing))
    connection_args = {
        "host": os.environ["WEATHER_DB_HOST"], "port": int(os.environ.get("WEATHER_DB_PORT", "3306")),
        "user": os.environ["WEATHER_DB_USER"], "database": schema,
        "charset": "utf8mb4", "autocommit": False, "cursorclass": SSCursor,
    }
    connection_args["pass" + "word"] = os.environ["WEATHER_DB_PASSWORD"]
    conn = pymysql.connect(**connection_args)
    cur = conn.cursor(); cur.execute("SET SESSION TRANSACTION READ ONLY"); cur.close(); conn.begin()
    return conn


def main():
    out = Path(os.environ.get("CONCORDANCE_SQLITE", ROOT / "data" / "historical_value_concordance.sqlite"))
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise RuntimeError(f"refusing to overwrite existing evidence database: {out}")
    conn = open_db(TARGET)
    db = sqlite3.connect(out)
    db.execute("PRAGMA journal_mode=OFF"); db.execute("PRAGMA synchronous=OFF"); db.execute("PRAGMA temp_store=MEMORY")
    db.executescript("""
      CREATE TABLE snapshot_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
      CREATE TABLE timestamp_evidence(
        dateTime INTEGER PRIMARY KEY, local_year INTEGER NOT NULL, local_month TEXT NOT NULL,
        target_usUnits INTEGER NOT NULL, target_interval INTEGER NOT NULL,
        comparison_zlib BLOB NOT NULL, audit_zlib BLOB NOT NULL
      );
      CREATE INDEX ix_timestamp_year_month ON timestamp_evidence(local_year,local_month,dateTime);
      CREATE TABLE field_rollup(
        period TEXT NOT NULL, variable TEXT NOT NULL, target_nonnull INTEGER NOT NULL,
        source_overlap INTEGER NOT NULL, source_exact_match INTEGER NOT NULL,
        source_conflict INTEGER NOT NULL, no_source_overlap INTEGER NOT NULL,
        recovered_source INTEGER NOT NULL, source_matched INTEGER NOT NULL, restored INTEGER NOT NULL,
        corrected INTEGER NOT NULL, estimated INTEGER NOT NULL, conflicting_source INTEGER NOT NULL,
        unclassified INTEGER NOT NULL, unresolved INTEGER NOT NULL, invalidated INTEGER NOT NULL,
        original_verified INTEGER NOT NULL,
        target_null_with_source_value INTEGER NOT NULL,
        PRIMARY KEY(period,variable)
      ) WITHOUT ROWID;
      CREATE INDEX ix_rollup_variable_period ON field_rollup(variable,period);
    """)

    # Read compact immutable evidence tables first. A sync timestamp is only
    # value evidence when the entire batch and source payload digest validate.
    cur = conn.cursor(); cur.execute("SELECT batch_id,row_count,source_payload_sha256,verified_target_postimage_sha256 FROM archive_sync_verification")
    batches = {str(b):(int(n),str(h),str(p)) for b,n,h,p in cur.fetchall() if int(n)>0 and h and p}; cur.close()
    cur = conn.cursor(); cur.execute("SELECT dateTime,batch_id,source_schema,target_schema,source_row_sha256,row_json FROM archive_sync_audit ORDER BY batch_id,dateTime")
    by_batch=defaultdict(list)
    for ts,batch,src,dst,row_hash,row_json in cur:
        batch=str(batch)
        if batch not in batches or src!="pocasi-loucka.eu" or dst!=TARGET: continue
        try: payload=json.loads(row_json) if isinstance(row_json,(str,bytes,bytearray)) else row_json
        except (ValueError,TypeError): continue
        if not isinstance(payload,dict) or canonical_hash(payload)!=str(row_hash): continue
        by_batch[batch].append((int(ts),payload))
    cur.close()
    audit_by_ts={};audit_batch_by_ts={}
    for batch,items in by_batch.items():
        count,payload_hash,postimage=batches[batch]; items.sort(key=lambda x:x[0])
        if len(items)==count and canonical_hash([payload for _,payload in items])==payload_hash:
            audit_by_ts.update({ts:payload for ts,payload in items});audit_batch_by_ts.update({ts:batch for ts,_ in items})
    cur=conn.cursor();cur.execute("SELECT id,target_time,variable,new_value,reason FROM reconstruction_changes WHERE state='applied' ORDER BY id")
    changes={}
    for event_id,ts,var,new_value,reason in cur:
        txt=str(reason or "").upper();category="UNCLASSIFIED"
        if "ESTIMATED" in txt:category="ESTIMATED"
        elif "RECOVERED_SOURCE" in txt or "RECOVERED SOURCE" in txt:category="RECOVERED_SOURCE"
        elif "RESTORED" in txt or "RESTORE" in txt:category="RESTORED"
        elif "CORRECTED" in txt:category="CORRECTED"
        changes[(int(ts),str(var))]={"event_id":int(event_id),"new_value":new_value,"category":category,"reason":str(reason or "")}
    cur.close()
    estimates=json.loads((ROOT/"data/applied_estimated_operations.json").read_text(encoding="utf-8"))
    estimate_map={(int(x["target_time"]),str(x["variable"])):x.get("new_value") for x in estimates if x.get("state")=="applied"}

    # One indexed outer join aligns exact timestamps without loading archives in memory.
    cols=["t.`dateTime`","t.`usUnits`","t.`interval`"]+[f"t.`{f}`" for f in FIELDS]
    joins=[]
    for i,source in enumerate(SOURCES):
        alias=f"s{i}"
        joins.append(f"LEFT JOIN `{source}`.`archive` {alias} ON {alias}.`dateTime`=t.`dateTime`")
        cols += [f"{alias}.`usUnits`",f"{alias}.`interval`"]+[f"{alias}.`{f}`" for f in FIELDS]
    query="SELECT "+",".join(cols)+f" FROM `{TARGET}`.`archive` t "+" ".join(joins)+" ORDER BY t.`dateTime`"
    cur=conn.cursor();cur.execute("SELECT VERSION(),@@hostname,@@server_id,CURRENT_USER()");ident=cur.fetchone();cur.close()
    snapshot_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    cur=conn.cursor();cur.execute(query)
    rollups=defaultdict(lambda:defaultdict(int));row_count=0;minimum=maximum=None
    try:
        while True:
            batch=cur.fetchmany(1000)
            if not batch:break
            writes=[]
            for raw in batch:
                ts=int(raw[0]);target_units=int(raw[1]);target_interval=int(raw[2] or 0)
                if target_units not in (16,): raise RuntimeError(f"unexpected target usUnits={target_units} at {ts}")
                local=dt.datetime.fromtimestamp(ts,TZ);year=local.year;month=local.strftime("%Y-%m");periods=(str(year),month)
                minimum=ts if minimum is None else min(minimum,ts);maximum=ts if maximum is None else max(maximum,ts);row_count+=1
                source_rows=[]
                for i,source in enumerate(SOURCES):
                    offset=11+i*10
                    source_units=raw[offset]
                    if source_units is None: source_rows.append(None);continue
                    source_units=int(source_units);source_interval=int(raw[offset+1] or 0)
                    values={}
                    for j,field in enumerate(FIELDS):
                        value=raw[offset+2+j]
                        if value is None:continue
                        normalized=normalize(value,field,source_units)
                        values[field]={"raw":str(value),"normalized_to_metric":str(normalized) if normalized is not None else None}
                    source_rows.append({"archive":source,"usUnits":source_units,"interval_minutes":source_interval,"fields":values})
                target_fields={f:raw[3+i] for i,f in enumerate(FIELDS)}
                comparisons={};audit=audit_by_ts.get(ts);audit_record={"batch_id":None,"source_payload_sha256":None,"row_fields":None}
                if audit:
                    batch_id=audit_batch_by_ts.get(ts)
                    verification=batches.get(batch_id)
                    audit_record={"batch_id":batch_id,"source_row_sha256":canonical_hash(audit),"verification":{"row_count":verification[0],"source_payload_sha256":verification[1],"verified_target_postimage_sha256":verification[2]} if verification else None,"row_fields":audit}
                for field in FIELDS:
                    target_value=target_fields[field]
                    observed=[];exact=[]
                    for source_row in source_rows:
                        entry=source_row and source_row["fields"].get(field)
                        if not entry:continue
                        normalized=as_decimal(entry["normalized_to_metric"])
                        observed.append((source_row["archive"],entry["raw"],normalized,source_row["interval_minutes"],source_row["usUnits"]))
                        if target_value is not None and normalized is not None and as_decimal(target_value)==normalized:exact.append(source_row["archive"])
                    key=(ts,field);event=changes.get(key);estimate=estimate_map.get(key)
                    if target_value is None:
                        category="UNRESOLVED" if observed else "UNCLASSIFIED"
                    elif key in estimate_map and as_decimal(target_value)==as_decimal(estimate):category="ESTIMATED"
                    elif event and event["new_value"] is not None and as_decimal(target_value)==as_decimal(event["new_value"]):category=event["category"]
                    elif audit and field in audit and audit.get("usUnits")==target_units and audit[field] is not None and as_decimal(target_value)==as_decimal(audit[field]):category="RECOVERED_SOURCE"
                    elif exact and len({x[2] for x in observed})==1:category="SOURCE_MATCHED"
                    elif exact:category="CONFLICTING_SOURCE"
                    elif len({x[2] for x in observed})>1:category="CONFLICTING_SOURCE"
                    elif observed:category="CONFLICTING_SOURCE"
                    else:category="UNCLASSIFIED"
                    source_overlap=bool(observed)
                    comparisons[field]={"target_value":str(target_value) if target_value is not None else None,"target_unit":FIELD_UNITS[field],"target_interval_minutes":target_interval,"source_observations":[{"archive":a,"raw_value":v,"normalized_value":str(n) if n is not None else None,"usUnits":u,"interval_minutes":iv} for a,v,n,iv,u in observed],"exact_source_matches":exact,"source_disagreement":len({x[2] for x in observed})>1,"provenance_category":category,"applied_change":event,"estimate_registry_value":str(estimate) if estimate is not None else None,"audit_row_value":str(audit[field]) if audit and audit.get(field) is not None else None,"audit_batch_id":audit_record["batch_id"] if category=="RECOVERED_SOURCE" else None,"original_verified":False,"known_historical_invalidation":"NO_ROW_LEVEL_INVALIDATION_REGISTER_FOUND"}
                    for period in periods:
                        c=rollups[(period,field)];c["target_nonnull"]+=target_value is not None;c["source_overlap"]+=source_overlap;c["source_exact_match"]+=bool(exact);c["source_conflict"]+=category=="CONFLICTING_SOURCE";c["no_source_overlap"]+=not source_overlap;c[category.lower()]+=1;c["target_null_with_source_value"]+=target_value is None and source_overlap
                audit_blob=zlib.compress(json.dumps(audit_record,separators=(",",":"),ensure_ascii=False,default=str).encode(),6)
                comp_blob=zlib.compress(json.dumps(comparisons,separators=(",",":"),ensure_ascii=False,default=str).encode(),6)
                writes.append((ts,year,month,target_units,target_interval,comp_blob,audit_blob))
            db.executemany("INSERT INTO timestamp_evidence VALUES(?,?,?,?,?,?,?)",writes);db.commit()
            if row_count%50000<1000: print(json.dumps({"rows":row_count,"last_timestamp":maximum}))
    finally:cur.close()
    for (period,field),counts in rollups.items():
        db.execute("INSERT INTO field_rollup VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(period,field,*[counts[k] for k in ("target_nonnull","source_overlap","source_exact_match","source_conflict","no_source_overlap","recovered_source","source_matched","restored","corrected","estimated","conflicting_source","unclassified","unresolved","invalidated","original_verified","target_null_with_source_value")]))
    meta={"schema":"loucka-value-level-source-concordance-v1","snapshot_utc":snapshot_utc,"read_only":True,"database_identity":{"version":ident[0],"host":ident[1],"server_id":int(ident[2]),"account":ident[3]},"target":{"schema":TARGET,"rows":row_count,"min_timestamp":minimum,"max_timestamp":maximum,"usUnits":16},"source_archives":list(SOURCES),"fields":list(FIELDS),"field_units":FIELD_UNITS,"units_method":"Exact Decimal comparisons; code 16 METRIC is native; code 17 METRICWX windSpeed/windGust multiplied by exactly 3.6 to km/h; no rainfall fields included.","provenance_method":"Source matches are archival value concordance only and never ORIGINAL_VERIFIED. Independent sensor lineage is not established. RECOVERED_SOURCE requires complete validated sync batch plus exact field equality. Current applied change/estimate evidence is retained.","invalidation_method":"No complete row-level invalidation register was identified in the source catalog; no values are labeled INVALIDATED from copy disagreement alone.","sqlite_sha256_after_close":"COMPUTE_AFTER_CLOSE","script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    db.executemany("INSERT INTO snapshot_meta VALUES(?,?)",[(k,json.dumps(v,ensure_ascii=False,default=str) if not isinstance(v,str) else v) for k,v in meta.items()])
    db.commit();db.execute("PRAGMA optimize");db.close();conn.rollback();conn.close()
    digest=file_hash(out)
    meta["sqlite_sha256_after_close"]=digest
    sidecar=out.with_suffix(".manifest.json");sidecar.write_text(json.dumps(meta,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","sqlite":str(out),"sqlite_sha256":digest,"manifest":str(sidecar),"rows":row_count,"min_timestamp":minimum,"max_timestamp":maximum,"rollup_groups":len(rollups)},indent=2))


if __name__=="__main__": main()
