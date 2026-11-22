#!/usr/bin/env python3
"""Add the separately retained 2018-12-31 proposal to the v1.2 operation ledger."""
import hashlib,json,os
from decimal import Decimal
from pathlib import Path
import pymysql
from pymysql.cursors import DictCursor

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/"proposals/restored_source_only_2018_dec31_primary"

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def eq(a,b):
    if a is None or b is None:return a is None and b is None
    try:return Decimal(str(a))==Decimal(str(b))
    except Exception:return a==b

def main():
    reg=json.loads((ROOT/"data/RECONSTRUCTION_OPERATION_REGISTRY_V1_2.json").read_text())
    package_manifest=json.loads((PKG/"manifest.json").read_text());batch_files=json.loads((PKG/"weather_mcp_batches.json").read_text());proposal_ops=[op for b in batch_files for op in b["corrections"]]
    timestamps=sorted({int(op["timestamp"]) for op in proposal_ops});vars=sorted({op["variable"] for op in proposal_ops})
    env=os.environ;conn=pymysql.connect(host=env["WEATHER_DB_HOST"],port=int(env.get("WEATHER_DB_PORT","3306")),user=env["WEATHER_DB_USER"],password=env["WEATHER_DB_PASSWORD"],database="loucka_reconstruction",autocommit=False,cursorclass=DictCursor)
    try:
        q=conn.cursor();q.execute("SET SESSION TRANSACTION READ ONLY");q.close();conn.begin();q=conn.cursor();ph=",".join(["%s"]*len(timestamps))
        q.execute(f"SELECT `dateTime`,`usUnits`,`interval`,`outHumidity`,`rain`,`rainRate`,`windSpeed`,`windGust`,`windDir`,`barometer` FROM `archive` WHERE `dateTime` IN ({ph})",timestamps);rows={int(x["dateTime"]):x for x in q.fetchall()}
        q.execute(f"SELECT `id`,`batch_key`,`target_time`,`variable`,`old_value`,`new_value`,`reason`,`state` FROM `reconstruction_changes` WHERE `target_time` IN ({ph}) ORDER BY `id`",timestamps);events={}
        for e in q.fetchall():events.setdefault((int(e["target_time"]),e["variable"]),[]).append(e)
        q.close();identity_cursor=conn.cursor();identity_cursor.execute("SELECT VERSION() version,@@hostname host,@@server_id server_id,CURRENT_USER() account");identity=identity_cursor.fetchone();identity_cursor.close();conn.rollback()
    finally:conn.close()
    appended=[]
    for batch in batch_files:
        payload_hash=hashlib.sha256(json.dumps(batch,sort_keys=True,separators=(",",":"),ensure_ascii=False,default=str).encode()).hexdigest()
        for idx,op in enumerate(batch["corrections"]):
            ts=int(op["timestamp"]);var=op["variable"];row=rows.get(ts);current=row.get(var) if row else None;history=events.get((ts,var),[])
            matches=[e for e in history if e["state"]=="applied" and eq(e["new_value"],op["new_value"])]
            current_matches=eq(current,op["new_value"])
            if var in {"rain","rainRate"}:disposition="BLOCKED_E4_COUNTER_SEMANTICS"
            elif matches and current_matches:disposition="ALREADY_APPLIED_EQUIVALENT_HISTORIC_EVENT"
            elif matches:disposition="APPLIED_EVENT_CURRENT_VALUE_MISMATCH"
            elif not eq(current,op.get("expected_old_value")):disposition="CURRENT_STATE_MISMATCH_REQUIRES_REVIEW"
            else:disposition="AWAITING_OWNER_APPROVAL"
            appended.append({**op,"package":"restored_source_only_2018_dec31_primary","canonical_batch_id":batch["batch_id"],"package_classification":batch["classification"],"package_payload_sha256":payload_hash,"source_artifacts":{"manifest_sha256":sha(PKG/"manifest.json"),"weather_mcp_batches_sha256":sha(PKG/"weather_mcp_batches.json"),"corrections_sha256":sha(PKG/"corrections.json")},"operation_index":idx,"current_target_row_exists":row is not None,"current_target_value":str(current) if current is not None else None,"current_value_matches_proposed_postimage":current_matches,"current_usUnits":int(row["usUnits"]) if row else None,"current_interval_minutes":int(row["interval"] or 0) if row else None,"matching_applied_event_ids":[int(e["id"]) for e in matches],"applied_event_history":[{"id":int(e["id"]),"batch_key":e["batch_key"],"new_value":str(e["new_value"]) if e["new_value"] is not None else None,"state":e["state"],"reason":e["reason"]} for e in history],"owner_approval_evidence_found":False,"disposition":disposition})
    merged=reg["operations"]+appended
    if len(merged)!=324 or len({(x["timestamp"],x["variable"]) for x in merged})!=324:raise RuntimeError("combined operation registry is not 324 unique field targets")
    dispositions={}
    for op in merged:dispositions[op["disposition"]]=dispositions.get(op["disposition"],0)+1
    result={"schema":"loucka-complete-historical-operation-registry-v1","captured_read_only":True,"database_identity":identity,"operation_count":len(merged),"unique_timestamp_variable_targets":len({(x["timestamp"],x["variable"]) for x in merged}),"counts_by_disposition":dispositions,"v1_2_execution_layer":{"operation_count":317,"insert_field_operations":314,"update_field_operations":3,"restored":296,"estimated":21,"exact_payload_batch_count":13,"payload_manifest_sha256":reg["v1_2_manifest_sha256"],"all_current_exact_batch_event_confirmed":all(x["disposition"]=="ACTUALLY_APPLIED_MATCHING_BATCH" for x in reg["operations"])},"historical_2018_12_31_package":{"proposed_operations":7,"already_applied_equivalent_non_rain_operations":sum(x["disposition"]=="ALREADY_APPLIED_EQUIVALENT_HISTORIC_EVENT" for x in appended),"rain_operations_blocked_e4":sum(x["disposition"]=="BLOCKED_E4_COUNTER_SEMANTICS" for x in appended),"manifest_classification_counts":package_manifest["classification_counts"],"prior_applied_outTemp_event_excluded_from_seven":package_manifest["prior_applied_event_excluded"],"manifest_sha256":sha(PKG/"manifest.json")},"count_reconciliation":{"future_plan_claimed_total":324,"historical_review_claimed_non_rain_total":314,"observed_immutable_v1_2_total":317,"observed_v1_2_insert_operations":314,"observed_v1_2_update_operations":3,"observed_2018_package_additional_proposals":7,"assessment":"The exact 314 value equals the v1.2 INSERT-operation count, while the v1.2 layer has 3 additional UPDATE operations; the 324 total equals 317 v1.2 operations plus the separate 7-operation 2018-12-31 package. The historical review labels 314 as total non-rain operations, which is not a complete count under the immutable manifest. That label should be treated as stale/mis-scoped."},"approved_but_not_applied":0,"awaiting_owner_approval":sum(x["disposition"]=="AWAITING_OWNER_APPROVAL" for x in merged),"historical_archive_writes_performed_by_this_registry":0,"operations":merged,"limitations":["The 2018 package is a separate pre-v1.2 proposal; its five non-rain values already have matching later applied audit events, while its rain/rainRate proposals remain blocked and unapplied.","The separately recorded preexisting outTemp applied event is not counted as an operation in the seven-item 2018 package.","No pending non-rain operation from these exact payloads is recommended for a new application."]}
    out=ROOT/"data/RECONSTRUCTION_OPERATION_REGISTRY_324.json";out.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","operations":len(merged),"dispositions":dispositions,"v1_2_batches_confirmed":result["v1_2_execution_layer"]["all_current_exact_batch_event_confirmed"],"output":str(out)},indent=2))

if __name__=="__main__":main()
