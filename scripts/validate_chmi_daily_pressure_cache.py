#!/usr/bin/env python3
"""Validate frozen daily pressure CSVs against manifest hashes and station schema."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 m=json.loads((ROOT/'data/chmi-daily-pressure/manifest.json').read_text())
 if len(m.get('files',[]))!=3:raise SystemExit('Expected three immutable CHMI daily-pressure cache files')
 result=[]
 for item in m['files']:
  p=ROOT/item['path'];raw=p.read_bytes()
  if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:raise SystemExit(f"Cache integrity mismatch: {item['path']}")
  with p.open(encoding='utf-8-sig',newline='') as stream:
   reader=csv.DictReader(stream); required={'STATION','ELEMENT','TIMEFUNC','DT','VALUE','FLAG','QUALITY'}
   if not required.issubset(set(reader.fieldnames or [])):raise SystemExit(f"CSV schema mismatch: {item['path']}")
   count=0
   for row in reader:
    count+=1
    if row['STATION']!=item['station_id'] or row['ELEMENT']!='P':raise SystemExit(f"Station/element mismatch: {item['path']} row {count}")
  result.append({'station_id':item['station_id'],'row_count':count,'sha256':item['sha256']})
 print(json.dumps({'status':'PASS','files':result},indent=2))
if __name__=='__main__':main()
