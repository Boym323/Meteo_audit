#!/usr/bin/env python3
"""Build the single final deliverable ZIP, excluding work caches, environments and prior ZIPs."""
import hashlib, json, os, shutil, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'loucka_complete_historical_data_audit_v1.zip'
MAN='FINAL_BUNDLE_MANIFEST.json'
EXCLUDED_DIRS={'.git','.venv','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','runs','tmp','node_modules'}

def skip(rel:Path):
 if any(part in EXCLUDED_DIRS for part in rel.parts): return True
 if rel.name.endswith('.zip') or rel.name=='final_bundle_validation.json' or rel.suffix in {'.pyc','.pyo'}: return True
 if rel.name=='.env' or rel.name in {'FINAL_BUNDLE_MANIFEST.sha256','FINAL_BUNDLE_MANIFEST.json'} or rel.name.endswith('.zip.sha256'): return True
 return False

def main():
 stamp=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
 with tempfile.TemporaryDirectory(prefix='loucka-final-build-') as td:
  stage=Path(td)/'payload';stage.mkdir()
  for src in ROOT.rglob('*'):
   rel=src.relative_to(ROOT)
   if skip(rel): continue
   if src.is_symlink(): continue
   dst=stage/rel
   if src.is_dir(): dst.mkdir(parents=True,exist_ok=True)
   elif src.is_file(): dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
  files=[]
  for f in sorted(x for x in stage.rglob('*') if x.is_file() and x.name!=MAN):
   b=f.read_bytes();files.append({'path':f.relative_to(stage).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
  manifest={'schema':'loucka-final-audit-bundle-v1','created_utc':stamp,'files_count':len(files),'files':files,'self_hash_note':'The manifest is intentionally excluded from its own file list; its SHA-256 is recorded in the detached MANIFEST.sha256 sidecar.'}
  (stage/MAN).write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
  shutil.copy2(stage/MAN,ROOT/MAN)
  tmp=OUT.with_suffix('.zip.tmp')
  with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
   for f in sorted(x for x in stage.rglob('*') if x.is_file()):z.write(f,f.relative_to(stage).as_posix())
  tmp.replace(OUT)
  digest=hashlib.sha256(OUT.read_bytes()).hexdigest()
  OUT.with_suffix('.zip.sha256').write_text(f'{digest}  {OUT.name}\n')
  manhash=hashlib.sha256((stage/MAN).read_bytes()).hexdigest()
  (ROOT/'FINAL_BUNDLE_MANIFEST.sha256').write_text(f'{manhash}  {MAN}\n')
  print(json.dumps({'archive':str(OUT),'created_utc':stamp,'payload_files':len(files),'archive_bytes':OUT.stat().st_size,'archive_sha256':digest,'manifest_sha256':manhash},indent=2))
if __name__=='__main__':main()
