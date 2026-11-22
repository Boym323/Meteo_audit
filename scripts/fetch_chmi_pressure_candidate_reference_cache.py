#!/usr/bin/env python3
"""Fetch the official CHMI synoptic P_hm reference for two 2026 Loucka months."""
import csv,hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATION='0-20000-0-11774'
OUT=ROOT/'data/chmi-2026-synop-pressure'
MANIFEST=OUT/'manifest.json'
BASE='https://opendata.chmi.cz/meteorology/climate/recent/data/1hour'

def sha(b):return hashlib.sha256(b).hexdigest()

def official_station_metadata():
    path=ROOT/'data/publication-pilot-reference/chmi_station_metadata_meta1.csv'
    with path.open(encoding='utf-8-sig',newline='') as f:
        rows=[r for r in csv.DictReader(f) if r.get('WSI')==STATION and r.get('BEGIN_DATE','')<='2026-01-01T00:00Z' and r.get('END_DATE','')>='2026-02-28T23:00Z']
    if len(rows)!=1:raise SystemExit(f'Expected one active CHMI metadata row for {STATION}; found {len(rows)}')
    r=rows[0]
    return {'station_id':r['WSI'],'name':r['FULL_NAME'],'latitude':float(r['GEOGR2']),'longitude':float(r['GEOGR1']),'elevation_m':float(r['ELEVATION']),'valid_from_utc':r['BEGIN_DATE'],'valid_to_utc':r['END_DATE'],'metadata_source':'data/publication-pilot-reference/chmi_station_metadata_meta1.csv','metadata_source_sha256':sha(path.read_bytes())}

def main():
    OUT.mkdir(parents=True,exist_ok=True);old=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {'files':[]}
    entries={r['period']:r for r in old.get('files',[])};station=official_station_metadata()
    for period in ('2026-01','2026-02'):
        yyyymm=period.replace('-','');month=yyyymm[-2:]
        name=f'1h-{STATION}-{yyyymm}.json';url=f'{BASE}/{month}/{name}';path=OUT/'raw'/name;path.parent.mkdir(parents=True,exist_ok=True)
        response=urllib.request.urlopen(url,timeout=45);payload=response.read();digest=sha(payload)
        raw=json.loads(payload);items=raw['data']['data']['values'];p_hm=[r for r in items if r[0]==STATION and r[1]=='P_hm']
        if not p_hm:raise SystemExit(f'No P_hm rows in {url}')
        if path.exists() and sha(path.read_bytes())!=digest:raise SystemExit(f'Immutable cached reference changed: {path}; retain prior bytes and review a new version separately')
        if not path.exists():path.write_bytes(payload)
        retrieved=datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
        entries[period]={'period':period,'month':yyyymm,'path':str(path.relative_to(ROOT)),'url':url,'source_url':url,'sha256':digest,'bytes':len(payload),'retrieved_at_utc':retrieved,'http_last_modified':response.headers.get('Last-Modified'),'chmi_dataset':'recent 1hour SYNOP','station_id':STATION,'element':'P_hm','unit':'hPa','row_count':len(p_hm),'station':station}
    doc={'schema':'loucka-chmi-synop-pressure-reference-cache-v1','provider':'ČHMÚ','dataset':'recent 1-hour SYNOP sea-level pressure P_hm','retrieved_at_utc':max(x['retrieved_at_utc'] for x in entries.values()),'files':[entries[k] for k in sorted(entries)],'method':'Original CHMI JSON retained byte-for-byte; P_hm rows are parsed with quality code preserved in validation.'}
    MANIFEST.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'manifest':str(MANIFEST),'files':len(doc['files']),'rows':sum(x['row_count'] for x in doc['files'])},indent=2))

if __name__=='__main__':main()
