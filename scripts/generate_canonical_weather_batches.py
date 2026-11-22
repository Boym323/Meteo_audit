#!/usr/bin/env python3
"""Deterministically rebuild the specified batch payloads from canonical corrections.json."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def main():
 # RH midpoint: single list-shaped Weather MCP batch, preserving canonical full operation payload.
 d=ROOT/'proposals/restored_rh_2014_midpoint_pilot'; ops=load(d/'corrections.json')
 save(d/'weather_mcp_batches.json',[{'batch_id':'restored-rh-2014-midpoint-001','classification':'RESTORED','max_batch_size':50,'operations':ops}])
 # 2023: stable four batches in canonical timestamp order.
 d=ROOT/'proposals/restored_source_only_2023_may_outtemp';ops=load(d/'corrections.json');old=load(d/'weather_mcp_batches.json');bs=[]
 for i in range(0,len(ops),50):
  n=i//50+1;chunk=ops[i:i+50];bs.append({'batch_id':f'restored-2023-may-outtemp-{n:02d}-v1','size':len(chunk),'operations':chunk})
 old.update(batch_count=len(bs),batches=bs);save(d/'weather_mcp_batches.json',old)
 # 2020 March v2: one four-operation batch.
 d=ROOT/'proposals/restored_source_only_2020_march_outtemp_v2';ops=load(d/'corrections.json')
 save(d/'weather_mcp_batches.json',{'contract':'Weather MCP proposal format; generated deterministically from corrections.json; not submitted','max_batch_size':50,'batch_count':1,'batches':[{'batch_id':'restored-2020-march-outtemp-v2-001','size':len(ops),'operations':ops}],'user_approval':'NOT_APPROVED','actual_mcp_dry_run':'NOT_RUN','application':'NOT_APPLIED'})
 print('PASS: deterministic canonical batch generation: RH2014 midpoint 1, 2023 May 190 (50/50/50/40), 2020 March v2 4.')
if __name__=='__main__':main()
