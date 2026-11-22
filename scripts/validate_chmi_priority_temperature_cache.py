#!/usr/bin/env python3
"""Verify immutable CHMI priority-temperature cache manifest and raw bytes."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 d=json.loads((ROOT/'data/chmi-priority-temperature/manifest.json').read_text())
 assert d['schema']=='loucka-chmi-priority-temperature-cache-v1'
 checked=0
 for x in d['files']:
  if x['status']!='cached':
   assert x['status']=='unavailable_http_404';continue
  p=ROOT/x['path'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==x['sha256'],x['path'];assert len(raw)==x['bytes'],x['path']
  j=json.loads(raw);vals=j['data']['data']['values'];assert all(r[0]==x['station_id'] for r in vals),x['path']
  assert sum(r[1] in ('T','TA') for r in vals)==x['temperature_rows'],x['path'];checked+=1
 print(json.dumps({'files_verified':checked,'periods':len(d['candidate_periods']),'unavailable':sum(x['status']!='cached' for x in d['files']),'manifest_sha256':hashlib.sha256((ROOT/'data/chmi-priority-temperature/manifest.json').read_bytes()).hexdigest()},indent=2))
if __name__=='__main__':main()
