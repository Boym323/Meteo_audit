#!/usr/bin/env python3
"""Build an immutable MCP execution layer from canonical v1.1 batch JSON."""
from __future__ import annotations
import hashlib, json, pathlib, re, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ZIP = ROOT / "loucka_complete_historical_data_audit_v1.1.zip"
ZIP_SHA_EXPECTED = "71b40577715de0a95459acbe60d342099467dc9dae1f6332cf01b861c10f721e"
SOURCES = {
 "restored_source_only_2013_july_pilot": ("RESTORED", "restored-source-only-2013-july-pilot"),
 "restored_rh_2014_boundary_pilot": ("RESTORED", "restored-rh-2014-boundary-pilot"),
 "restored_rh_2014_midpoint_pilot": ("RESTORED", "restored-rh-2014-midpoint-pilot"),
 "restored_source_only_2019_may30_outtemp": ("RESTORED", "restored-source-only-2019-may30-outtemp"),
 "restored_source_only_2020_isolated_outtemp": ("RESTORED", "restored-source-only-2020-isolated-outtemp"),
 "restored_source_only_2020_march_outtemp_v2": ("RESTORED", "restored-source-only-2020-march-outtemp-v2"),
 "restored_source_only_2022_august_outtemp": ("RESTORED", "restored-source-only-2022-august-outtemp"),
 "restored_source_only_2023_may_outtemp": ("RESTORED", "restored-source-only-2023-may-outtemp"),
 "estimated_short_temperature_gaps_v2": ("ESTIMATED", "p3-v2.1"),
}
OUT = ROOT / "execution_payloads" / "v1.2"
def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def jbytes(x) -> bytes: return (json.dumps(x, ensure_ascii=False, indent=2) + "\n").encode()
zip_bytes = ZIP.read_bytes()
assert sha(zip_bytes) == ZIP_SHA_EXPECTED, "canonical v1.1 ZIP hash changed"
for stale in (OUT / "batches").glob("*.json"):
 stale.unlink()
manifest = {
 "execution_version":"v1.2",
 "canonical_bundle":"loucka_complete_historical_data_audit_v1.1.zip",
 "canonical_bundle_sha256":ZIP_SHA_EXPECTED,
 "source_sha256_basis":"SHA-256 of exact weather_mcp_batches.json member bytes extracted from the canonical v1.1 ZIP",
 "batch_ids_are_new":True,
 "mcp_source_file_expected_sha256":"95d87c09608347aa50c21cf30befa4465f9bcddd34ad2b578804a49e55c465eb",
 "mcp_source_file_present_in_current_workspace":False,
 "batches":[],
 "total_field_operations":0,
 "technical_change_rules":[
  "Preserve timestamp, variable, new_value, expected_old_value, source_database, source_time, source_value, classification.",
  "Remove us_units and interval_minutes from UPDATE field objects; preserve those original metadata in canonical source and operation-diff evidence.",
  "Use only INSERT for the three new 2013 archive rows; keep UPDATE for the existing 2013 row.",
  "Use a concise MCP reason carrying classification and SHA-256 references to the original complete reason and canonical source batch. The full original reason remains byte-for-byte in the immutable v1.1 package."
 ]
}
with zipfile.ZipFile(ZIP) as z:
 for package,(classification,batch_prefix) in SOURCES.items():
  member=f"proposals/{package}/weather_mcp_batches.json"
  canonical_bytes=z.read(member); canonical_sha=sha(canonical_bytes)
  local=(ROOT/member).read_bytes()
  assert local==canonical_bytes, f"local proposal differs from canonical ZIP: {member}"
  raw=json.loads(canonical_bytes)
  batches=raw if isinstance(raw,list) else raw.get("batches",[])
  for b in batches:
   old_id=b["batch_id"]
   new_id=old_id.replace(".", "-") + "-exec-v12"
   assert 3 <= len(new_id) <= 64
   corrections=[]; op_diffs=[]
   for index,op0 in enumerate(b["operations"]):
    op=dict(op0); old_op=op["operation"]
    reason0=op["reason"]
    reason_sha=sha(reason0.encode())
    original_units=op.get("us_units")
    original_interval=op.get("interval_minutes")
    if package=="restored_source_only_2013_july_pilot" and op["timestamp"] in (1373319000,1373319600,1373320200) and op["variable"]=="outHumidity":
     assert old_op=="update"
     op["operation"]="insert"
     op["us_units"]=16
     op["interval_minutes"]=5
    if op["operation"]=="update":
     op.pop("us_units",None); op.pop("interval_minutes",None)
    compact = f"{classification}; MODERATE; reason={reason_sha}; batch={old_id}; payload={canonical_sha}."
    if classification=="ESTIMATED":
     compact = f"ESTIMATED; reason={reason_sha}; batch={old_id}; payload={canonical_sha}."
    if len(reason0)>245:
     op["reason"]=compact
    elif len(op["reason"])>245:
     op["reason"]=compact
    diffs=[]
    if old_id!=new_id: diffs.append({"field":"batch_id","from":old_id,"to":new_id})
    if old_op!=op["operation"]: diffs.append({"field":"operation","from":old_op,"to":op["operation"]})
    removed=[k for k in ("us_units","interval_minutes") if k in op0 and k not in op]
    if removed: diffs.append({"removed_update_only_fields":removed,"original_values":{"us_units":original_units,"interval_minutes":original_interval}})
    added=[k for k in ("us_units","interval_minutes") if k not in op0 and k in op]
    if added: diffs.append({"added_insert_metadata":{k:op[k] for k in added},"canonical_update_had_no_insert_metadata":True})
    if reason0!=op["reason"]:
     diffs.append({"field":"reason","from_sha256":reason_sha,"to_sha256":sha(op["reason"].encode()),"from_length":len(reason0),"to_length":len(op["reason"])})
    # This explicit allowlist guarantees no meteorological/source evidence changes.
    for k in ("timestamp","variable","new_value","expected_old_value","source_database","source_time","source_value"):
     assert op[k]==op0[k], f"forbidden operation change {package}/{old_id}/{k}"
    corrections.append(op)
    op_diffs.append({"operation_index":index,"timestamp":op["timestamp"],"variable":op["variable"],"changes":diffs})
   payload={
    "execution_version":"v1.2",
    "batch_id":new_id,
    "canonical_batch_id":old_id,
    "source_package":package,
    "classification":classification,
    "canonical_batch_payload_sha256":canonical_sha,
    "canonical_bundle_sha256":ZIP_SHA_EXPECTED,
    "corrections":corrections
   }
   dest=OUT/"batches"/f"{new_id}.json"
   dest.write_bytes(jbytes(payload))
   manifest["batches"].append({
    "batch_id":new_id,"canonical_batch_id":old_id,"source_package":package,
    "classification":classification,"operation_count":len(corrections),
    "payload_path":str(dest.relative_to(ROOT)),
    "payload_sha256":sha(dest.read_bytes()),
    "canonical_member":member,"canonical_member_sha256":canonical_sha,
    "diffs":op_diffs
   })
   manifest["total_field_operations"]+=len(corrections)
manifest["batches"].sort(key=lambda x:(x["source_package"],x["canonical_batch_id"]))
(OUT/"manifest.json").write_bytes(jbytes(manifest))
print(json.dumps({"batches":len(manifest["batches"]),"field_operations":manifest["total_field_operations"],"manifest_sha256":sha((OUT/"manifest.json").read_bytes())},indent=2))
