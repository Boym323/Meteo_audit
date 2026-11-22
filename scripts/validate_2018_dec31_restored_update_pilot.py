#!/usr/bin/env python3
"""Validate the 2018-12-31 pilot and active proposal registry uniqueness; no DB access."""
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'proposals/restored_source_only_2018_dec31_primary'
subprocess.run([sys.executable,str(P/'validate.py')],check=True)
cor=json.loads((P/'corrections.json').read_text())
keys={(x['timestamp'],x['variable']) for x in cor}
duplicates=[]
def walk(v,path):
 if isinstance(v,dict):
  if {'timestamp','variable','new_value','operation'}<=v.keys():
   k=(v['timestamp'],v['variable'])
   if k in keys:duplicates.append((path,k))
  for x in v.values():walk(x,path)
 elif isinstance(v,list):
  for x in v:walk(x,path)
for f in (R/'proposals').rglob('*.json'):
 if P in f.parents:continue
 try:walk(json.loads(f.read_text()),f.relative_to(R).as_posix())
 except (json.JSONDecodeError,UnicodeDecodeError):continue
assert not duplicates,duplicates
assert len(keys)==7 and len(cor)==7
print('PASS: active proposal registry has no duplicate timestamp-variable operation for the seven pilot updates.')
