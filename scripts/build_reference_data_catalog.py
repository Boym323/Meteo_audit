#!/usr/bin/env python3
"""Summarize local public-reference caches from their manifests."""
import json,csv
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
manifest_paths=sorted((ROOT/'data').glob('*/manifest.json'))
datasets=[]; all_files={}
for mp in manifest_paths:
    raw=json.loads(mp.read_text())
    if isinstance(raw,list): entries=raw; provider='ČHMÚ'; dataset='historical 10-minute station series 2018'
    elif mp.parent.name=='chmi-rain-window':
        entries=list(raw.get('daily_sources',[]))+list(raw.get('subdaily_sources_reused',[])); provider='ČHMÚ'; dataset='daily SRA and reused 10-minute SRA10M window cross-check'
    else:
        entries=raw.get('files',[]); provider=raw.get('provider','ČHMÚ'); dataset=raw.get('dataset',mp.parent.name)
    downloaded=[]; missing=[]
    for e in entries:
        rel=e.get('path')
        if not rel and e.get('url') and mp.parent.name=='chmi-2018': rel='data/chmi-2018/raw/'+Path(urlparse(e['url']).path).name
        if not rel: continue
        fp=ROOT/rel
        if not fp.exists(): fp=mp.parent/rel
        if e.get('status'):
            status=e['status']
        elif mp.parent.name=='chmi-rain-window' and str(rel).startswith('data/chmi-2018/'):
            status='reused_existing'
        elif fp.exists() or e.get('http_status')==200:
            status='downloaded'
        else:
            status='unavailable'
        rec={'path':str(fp.relative_to(ROOT)) if fp.exists() else rel,'url':e.get('url'),'bytes_manifest':int(e.get('bytes') or 0),'sha256_manifest':e.get('sha256'),'status':status,'station_id':e.get('station_id',e.get('station')),'element':e.get('element'),'month':e.get('month')}
        if fp.exists() and status not in ('unavailable_http_404','unavailable'):
            rec['bytes_actual']=fp.stat().st_size
            downloaded.append(rec); all_files[str(fp.resolve())]=rec
        else: missing.append(rec)
    datasets.append({'dataset_id':mp.parent.name,'provider':provider,'dataset':dataset,'manifest':str(mp.relative_to(ROOT)),'retrieved_at_utc':raw.get('retrieved_at_utc') if isinstance(raw,dict) else None,'manifest_entries':len(entries),'existing_file_references':len(downloaded),'unavailable_or_missing_entries':len(missing),'existing_bytes':sum(x['bytes_actual'] for x in downloaded),'files':downloaded,'missing_entries':missing})
out={'generated_from_manifests':[str(p.relative_to(ROOT)) for p in manifest_paths],'distinct_existing_file_count':len(all_files),'distinct_existing_bytes':sum(x['bytes_actual'] for x in all_files.values()),'datasets':datasets}
target=ROOT/'data/reference-inventory/reference_source_catalog.json';target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (ROOT/'reports/2026-11-13-reference-cache-manifest-summary.csv').open('w',newline='') as f:
    fields=['dataset_id','provider','dataset','retrieved_at_utc','manifest_entries','existing_file_references','unavailable_or_missing_entries','existing_bytes','manifest']
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for d in datasets:w.writerow({k:d.get(k) for k in fields})
print(f'{len(datasets)} datasets; {len(all_files)} distinct cache files; {out["distinct_existing_bytes"]} bytes')
