#!/usr/bin/env python3
"""Generate schema-shaped, proposal-only provenance sidecars for the active registry."""
import json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]; reg=json.loads((R/'config/active_proposal_registry.json').read_text())
base_units={'outTemp':'°C','outHumidity':'% RH','rain':'mm per archive interval (historical interval semantics review required)','rainRate':'mm/h (historical interval semantics review required)','windSpeed':'m/s','windGust':'m/s','windDir':'degree','barometer':'hPa'}
def field_unit(field,code):
 if field in ('windSpeed','windGust'): return 'm/s' if code==17 else ('km/h' if code==16 else 'unknown wind-speed unit')
 return base_units.get(field,'unit not mapped')
def find_target_code(obj,ts):
 if isinstance(obj,dict):
  if int(obj.get('timestamp',obj.get('dateTime',-1)) or -1)==ts:
   for k in ('us_units','usUnits','target_usUnits','target_units'):
    if isinstance(obj.get(k),int):return obj[k]
  for v in obj.values():
   found=find_target_code(v,ts)
   if found is not None:return found
 elif isinstance(obj,list):
  for v in obj:
   found=find_target_code(v,ts)
   if found is not None:return found
 return None
records=[]; package_stats=[]
for pkg in reg['packages']:
 if pkg['status']!='ACTIVE':continue
 root=R/pkg['path']; ops=json.loads((root/'corrections.json').read_text()); n=len(ops)
 registry_ops={(int(x['timestamp']),x['variable']):x for x in pkg['operation_keys']}
 target_codes={}
 for fn in ('target_snapshot.json','local_target_state.json','target_state.json','candidate_metadata.json','source_snapshot.json'):
  q=root/fn
  if q.exists():
   try:payload=json.loads(q.read_text())
   except Exception:continue
   for o in ops:
    tt=int(o['timestamp']);found=find_target_code(payload,tt)
    if found is not None:target_codes[tt]=found
 meta_path=root/'candidate_metadata.json'; meta=json.loads(meta_path.read_text()) if meta_path.exists() else None
 bytime={}
 if isinstance(meta,list):
  for x in meta:
   if isinstance(x,dict) and 'timestamp' in x:bytime[int(x['timestamp'])]=x
 elif isinstance(meta,dict):
  for x in meta.get('records',meta.get('candidates',[])):
   if isinstance(x,dict) and 'timestamp' in x:bytime[int(x['timestamp'])]=x
 for i,op in enumerate(ops):
  ts=int(op['timestamp']);var=op['variable'];cl=pkg['classification'];reason=op.get('reason','')
  assert reason.startswith(cl+';'),(pkg['package_id'],ts,var,reason[:50])
  srcdb=op.get('source_database');srcts=op.get('source_time');srcv=op.get('source_value')
  source_code=17 if srcdb in ('old_weewx','weewx_WH1080') else (16 if srcdb in ('pocasi-loucka.eu_old','pocasi-loucka.eu','pocasi-loucka.eu_GW1000','loucka_reconstruction') else None)
  srcunit=field_unit(var,source_code)
  code=registry_ops.get((ts,var),{}).get('target_us_units') or op.get('us_units') or target_codes.get(ts) or 16;u=field_unit(var,code);m=bytime.get(ts,{})
  if cl=='ESTIMATED':
   unc={'type':'unknown','value':None,'lower':None,'upper':None,'unit':u}
   method={'id':'linear_interpolation','version':pkg['version'],'parameters_ref':f"{pkg['path']}/candidate_metadata.json#{ts}"}
   hold='2019–2020 conditional masked-block holdout by gap-duration cohort; not an individual prediction interval.'
  else:
   unc={'type':'unknown','value':None,'lower':None,'upper':None,'unit':u}
   method={'id':'restore_exact_source_archival_measurement','version':pkg['version'],'parameters_ref':f"{pkg['path']}/candidate_metadata.json#{ts}" if meta_path.exists() else f"{pkg['path']}/corrections.json#{ts}"}
   hold=None
  deps=[]
  if pkg['package_id']=='restored-source-only-2013-july-pilot' and var=='outHumidity':deps=[f"{ts}:outTemp"]
  batch_n=(i//50)+1
  lineage=(pkg.get('independent_review') or 'No separate independent review recorded.')+' Archive-copy agreement is not treated as independent sensor truth.'
  if pkg['package_id']=='p3-temperature-v2.1':lineage+=' No exact target/source archive value; measured endpoints and context drive interpolation.'
  target={'operation':op['operation'],'old_value':op.get('expected_old_value'),'interval_minutes':op.get('interval_minutes'),'us_units':code}
  record={'schema_version':'1.0','variable':var,'timestamp_utc_epoch':ts,'original_value':op.get('expected_old_value'),'new_value':op.get('new_value'),'unit':u,
   'origin_class':cl,'review_status':'REVIEW_REQUIRED','source':{'database':srcdb,'timestamp_utc_epoch':srcts,'value':srcv,'unit':srcunit,'lineage_note':lineage+f' Source archive unit code inferred from audited archive metadata: {source_code}; target code {code}.'},
   'method':method,'validation':{'group_id':pkg['package_id'],'metrics_ref':f"{pkg['path']}/candidate_metadata.json" if meta_path.exists() else f"{pkg['path']}/corrections.json",'holdout_scope':hold},
   'uncertainty':{**unc,'unit':u},'dependencies':deps,'expected_target_state':target,
   'reason':reason+' Proposal status: NOT_APPROVED; no actual MCP dry-run; NOT_APPLIED.',
   'batch_id':f"{pkg['package_id']}:batch-{batch_n:02d}",'dependencies_ref':f"{pkg['path']}/dependency_metadata.json" if (root/'dependency_metadata.json').exists() else None}
  records.append(record)
 package_stats.append({'package_id':pkg['package_id'],'classification':cl,'operations':n,'targets_with_per_row_metadata':sum(int(o['timestamp']) in bytime for o in ops),'metadata_rows':len(bytime),'review_status':'REVIEW_REQUIRED_PENDING_SEPARATE_APPROVAL'})
out={'schema':'loucka-active-proposal-quality-provenance-v1','created_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'quality_schema':'config/quality-provenance-record.schema.json','records_count':len(records),'classification_counts':{x:sum(q['origin_class']==x for q in records) for x in ('RESTORED','ESTIMATED')},'proposal_state':'all records are proposal metadata only; NOT_APPROVED, NOT_RUN, NOT_APPLIED','individual_uncertainty':'unknown unless a calibrated per-value interval exists; P3 grouped conditional holdout summaries are not individual prediction intervals','packages':package_stats,'records':records}
(R/'data/active_proposal_quality_provenance.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'records':len(records),'classes':out['classification_counts'],'packages':len(package_stats),'metadata_rows_by_package':package_stats},ensure_ascii=False,indent=2))
