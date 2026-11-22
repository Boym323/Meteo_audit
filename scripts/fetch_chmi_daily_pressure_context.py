#!/usr/bin/env python3
"""Fetch the two nearby official CHMI historical daily air-pressure files once."""
from __future__ import annotations
import hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='https://opendata.chmi.cz/meteorology/climate/historical_csv/data/daily/air_pressure'
STATIONS={'0-203-0-11777':'Vizovice','0-203-0-11778':'Kladna-Zilin','0-20000-0-11774':'Holesov'}
STATION_METADATA={'0-20000-0-11774':{'latitude':49.320556,'longitude':17.57,'elevation_m':222.25,
  'valid_from_utc':'2009-07-01T00:00Z','metadata_source':'data/publication-pilot-reference/chmi_station_metadata_meta1.csv',
  'metadata_source_sha256':'3267b1808e7496a39f8c43a178c02832a9a2e2977209a44252a015fa1f5dc03e'}}
OUT=ROOT/'data/chmi-daily-pressure'
def main():
    (OUT/'raw').mkdir(parents=True,exist_ok=True); records=[]
    for station,name in STATIONS.items():
        filename=f'dly-{station}-P.csv';url=f'{BASE}/{filename}';path=OUT/'raw'/filename;content_type='cached'
        if path.exists():data=path.read_bytes();status='REUSED_IMMUTABLE_CACHE'
        else:
            req=urllib.request.Request(url,headers={'User-Agent':'Loucka-weather-audit/1.0'})
            with urllib.request.urlopen(req,timeout=60) as response:
                data=response.read()
                if response.status!=200:raise RuntimeError(f'CHMI HTTP {response.status}: {url}')
                content_type=response.headers.get('Content-Type')
            if not data.startswith(b'STATION,ELEMENT,TIMEFUNC,DT,VALUE,FLAG,QUALITY'):
                raise RuntimeError(f'Unexpected CHMI CSV header: {url}')
            temp=path.with_suffix(path.suffix+'.tmp');temp.write_bytes(data);temp.replace(path);status='FETCHED'
        records.append({'station_id':station,'station_name':name,**STATION_METADATA.get(station,{}),'filename':filename,'path':str(path.relative_to(ROOT)),
          'url':url,'http_status':200,'content_type':content_type,'bytes':len(data),
          'sha256':hashlib.sha256(data).hexdigest(),'status':status})
    manifest={'schema':'loucka-chmi-daily-pressure-cache-v1','provider':'Czech Hydrometeorological Institute (CHMI)',
      'dataset':'Historical daily air pressure (P); TIMEFUNC and pressure element semantics are preserved from source rows.',
      'source_base_url':BASE,'retrieved_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),
      'files':records,'usage_limits':['Regional aggregate context only; not equivalent to Loucka archive observations or a calibration standard.',
      'Retain element, TIMEFUNC, flag, and quality; only quality 0 values may enter numeric summaries.',
      'No interpolation, pressure reduction, or synthetic subdaily values.']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(OUT/'manifest.json'),'files':len(records),'bytes':sum(x['bytes'] for x in records),'statuses':[x['status'] for x in records]},indent=2))
if __name__=='__main__':main()
