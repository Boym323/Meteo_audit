#!/usr/bin/env python3
"""Fetch immutable official CHMI daily relative-humidity context files."""
from __future__ import annotations
import hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE='https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/humidity'
STATIONS={'0-203-0-11777':'Vizovice','0-203-0-11778':'Kladna-Zilin'}
OUT=ROOT/'data/chmi-daily-humidity'

def main():
    (OUT/'raw').mkdir(parents=True,exist_ok=True)
    records=[]
    for station,name in STATIONS.items():
        filename=f'dly-{station}-H.csv';url=f'{BASE}/{filename}';path=OUT/'raw'/filename
        content_type='cached'
        if path.exists():
            data=path.read_bytes()
            status='REUSED_IMMUTABLE_CACHE'
        else:
            request=urllib.request.Request(url,headers={'User-Agent':'Loucka-weather-audit/1.0'})
            with urllib.request.urlopen(request,timeout=60) as response:
                data=response.read()
                if response.status!=200:raise RuntimeError(f'CHMI HTTP {response.status}: {url}')
                content_type=response.headers.get('Content-Type')
            if not data.startswith(b'STATION,ELEMENT,TIMEFUNC,DT,VALUE,FLAG,QUALITY'):
                raise RuntimeError(f'Unexpected CHMI CSV header: {url}')
            temp=path.with_suffix(path.suffix+'.tmp');temp.write_bytes(data);temp.replace(path)
            status='FETCHED'
        records.append({'station_id':station,'station_name':name,'filename':filename,'path':str(path.relative_to(ROOT)),
          'url':url,'http_status':200,'content_type':content_type,
          'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'status':status})
    manifest={'schema':'loucka-chmi-daily-humidity-cache-v1','provider':'Czech Hydrometeorological Institute (CHMI)',
      'dataset':'Historical daily relative air humidity (H, TIMEFUNC=AVG); values are daily context, not subdaily equivalents.',
      'source_base_url':BASE,'retrieved_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),
      'files':records,'usage_limits':['Regional daily context only; do not equate with Loucka subdaily monthly means.',
      'Retain CHMI quality flags and exclude nonzero/missing quality from quantitative context.',
      'No interpolation or synthetic subdaily values.']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT/'manifest.json'),'files':len(records),'bytes':sum(x['bytes'] for x in records),'statuses':[x['status'] for x in records]},indent=2))
if __name__=='__main__':main()
