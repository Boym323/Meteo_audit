#!/usr/bin/env python3
"""Map each selected monthly temperature mean to cached exact-month references."""
import csv,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 candidates=json.loads((ROOT/'MONTHLY_PUBLICATION_CANDIDATES.json').read_text())['candidates'];temps=[x for x in candidates if x['variable']=='outTemp'];rows=[]
 for c in temps:
  period=c['period'];matches=[]
  for path in sorted((ROOT/'data/chmi-2018/raw').glob(f'*{period.replace("-","")}*.json')):
   matches.append({'provider':'CHMI','station_id':path.name.split('-')[3]+'-'+path.name.split('-')[4]+'-'+path.name.split('-')[5] if False else path.name.split('-')[1]+'-'+path.name.split('-')[2]+'-'+path.name.split('-')[3]+'-'+path.name.split('-')[4],'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cadence':'10-minute','month':period})
  for path in sorted((ROOT/'data/chmi-rh-winter-validation/raw').glob(f'*T-{period.replace("-","")}.csv')):
   matches.append({'provider':'CHMI','station_id':path.name.split('-')[3]+'-'+path.name.split('-')[4]+'-'+path.name.split('-')[5] if False else '-'.join(path.name.split('-')[1:5]),'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cadence':'10-minute','month':period})
  for path in sorted((ROOT/'data/chmi-2026-recent/raw').glob(f'*{period.replace("-","")}*.json')):
   parts=path.stem.split('-');station_id='-'.join(parts[1:5])
   matches.append({'provider':'CHMI','station_id':station_id,'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cadence':'10-minute','month':period})
  for path in sorted((ROOT/'data/chmi-priority-temperature/raw').glob(f'*{period.replace("-","")}*.json')):
   parts=path.stem.split('-');station_id='-'.join(parts[1:5])
   if not any(x.get('path')==path.relative_to(ROOT).as_posix() for x in matches):
    matches.append({'provider':'CHMI','station_id':station_id,'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cadence':'10-minute','month':period})
  if period=='2026-01':
   path=ROOT/'data/publication-pilot-reference/chmi_11777_2026-01_10min.json'
   if path.exists() and not any(x['sha256']==hashlib.sha256(path.read_bytes()).hexdigest() for x in matches):matches.append({'provider':'CHMI','station_id':'0-203-0-11777','path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cadence':'10-minute','month':period})
  for path in sorted((ROOT/'data/chmi-2013-context/raw').glob('*')):
   if period.startswith('2013-') and path.name.endswith(('TMA.csv','TMI.csv')):matches.append({'provider':'CHMI','path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cadence':'daily extrema; not directly pairable to monthly mean','month':period})
  # Retain one canonical file per station/cadence. The expanded historical cache
  # is preferred when it covers a month; do not count the same station twice
  # just because older pilot caches also contain that source month.
  selected=[]; seen=set()
  matches.sort(key=lambda x:(0 if 'chmi-priority-temperature/' in x.get('path','') else 1, x.get('path','')))
  for ref in matches:
   key=(ref.get('station_id'),ref.get('cadence'))
   if ref.get('station_id') and ref.get('cadence')=='10-minute':
    if key in seen: continue
    seen.add(key)
   selected.append(ref)
  rows.append({**c,'reference_status':'SAME_MONTH_SUBDAILY_AVAILABLE' if any('10-minute'==x['cadence'] for x in selected) else ('DAILY_CONTEXT_ONLY' if selected else 'NO_LOCAL_SAME_MONTH_REFERENCE'),'references':selected,'decision_note':'Regional comparator only; require exact UTC cadence pairing, station QC filtering, and site/elevation limitations before using as validation.'})
 doc={'schema':'loucka-temperature-reference-availability-v1','candidate_count':len(rows),'candidates':rows,'source_catalog':'REFERENCE_STATION_CATALOG.json','summary':{s:sum(x['reference_status']==s for x in rows) for s in sorted({x['reference_status'] for x in rows})}}
 (ROOT/'TEMPERATURE_REFERENCE_AVAILABILITY.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n');print(json.dumps(doc['summary'],indent=2))
if __name__=='__main__':main()
