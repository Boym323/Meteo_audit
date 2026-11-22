#!/usr/bin/env python3
"""Produce final read-only MariaDB and local artifact evidence."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT_DIR=Path(__file__).resolve().parent
sys.path[:]=[p for p in sys.path if not p or Path(p).resolve()!=SCRIPT_DIR]
sys.path.insert(0,str(ROOT/"production-existing-account-v1.2/src"))
from meteo_audit.archive_sync import ARCHIVE_FIELDS,PROTECTED_LOWER_BOUND
from meteo_audit.archive_sync_writer import (pymysql_connection_from_env,read_bounded_source_rows,TARGET_SCHEMA,_canonical_hash,_db_values_equal)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def props(unit,keys):
    x=subprocess.run(["systemctl","show",unit,"--property="+",".join(keys),"--no-pager"],capture_output=True,text=True)
    return {k:v for line in x.stdout.splitlines() if "=" in line for k,v in [line.split("=",1)]}

def main():
    s=pymysql_connection_from_env("pocasi-loucka.eu",readonly=True);t=pymysql_connection_from_env("loucka_reconstruction",readonly=True)
    db={}
    try:
        q=s.cursor();q.execute("SELECT VERSION() AS version,@@hostname AS hostname,CURRENT_USER() AS account,COUNT(*) AS source_count,MAX(`dateTime`) AS source_max FROM `pocasi-loucka.eu`.`archive`");ident=q.fetchone();sv,sh,account,source_count,source_max=ident["version"],ident["hostname"],ident["account"],ident["source_count"],ident["source_max"];q.close()
        q=t.cursor();q.execute("SELECT VERSION() AS version,@@hostname AS hostname,COUNT(*) AS n,MIN(`dateTime`) AS min_ts,MAX(`dateTime`) AS max_ts FROM `loucka_reconstruction`.`archive`");ident=q.fetchone();tv,th,target_count,target_min,target_max=ident["version"],ident["hostname"],ident["n"],ident["min_ts"],ident["max_ts"]
        q.execute("SELECT `sync_name`,`watermark`,`last_batch_id` FROM `loucka_reconstruction`.`archive_sync_cursor` ORDER BY `sync_name`");cursors=[dict(x) for x in q.fetchall()]
        q.execute("SELECT COUNT(*) AS n FROM `loucka_reconstruction`.`archive_sync_audit` WHERE `batch_id` LIKE 'gw3000-%'");audit_count=int(q.fetchone()["n"])
        q.execute("SELECT COUNT(*) AS n FROM `loucka_reconstruction`.`archive_sync_verification` WHERE `batch_id` LIKE 'gw3000-%'");verification_count=int(q.fetchone()["n"])
        q.execute("SELECT COUNT(DISTINCT a.`batch_id`) AS n FROM `loucka_reconstruction`.`archive_sync_audit` a LEFT JOIN `loucka_reconstruction`.`archive_sync_verification` v ON v.`batch_id`=a.`batch_id` WHERE a.`batch_id` LIKE 'gw3000-%' AND v.`batch_id` IS NULL");unverified=int(q.fetchone()["n"])
        q.execute("SELECT * FROM `loucka_reconstruction`.`archive` WHERE `dateTime`=%s",(PROTECTED_LOWER_BOUND,));protected=q.fetchone()
        q.execute("SHOW CREATE TABLE `pocasi-loucka.eu`.`archive`");source_ddl=next(v for k,v in q.fetchone().items() if str(k).lower().startswith("create"))
        q.execute("SHOW CREATE TABLE `loucka_reconstruction`.`archive`");target_ddl=next(v for k,v in q.fetchone().items() if str(k).lower().startswith("create"))
        q.execute("SHOW GRANTS FOR CURRENT_USER");grants=[str(next(iter(x.values()))) for x in q.fetchall()]
        q.close();t.rollback()
        source_rows=read_bounded_source_rows(s,PROTECTED_LOWER_BOUND, int(source_max)+1)
        cols=",".join(f"`{x}`" for x in sorted(ARCHIVE_FIELDS))
        q=t.cursor();q.execute(f"SELECT {cols} FROM `loucka_reconstruction`.`archive` WHERE `dateTime`>%s AND `dateTime`<=%s ORDER BY `dateTime`",(PROTECTED_LOWER_BOUND,int(source_max)));target_rows=q.fetchall();q.close()
        src={int(r["dateTime"]):r for r in source_rows};dst={int(r["dateTime"]):r for r in target_rows}
        missing=sorted(set(src)-set(dst));extra=sorted(set(dst)-set(src));different=[]
        for ts in set(src)&set(dst):
            if any(not _db_values_equal(src[ts][k],dst[ts][k]) for k in ARCHIVE_FIELDS):different.append(ts)
        db={"source_server_version":sv,"target_server_version":tv,"source_server_hostname":sh,"target_server_hostname":th,"connected_account":account,"source_archive_rows":int(source_count),"source_max_timestamp":int(source_max),"target_archive_rows":int(target_count),"target_min_timestamp":int(target_min),"target_max_timestamp":int(target_max),"post_protection_source_rows":len(src),"post_protection_target_rows":len(dst),"full_row_values_compared":len(set(src)&set(dst))*len(ARCHIVE_FIELDS),"missing_target_timestamps":missing,"target_only_timestamps":extra,"differing_timestamps":sorted(different),"gw3000_audit_rows":audit_count,"gw3000_verification_batches":verification_count,"unverified_gw3000_batches":unverified,"cursors":cursors,"protected_row_sha256":_canonical_hash(protected),"source_archive_ddl_sha256":hashlib.sha256(source_ddl.encode()).hexdigest(),"target_archive_ddl_sha256":hashlib.sha256(target_ddl.encode()).hexdigest(),"current_account_has_grant_option":any("WITH GRANT OPTION" in x.upper() for x in grants)}
    finally:s.close();t.close()
    health=json.loads(Path("/var/lib/loucka-archive-sync/health.json").read_text())
    reconcile=json.loads(Path("/var/lib/loucka-archive-sync/periodic-reconcile.json").read_text())
    try:stats=json.loads((ROOT/"data/STATISTICAL_READINESS_CURRENT.json").read_text());stats_snapshot=stats["snapshot"]
    except Exception:stats_snapshot=None
    local={"sync_service":props("loucka-archive-sync.service",["ActiveState","SubState","Result"]),"sync_timer":props("loucka-archive-sync.timer",["ActiveState","UnitFileState","NextElapseUSecRealtime"]),"reconcile_service":props("loucka-archive-reconcile.service",["ActiveState","SubState","Result"]),"reconcile_timer":props("loucka-archive-reconcile.timer",["ActiveState","UnitFileState","NextElapseUSecRealtime"]),"continuous_health":health,"periodic_reconcile":reconcile,"statistics_snapshot":stats_snapshot}
    files=["scripts/build_authoritative_statistical_readiness.py","scripts/finalize_authoritative_statistical_outputs.py","scripts/build_master_archive_evidence.py","scripts/package_master_archive_completion.py","tests/test_authoritative_statistical_readiness.py","production-existing-account-v1.2/scripts/archive_sync_cli.py","production-existing-account-v1.2/scripts/periodic_readonly_reconcile.py","production-existing-account-v1.2/src/meteo_audit/archive_sync_writer.py","production-existing-account-v1.2/src/meteo_audit/archive_sync_frozen.py","production-existing-account-v1.2/deploy/loucka-archive-sync.service","production-existing-account-v1.2/deploy/loucka-archive-sync.timer","production-existing-account-v1.2/deploy/loucka-archive-reconcile.service","production-existing-account-v1.2/deploy/loucka-archive-reconcile.timer","STATISTICAL_READINESS_CURRENT_REPORT.md","MASTER_GOAL_HISTORICAL_REVIEW_2026-11-15.md","GW3000_ARCHIVE_SYNC_RUNBOOK.md"]
    artifact_hashes={f:sha(ROOT/f) for f in files if (ROOT/f).is_file()}
    evidence={"schema":"loucka-master-archive-completion-evidence-v1","captured_utc":datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"),"database":db,"local_operations":local,"artifact_sha256":artifact_hashes,"known_limitations":["Historical lineage for rows without exact audit evidence remains unknown and publication readiness is not inferred.","Rain/rainRate remain excluded pending E4 counter semantics.","Existing account retains target-scoped WITH GRANT OPTION; grants were not changed.","Database backups were not restored or tested during this goal; this is disclosed in existing historical audit evidence."]}
    evidence["expected_protected_row_sha256"]="da936e263207cdd13e7a3745a2b4dc02a4f94fb6b534cbba8021fc63548f34fa"
    evidence["status"]="PASS" if not (db["missing_target_timestamps"] or db["target_only_timestamps"] or db["differing_timestamps"] or db["unverified_gw3000_batches"] or db["source_archive_ddl_sha256"]!=db["target_archive_ddl_sha256"] or db["protected_row_sha256"]!=evidence["expected_protected_row_sha256"] or local["continuous_health"].get("status")!="HEALTHY" or local["periodic_reconcile"].get("status")!="PASS" or local["sync_timer"].get("ActiveState")!="active" or local["reconcile_timer"].get("ActiveState")!="active") else "REVIEW_REQUIRED"
    out=ROOT/"MASTER_GOAL_ARCHIVE_COMPLETION_EVIDENCE.json";out.write_text(json.dumps(evidence,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
    print(json.dumps({"status":evidence["status"],"source_rows":db["post_protection_source_rows"],"target_rows":db["post_protection_target_rows"],"fields_compared":db["full_row_values_compared"],"missing":len(db["missing_target_timestamps"]),"extra":len(db["target_only_timestamps"]),"differences":len(db["differing_timestamps"]),"unverified_batches":db["unverified_gw3000_batches"],"continuous_health":health.get("status"),"periodic_reconcile":reconcile.get("status")},indent=2))

if __name__=="__main__":main()
