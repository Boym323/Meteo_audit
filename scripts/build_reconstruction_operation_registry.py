#!/usr/bin/env python3
"""Reconcile immutable v1.2 historical operations with the live read-only state."""
from __future__ import annotations
import hashlib,json,os,sqlite3
from collections import Counter,defaultdict
from decimal import Decimal
from pathlib import Path
import pymysql
from pymysql.cursors import DictCursor

ROOT=Path(__file__).resolve().parents[1];PAYLOADS=ROOT/"execution_payloads/v1.2";OUT=ROOT/"data/RECONSTRUCTION_OPERATION_REGISTRY_V1_2.json"
FIELDS=("outTemp","outHumidity","pressure","barometer","altimeter","windSpeed","windGust","windDir")

def digest_bytes(b):return hashlib.sha256(b).hexdigest()
def numeq(a,b):
    if a is None or b is None:return a is None and b is None
    try:return Decimal(str(a))==Decimal(str(b))
    except Exception:return a==b

def main():
    manifest=json.loads((PAYLOADS/"manifest.json").read_text());ops=[];payload_files=[]
    for item in manifest["batches"]:
        path=ROOT/item["payload_path"];raw=path.read_bytes();actual_hash=digest_bytes(raw)
        if actual_hash!=item["payload_sha256"]:raise RuntimeError(f"immutable payload hash mismatch: {path}")
        payload=json.loads(raw)
        if len(payload["corrections"])!=item["operation_count"]:raise RuntimeError(f"payload count mismatch: {path}")
        payload_files.append({"path":str(path.relative_to(ROOT)),"sha256":actual_hash,"batch_id":payload["batch_id"],"canonical_batch_id":payload["canonical_batch_id"],"canonical_payload_sha256":payload["canonical_batch_payload_sha256"],"classification":payload["classification"],"operations":len(payload["corrections"])})
        for index,op in enumerate(payload["corrections"]):
            if op["variable"] not in FIELDS:raise RuntimeError(f"unreviewed operation field {op['variable']}")
            ops.append({**op,"batch_id":payload["batch_id"],"canonical_batch_id":payload["canonical_batch_id"],"source_package":payload["source_package"],"classification":payload["classification"],"payload_sha256":actual_hash,"canonical_payload_sha256":payload["canonical_batch_payload_sha256"],"operation_index":index})
    if len({(x["timestamp"],x["variable"]) for x in ops})!=len(ops):raise RuntimeError("duplicate timestamp/field in immutable execution layer")
    env=os.environ
    conn=pymysql.connect(host=env["WEATHER_DB_HOST"],port=int(env.get("WEATHER_DB_PORT","3306")),user=env["WEATHER_DB_USER"],password=env["WEATHER_DB_PASSWORD"],database="loucka_reconstruction",charset="utf8mb4",autocommit=False,cursorclass=DictCursor)
    try:
        q=conn.cursor();q.execute("SET SESSION TRANSACTION READ ONLY");q.close();conn.begin()
        q=conn.cursor();q.execute("SELECT VERSION() version,@@hostname host,@@server_id server_id,CURRENT_USER() account");identity=q.fetchone()
        stamps=sorted({int(x["timestamp"]) for x in ops});placeholders=",".join(["%s"]*len(stamps));cols=",".join(f"`{f}`" for f in FIELDS)
        q.execute(f"SELECT `dateTime`,`usUnits`,`interval`,{cols} FROM `archive` WHERE `dateTime` IN ({placeholders})",stamps);target={int(r["dateTime"]):r for r in q.fetchall()}
        q.execute(f"SELECT `id`,`batch_key`,`target_time`,`variable`,`old_value`,`new_value`,`reason`,`state` FROM `reconstruction_changes` WHERE `target_time` IN ({placeholders}) ORDER BY `id`",stamps)
        events=defaultdict(list)
        for r in q.fetchall():events[(int(r["target_time"]),r["variable"])].append(r)
        q.close()
        for op in ops:
            ts=int(op["timestamp"]);var=op["variable"];row=target.get(ts);current=row.get(var) if row else None
            matching=[e for e in events.get((ts,var),[]) if e["state"]=="applied" and numeq(e["new_value"],op["new_value"])]
            exact_batch=[e for e in matching if e["batch_key"]==op["batch_id"]]
            current_matches_payload=numeq(current,op["new_value"])
            if exact_batch and current_matches_payload:state="ACTUALLY_APPLIED_MATCHING_BATCH"
            elif matching and current_matches_payload:state="ACTUALLY_APPLIED_EQUIVALENT_EVENT"
            elif exact_batch or matching:state="APPLIED_EVENT_CURRENT_VALUE_MISMATCH"
            elif any(e["state"]=="applied" and not numeq(e["new_value"],op["new_value"]) for e in events.get((ts,var),[])) and row is not None and numeq(current,next(e["new_value"] for e in reversed(events[(ts,var)]) if e["state"]=="applied")):
                state="CURRENT_STATE_MISMATCH_PRIOR_EVENT_DIFFERS"
            elif op["operation"]=="insert" and row is None:state="AWAITING_APPROVAL_PRESTATE_ABSENT"
            elif numeq(current,op.get("expected_old_value")):state="AWAITING_APPROVAL_PRESTATE_MATCHES"
            else:state="CURRENT_STATE_MISMATCH_REQUIRES_REVIEW"
            approved=False
            op.update({"current_target_row_exists":row is not None,"current_target_value":str(current) if current is not None else None,"current_value_matches_proposed_postimage":current_matches_payload,"current_usUnits":int(row["usUnits"]) if row else None,"current_interval_minutes":int(row["interval"] or 0) if row else None,"matching_applied_event_ids":[int(e["id"]) for e in matching],"matching_batch_event_ids":[int(e["id"]) for e in exact_batch],"applied_event_history":[{"id":int(e["id"]),"batch_key":e["batch_key"],"new_value":str(e["new_value"]) if e["new_value"] is not None else None,"state":e["state"],"reason":e["reason"]} for e in events.get((ts,var),[])],"owner_approval_evidence_found":approved,"disposition":state})
        conn.rollback()
    finally:conn.close()
    counts=Counter(x["disposition"] for x in ops)
    registry={"schema":"loucka-reconstruction-operation-registry-v1","captured_read_only":True,"database_identity":identity,"v1_2_manifest_sha256":digest_bytes((PAYLOADS/"manifest.json").read_bytes()),"immutable_payload_files":payload_files,"operation_count":len(ops),"unique_timestamp_variable_count":len({(x['timestamp'],x['variable']) for x in ops}),"counts_by_disposition":dict(counts),"approved_but_not_applied":sum(x["owner_approval_evidence_found"] and x["disposition"].startswith("AWAITING") for x in ops),"not_approved_and_not_applied":sum(not x["owner_approval_evidence_found"] and x["disposition"].startswith("AWAITING") for x in ops),"q1_2018_or_2021_targets":sum(1514764800<=int(x['timestamp'])<1522540800 or 1609459200<=int(x['timestamp'])<1640995200 for x in ops),"rain_or_rainrate_targets":sum(x['variable'] in {'rain','rainRate'} for x in ops),"operations":ops,"limitations":["Owner approval artifacts were not found in the exact v1.2 immutable execution layer; pending operations remain unapproved.","A matching applied event is counted as applied only by timestamp, field, and exact postimage; exact event/batch identity is reported separately.","Pending operations require a new read-only preflight and separate owner approval; this registry is not an execution authorization."]}
    OUT.write_text(json.dumps(registry,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","operations":len(ops),"dispositions":dict(counts),"approved_but_not_applied":registry["approved_but_not_applied"],"not_approved_and_not_applied":registry["not_approved_and_not_applied"],"protected_targets":registry["q1_2018_or_2021_targets"],"rain_targets":registry["rain_or_rainrate_targets"],"output":str(OUT)},indent=2))

if __name__=="__main__":main()
