#!/usr/bin/env python3
"""Combine authoritative station inventory with locally cached reference evidence."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 inv=ROOT/'data/reference-inventory/reference_stations_snapshot_20261113.json';cache=ROOT/'data/reference-inventory/reference_source_catalog.json'
 if not cache.exists():
  import subprocess,sys;subprocess.run([sys.executable,str(ROOT/'scripts/build_reference_data_catalog.py')],check=True)
 stations=json.loads(inv.read_text())['stations']; datasets=json.loads(cache.read_text())['datasets'];items=[]
 for s in stations:
  items.append({'station_id':s['station_id'],'provider':s['provider'],'name':s['station_name'],'location_description':s.get('location_description'),'latitude':s.get('latitude_n'),'longitude':s.get('longitude_e'),'coordinates_status':s.get('coordinates_status'),'elevation_m':s.get('elevation_m'),'timezone':s.get('timezone_name'),'first_observed_utc':s.get('first_observed_utc'),'last_observed_utc':s.get('last_observed_utc'),'available_variables':s.get('primary_available_variables',[]),'access_status':s.get('access_status'),'inventory_source':'data/reference-inventory/reference_stations_snapshot_20261113.json','limitation':'Coordinates are null when not recorded; no village centroid substitution.'})
 for sid,name,lat,lon,elev in [('0-203-0-11777','ČHMÚ Vizovice',49.22297,17.84361,313.0),('0-203-0-11778','ČHMÚ Luhačovice',49.099,17.757,None)]:
  files=[f for d in datasets for f in d['files'] if f.get('station_id')==sid]
  items.append({'station_id':sid,'provider':'ČHMÚ','name':name,'latitude':lat,'longitude':lon,'elevation_m':elev,'timezone':'UTC','cached_files':len(files),'cached_variables':sorted({f.get('element') for f in files if f.get('element')}),'cached_months':sorted({str(f.get('month')) for f in files if f.get('month')}),'cache_paths':sorted({f['path'] for f in files}),'datasets':[d['dataset_id'] for d in datasets if any(f.get('station_id')==sid for f in d['files'])],'limitation':'Reference station is regional comparison evidence, not Loučka sensor identity or equality.'})
 pressure_manifest=ROOT/'data/chmi-2026-synop-pressure/manifest.json'
 if pressure_manifest.exists():
  for station in {json.dumps(f['station'],sort_keys=True):f['station'] for f in json.loads(pressure_manifest.read_text())['files']}.values():
   files=[f for d in datasets for f in d['files'] if f.get('station_id')==station['station_id']]
   items.append({'station_id':station['station_id'],'provider':'ČHMÚ','name':station['name'],'latitude':station['latitude'],'longitude':station['longitude'],'elevation_m':station['elevation_m'],'timezone':'UTC','cached_files':len(files),'cached_variables':sorted({f.get('element') for f in files if f.get('element')}),'cached_months':sorted({str(f.get('month')) for f in files if f.get('month')}),'cache_paths':sorted({f['path'] for f in files}),'datasets':[d['dataset_id'] for d in datasets if any(f.get('station_id')==station['station_id'] for f in d['files'])],'metadata_source':station['metadata_source'],'metadata_source_sha256':station['metadata_source_sha256'],'limitation':'Hourly SYNOP P_hm used only for regional pressure plausibility; no Loučka field or sensor equivalence implied.'})
 out={'schema':'loucka-reference-station-catalog-v1','inventory_snapshot_utc':json.loads(inv.read_text())['snapshot_utc'],'inventory_sha256':hashlib.sha256(inv.read_bytes()).hexdigest(),'cache_catalog_sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),'stations':items}
 (ROOT/'REFERENCE_STATION_CATALOG.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'stations':len(items),'inventory_stations':len(stations),'chmi_stations':sum(x['provider']=='ČHMÚ' for x in items)},indent=2))
if __name__=='__main__':main()
