#!/usr/bin/env python3
"""Check frozen CHMI daily humidity files against their manifest and CSV schema."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 m=json.loads((ROOT/'data/chmi-daily-humidity/manifest.json').read_text())
 if len(m.get('files',[]))!=2:raise SystemExit('Expected exactly two frozen CHMI daily humidity files')
 summaries=[]
 for item in m['files']:
  p=ROOT/item['path']; raw=p.read_bytes()
  if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise SystemExit(f"Manifest mismatch: {item['path']}")
  with p.open(encoding='utf-8-sig',newline='') as stream:
   reader=csv.DictReader(stream)
   required={'STATION','ELEMENT','TIMEFUNC','DT','VALUE','FLAG','QUALITY'}
   if not required.issubset(set(reader.fieldnames or [])):raise SystemExit(f"Unexpected CSV schema: {item['path']}")
   count=0
   for row in reader:
    count+=1
    if row['STATION']!=item['station_id'] or row['ELEMENT']!='H':raise SystemExit(f"Station/element mismatch: {item['path']} row {count}")
  summaries.append({'station_id':item['station_id'],'rows':count,'sha256':item['sha256']})
 print(json.dumps({'status':'PASS','files':summaries},indent=2))
if __name__=='__main__':main()
