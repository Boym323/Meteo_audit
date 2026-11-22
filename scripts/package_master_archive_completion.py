#!/usr/bin/env python3
"""Create a checksum-manifested local completion handoff ZIP."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib,json,shutil,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STAGE=Path("/tmp/loucka_master_archive_completion_v1")
ZIP=ROOT/"loucka_master_archive_completion_v1.zip"

def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def main():
    if STAGE.exists():shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    exact=[
        "MASTER_GOAL_ARCHIVE_COMPLETION_REPORT.md","MASTER_GOAL_ARCHIVE_COMPLETION_EVIDENCE.json","MASTER_GOAL_ARCHIVE_PROGRESS.json",
        "MASTER_GOAL_HISTORICAL_REVIEW_2026-11-15.md","MASTER_GOAL_STATISTICAL_READINESS_METHOD.md","STATISTICAL_READINESS_CURRENT_REPORT.md","GW3000_ARCHIVE_SYNC_RUNBOOK.md",
        "GW3000_FROZEN_BACKFILL_PRODUCTION_REPORT.md","GW3000_FROZEN_BOUNDARY_FIX_REPORT.md","LOUCKA_REMAINING_COMPLETION_FINAL_REPORT.md","FUTURE_RECONSTRUCTION_PLAN.md","UNIFIED_ARCHIVE_BLOCKERS.md",
        "scripts/build_authoritative_statistical_readiness.py","scripts/finalize_authoritative_statistical_outputs.py","scripts/build_master_archive_evidence.py","scripts/package_master_archive_completion.py",
        "tests/test_authoritative_statistical_readiness.py","data/applied_estimated_operations.json","data/GW3000_INSERT_ONLY_BACKFILL_MANIFEST.json","data/GW3000_INSERT_ONLY_BACKFILL_PAYLOAD.jsonl","data/GW3000_INSERT_ONLY_BACKFILL_ROW_HASHES.json",
        "data/catchup_snapshots/20261115T130027Z/manifest.json","data/catchup_snapshots/20261115T130027Z/payload.jsonl",
        "data/DAILY_STATISTICAL_READINESS_CURRENT.csv","data/MONTHLY_STATISTICAL_READINESS_CURRENT.csv","data/ANNUAL_STATISTICAL_READINESS_CURRENT.csv","data/STATISTICAL_PROVENANCE_CURRENT.csv","data/STATISTICAL_MISSING_DATA_CURRENT.csv","data/STATISTICAL_PUBLICATION_BLOCKERS_CURRENT.csv","data/STATISTICAL_RECONSTRUCTION_RECOMMENDATIONS_CURRENT.csv","data/STATISTICAL_READINESS_CURRENT.json","data/STATISTICAL_READINESS_VALIDATION.json",
    ]
    for rel in exact:
        src=ROOT/rel
        if not src.is_file():raise FileNotFoundError(src)
        dst=STAGE/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    # Include the complete self-contained approved runner, manifests, SQL, tests,
    # deployment files, and offline MariaDB harness. Do not package pycache.
    srcroot=ROOT/"production-existing-account-v1.2";dstroot=STAGE/"production-existing-account-v1.2"
    shutil.copytree(srcroot,dstroot,ignore=shutil.ignore_patterns("__pycache__",".venv*"))
    state=STAGE/"runtime_evidence";state.mkdir()
    for name,src in (("continuous-health.json",Path("/var/lib/loucka-archive-sync/health.json")),("weekly-readonly-reconcile.json",Path("/var/lib/loucka-archive-sync/periodic-reconcile.json"))):
        shutil.copy2(src,state/name)
    intro=STAGE/"README.md"
    intro.write_text("# Loučka master archive completion handoff\n\nSee MASTER_GOAL_ARCHIVE_COMPLETION_REPORT.md for results and limitations. `PACKAGE-MANIFEST.json` lists the SHA-256 digest of every other package file. Runtime credentials are intentionally excluded. The statistical snapshot is read-only and no historical correction candidates are executable.\n",encoding="utf-8")
    files=[]
    for f in sorted(x for x in STAGE.rglob("*") if x.is_file() and x.name!="PACKAGE-MANIFEST.json"):
        files.append({"path":f.relative_to(STAGE).as_posix(),"size_bytes":f.stat().st_size,"sha256":digest(f)})
    manifest={"schema":"loucka-master-archive-completion-package-v1","created_utc":datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"),"file_count":len(files),"files":files}
    (STAGE/"PACKAGE-MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if ZIP.exists():ZIP.unlink()
    with zipfile.ZipFile(ZIP,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(x for x in STAGE.rglob("*") if x.is_file()):z.write(f,f.relative_to(STAGE).as_posix())
    with zipfile.ZipFile(ZIP) as z:
        bad=z.testzip()
        if bad:raise RuntimeError(f"corrupt ZIP member: {bad}")
        m=json.loads(z.read("PACKAGE-MANIFEST.json"))
        for row in m["files"]:
            data=z.read(row["path"])
            if len(data)!=row["size_bytes"] or hashlib.sha256(data).hexdigest()!=row["sha256"]:
                raise RuntimeError(f"package hash validation failed: {row['path']}")
    (ROOT/"loucka_master_archive_completion_v1.zip.sha256").write_text(f"{digest(ZIP)}  {ZIP.name}\n",encoding="ascii")
    print(json.dumps({"status":"PASS","zip":str(ZIP),"zip_size_bytes":ZIP.stat().st_size,"zip_sha256":digest(ZIP),"package_files":len(files),"manifest_sha256":digest(STAGE/"PACKAGE-MANIFEST.json")},indent=2))

if __name__=="__main__":main()
