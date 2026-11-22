#!/usr/bin/env python3
"""Fetch official CHMI 10-minute T/RH winter files for two nearby stations.

Only public historical CSVs are fetched. The output is an immutable local cache
with URL, retrieval time, byte size, and SHA-256 manifest; no database writes.
"""
from __future__ import annotations
import csv,hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='https://opendata.chmi.cz/meteorology/climate/historical_csv/data/10min'
STATIONS={'0-203-0-11777':'Vizovice','0-203-0-11778':'Kladná-Žilín'}
YEARS=(2019,2020,2021,2022)
MONTHS=(1,2)
ELEMENTS={'H':'humidity','T':'temperature'}
OUT=ROOT/'data/chmi-rh-winter-validation/raw';OUT.mkdir(parents=True,exist_ok=True)
entries=[]
for year in YEARS:
 for month in MONTHS:
  ym=f'{year}{month:02d}'
  for station,name in STATIONS.items():
   for element,subdir in ELEMENTS.items():
    filename=f'10m-{station}-{element}-{ym}.csv'
    url=f'{BASE}/{subdir}/{year}/{filename}'
    path=OUT/filename
    if not path.exists():
     req=urllib.request.Request(url,headers={'User-Agent':'Loucka historical audit/1.0'})
     with urllib.request.urlopen(req,timeout=45) as response:
      if response.status!=200:raise RuntimeError(f'HTTP {response.status}: {url}')
      data=response.read()
     path.write_bytes(data)
    data=path.read_bytes()
    if not data.startswith(b'STATION,ELEMENT,DT,VALUE,FLAG,QUALITY,'):
     raise ValueError(f'Unexpected CHMI CSV header: {filename}')
    # Verify every record belongs to this file's station and element.
    with path.open(newline='',encoding='utf-8') as stream:
     rd=csv.DictReader(stream)
     rows=list(rd)
    if not rows or any(r['STATION']!=station or r['ELEMENT']!=element for r in rows):
     raise ValueError(f'Station/element mismatch or empty file: {filename}')
    entries.append({'path':str(path.relative_to(ROOT)),'url':url,'station':station,'station_name':name,'element':element,'year':year,'month':month,'rows':len(rows),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'first_dt':rows[0]['DT'],'last_dt':rows[-1]['DT'],'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'protected_scope':('2021 diagnostic_only' if year==2021 else ('2022 target_context' if year==2022 else 'historical_validation'))})
manifest={'dataset':'CHMI official historical 10-minute temperature and relative humidity','license':'CC BY 4.0 as specified in local reference inventory; verify attribution on redistribution','scope_years':list(YEARS),'months':[1,2],'stations':STATIONS,'elements':ELEMENTS,'records_total':sum(x['rows'] for x in entries),'files':entries,'database_access':'none','writes_or_staging':False}
(ROOT/'data/chmi-rh-winter-validation/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files':len(entries),'rows':manifest['records_total'],'bytes':sum(x['bytes'] for x in entries)},indent=2))
