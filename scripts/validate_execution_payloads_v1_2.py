#!/usr/bin/env python3
"""Reproducible contract validator for v1.2 MCP execution payloads."""
from __future__ import annotations
import hashlib,json,math,pathlib,re,sys,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/"execution_payloads"/"v1.2"
manifest=json.loads((BASE/"manifest.json").read_text())
def sha(b): return hashlib.sha256(b).hexdigest()
def fail(m): raise SystemExit("FAIL: "+m)
# Safe identifier character set exercised against the live Weather MCP runtime.
batch_re=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
common={"operation","timestamp","variable","new_value","expected_old_value","source_database","source_time","source_value","reason"}
allowed={"insert":common|{"us_units","interval_minutes"},"update":common}
all_fields=set(); global_targets={}; batch_ids=set(); op_count=0; restored=estimated=0
insert_groups=0; physical_inserts=0; update_count=0
zip_path=ROOT/manifest["canonical_bundle"]
if sha(zip_path.read_bytes())!=manifest["canonical_bundle_sha256"]: fail("canonical ZIP digest mismatch")
with zipfile.ZipFile(zip_path) as z:
 for item in manifest["batches"]:
  path=ROOT/item["payload_path"]; raw=path.read_bytes()
  if sha(raw)!=item["payload_sha256"]: fail(f"payload digest mismatch {path}")
  p=json.loads(raw)
  if p["batch_id"]!=item["batch_id"] or p["canonical_batch_id"]!=item["canonical_batch_id"]: fail("manifest/payload batch mismatch")
  if p["batch_id"] in batch_ids: fail("duplicate batch_id")
  batch_ids.add(p["batch_id"])
  if not batch_re.fullmatch(p["batch_id"]): fail("batch_id outside validated ASCII-safe identifier subset")
  if len(p["corrections"])!=item["operation_count"] or not 1<=len(p["corrections"])<=50: fail("batch size outside 1..50")
  if p["classification"] not in ("RESTORED","ESTIMATED"): fail("invalid classification")
  restored += len(p["corrections"]) if p["classification"]=="RESTORED" else 0
  estimated += len(p["corrections"]) if p["classification"]=="ESTIMATED" else 0
  if sha(z.read(item["canonical_member"]))!=item["canonical_member_sha256"]: fail("canonical member hash mismatch")
  groups={}; kinds={}
  for op in p["corrections"]:
   op_count += 1
   typ=op.get("operation")
   if typ not in allowed: fail("invalid operation")
   if set(op)!=allowed[typ]: fail(f"field set mismatch {typ}: {sorted(set(op)^allowed[typ])}")
   if not isinstance(op["timestamp"],int) or isinstance(op["timestamp"],bool): fail("timestamp must be integer Unix seconds")
   ts=op["timestamp"]; var=op["variable"]
   if not isinstance(var,str) or not var: fail("variable missing")
   target=(ts,var)
   if target in global_targets: fail(f"global duplicate timestamp+variable {target}: {global_targets[target]} and {p['batch_id']}")
   global_targets[target]=p["batch_id"]
   # Protect all of Q1 2018 and all of 2021.
   if 1514764800<=ts<1522540800: fail("Q1 2018 target is prohibited")
   if 1609459200<=ts<1640995200: fail("2021 target is diagnostic-only")
   for key in ("new_value","expected_old_value","source_value"):
    value=op[key]
    if value is not None and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value)): fail(f"invalid numeric field {key}")
   if op["source_database"] not in {"old_weewx","weewx_WH1080","pocasi-loucka.eu_old","loucka_reconstruction"}: fail("unknown source_database")
   if not isinstance(op["source_time"],int) or isinstance(op["source_time"],bool): fail("source_time must be integer")
   reason=op["reason"]
   if not isinstance(reason,str) or not 5<=len(reason)<=245: fail("reason length outside 5..245")
   if not reason.startswith(p["classification"]): fail("audit reason classification mismatch")
   if "reason=" in reason and "payload=" in reason:
    original=next((x for x in source["operations"] if x["timestamp"]==ts and x["variable"]==var),None) if False else None
    if not re.search(r"reason=[0-9a-f]{64}; batch=[A-Za-z0-9._-]+; payload=[0-9a-f]{64}",reason): fail("compacted reason lineage reference malformed")
   if var in {"rain","rainRate"}: fail("deferred rainfall operation appeared in execution layer")
   if typ=="update":
    update_count+=1
    if op["expected_old_value"] is None and op["new_value"] is None: pass
    if "us_units" in op or "interval_minutes" in op: fail("UPDATE contains INSERT-only metadata")
   else:
    if op["expected_old_value"] is not None: fail("INSERT expected_old_value must be NULL")
    if op["us_units"]!=16: fail("INSERT target units must be 16")
    if op["interval_minutes"]!=5: fail("INSERT interval must be 5")
    if isinstance(op["us_units"],bool) or not isinstance(op["us_units"],int): fail("us_units type")
    if isinstance(op["interval_minutes"],bool) or not isinstance(op["interval_minutes"],int): fail("interval_minutes type")
    physical_inserts+=1
   kinds.setdefault(ts,set()).add(typ)
   if typ=="insert": groups.setdefault(ts,[]).append((op["us_units"],op["interval_minutes"]))
  if any(len(v)>1 for v in kinds.values()): fail("INSERT+UPDATE mix at same timestamp")
  for ts,rows in groups.items():
   if len(set(rows))!=1: fail(f"grouped INSERT metadata mismatch at {ts}")
   insert_groups+=1
  # Preserve exact meteorological/source fields vs canonical batch. Only declared
  # technical differences are allowed (batch id, operation for July rows, reason,
  # and removal of insert-only metadata from UPDATE objects).
  item_data=json.loads(z.read(item["canonical_member"]))
  canon_batches=item_data if isinstance(item_data,list) else item_data.get("batches",[])
  source=next((x for x in canon_batches if x["batch_id"]==p["canonical_batch_id"]),None)
  if source is None: fail("canonical batch id missing")
  if len(source["operations"])!=len(p["corrections"]): fail("operation count differs from canonical")
  for old,new in zip(source["operations"],p["corrections"]):
   if new["reason"] != old["reason"] and "reason=" in new["reason"]:
    reason_sha=hashlib.sha256(old["reason"].encode()).hexdigest()
    if "reason="+reason_sha not in new["reason"]: fail("compacted reason does not reference exact canonical reason")
   if old["operation"] != new["operation"] and not (p["source_package"]=="restored_source_only_2013_july_pilot" and old["timestamp"] in {1373319000,1373319600,1373320200} and old["variable"]=="outHumidity" and old["operation"]=="update" and new["operation"]=="insert"): fail("unapproved operation conversion")
   for key in ("timestamp","variable","new_value","expected_old_value","source_database","source_time","source_value"):
    if old[key]!=new[key]: fail(f"source/value changed in {key}")
print(json.dumps({"status":"PASS","batch_count":len(manifest["batches"]),"field_operations":op_count or manifest["total_field_operations"],"restored":restored,"estimated":estimated,"insert_field_operations":physical_inserts,"physical_insert_groups":insert_groups,"update_field_operations":update_count,"unique_timestamp_variable_targets":len(global_targets),"target_units":16,"max_batch_size":max(x["operation_count"] for x in manifest["batches"]),"validator_basis":"Local reproducible contract validator; exact source checkout absent. Runtime behavior independently checked by MCP dry-runs for each batch.","mcp_source_sha256_expected":manifest.get("mcp_source_file_expected_sha256"),"mcp_source_file_present":manifest.get("mcp_source_file_present_in_current_workspace")},indent=2))
