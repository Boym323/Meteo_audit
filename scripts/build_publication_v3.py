#!/usr/bin/env python3
"""Export V3 publication policy decisions from current matrix and evidence registry."""
import csv,json,hashlib,sys
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from meteo_audit.time_bounds import local_period_bounds,PRAGUE

def main():
 src=ROOT/'data/PUBLICATION_READINESS_DECISIONS.csv';raw=list(csv.DictReader(src.open(encoding='utf-8')))
 registry=json.loads((ROOT/'MONTHLY_VALIDATION_EVIDENCE.json').read_text());ev={(x['period'],x['variable']):x for x in registry['records']}
 output=[]
 for r in raw:
  start,end=local_period_bounds(r['period']);e=ev.get((r['period'],r['variable']))
  row=dict(r);row.update({'statistic_id':f"{r['period']}:{r['scope']}:{r['variable']}:{r['statistic']}",'period_start':datetime.fromtimestamp(start,PRAGUE).isoformat(),'period_end':datetime.fromtimestamp(end,PRAGUE).isoformat(),'timezone':'Europe/Prague','publication_authorized':False,'individual_evidence_record':e,'methodology_version':'statistical-publication-policy-v3.0','source_matrix':'data/PUBLICATION_READINESS_DECISIONS.csv'})
  output.append(row)
 counts={}
 for r in output:counts[r['publication_readiness']]=counts.get(r['publication_readiness'],0)+1
 # Source snapshot date makes this export reproducible for identical inputs.
 snapshot=json.loads((ROOT/'data/STATISTICAL_READINESS_CURRENT.json').read_text()).get('snapshot',{})
 generated=snapshot.get('snapshot_utc') or snapshot.get('snapshot_id') or 'unknown-source-snapshot'
 doc={'schema':'loucka-publication-decisions-v3','generated_utc':generated,'source_matrix_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'evidence_registry_sha256':hashlib.sha256((ROOT/'MONTHLY_VALIDATION_EVIDENCE.json').read_bytes()).hexdigest(),'row_count':len(output),'status_counts':counts,'ready_for_publication_rows':counts.get('READY_FOR_PUBLICATION',0),'ready_with_disclosed_limitations_rows':counts.get('READY_WITH_DISCLOSED_LIMITATIONS',0),'publication_authorized':False,'decisions':output}
 (ROOT/'STATISTICAL_PUBLICATION_DECISIONS_V3.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
 fields=list(output[0]);
 with (ROOT/'STATISTICAL_PUBLICATION_DECISIONS_V3.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for row in output:w.writerow({k:(json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else v) for k,v in row.items()})
 print(json.dumps({'rows':len(output),'counts':counts,'publication_authorized':False},indent=2))
if __name__=='__main__':main()
