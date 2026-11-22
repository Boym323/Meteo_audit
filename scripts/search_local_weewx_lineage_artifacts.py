#!/usr/bin/env python3
"""Read-only filename search for local historical WeeWX config/backup artifacts.
Searches the container-visible root filesystem on one device only; never reads file content.
"""
import json,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cmd=['find','/','-xdev','-type','f','(','-iname','weewx.conf','-o','-iname','weewx.conf.*','-o','-iname','*weewx*.archive','-o','-iname','*weewx*.sql','-o','-iname','*weather*.dump','-o','-iname','*weewx*.backup','-o','-iname','*weewx*.tar*',')','-printf','%p\t%s\t%TY-%Tm-%Td\n']
r=subprocess.run(cmd,capture_output=True,text=True,check=True)
found=[]
for line in r.stdout.splitlines():
 fields=line.split('\t')
 if len(fields)==3:found.append({'path':fields[0],'bytes':int(fields[1]),'modified_date':fields[2]})
mounts=subprocess.run(['findmnt','-rn','-o','TARGET,SOURCE,FSTYPE'],capture_output=True,text=True,check=True).stdout.splitlines()
backup_mounts=[x for x in mounts if x.split(' ',1)[0].startswith(('/mnt','/media','/backup','/backups'))]
zfs_cli=shutil.which('zfs')
result={'search':'find / -xdev with config/archive/sql/dump/backup filename patterns','content_read':False,'matched_files':found,'matched_count':len(found),'container_visible_root_mount':next((x for x in mounts if x.startswith('/ ')),None),'dedicated_backup_mounts':backup_mounts,'zfs_cli_available':bool(zfs_cli),'host_zfs_snapshots_visible':False if not zfs_cli else 'not assessed','limitation':'Host-level ZFS snapshots and external backup systems are not visible from this container; no file contents were read.'}
(ROOT/'reports/2026-11-13-local-weewx-lineage-search.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
lines=['# Local search for historical WeeWX lineage artifacts','', '**Date:** 2026-11-13. Filename-only, read-only search; file contents were not opened.','',f"Searched the container-visible root filesystem on one device for historical `weewx.conf`, `.archive`, SQL dump, weather dump, backup and tar patterns. Matches: **{len(found)}**.",'',f"Container root mount: `{result['container_visible_root_mount']}`. Dedicated backup mounts under `/mnt`, `/media`, `/backup`, or `/backups`: {len(backup_mounts)}. ZFS CLI available: {'yes' if zfs_cli else 'no'}.",'','## Interpretation','', 'This result does not prove that no backup exists on the host or in an external repository. The container cannot inspect host-level ZFS snapshots because `zfs` is unavailable, and no dedicated backup mount is present. No archive lineage is authenticated, so source-only candidates remain REVIEW_REQUIRED and no pilot RESTORED package is authorized by this evidence.','', 'Reproduction: `scripts/search_local_weewx_lineage_artifacts.py`; machine result: `reports/2026-11-13-local-weewx-lineage-search.json`.','']
(ROOT/'reports/2026-11-13-local-weewx-lineage-search.md').write_text('\n'.join(lines))
print(json.dumps({'matched_count':len(found),'backup_mounts':len(backup_mounts),'zfs_cli_available':bool(zfs_cli),'root_mount':result['container_visible_root_mount']}))
