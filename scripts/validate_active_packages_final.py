#!/usr/bin/env python3
"""Final deterministic contract audit of all active proposal packages and offline simulations."""
import argparse,csv,hashlib,json,subprocess,sys,tempfile
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--no-execute',action='store_true');ap.add_argument('--output',type=Path);a=ap.parse_args()
reg=json.loads((R/'config/active_proposal_registry.json').read_text());assert reg['database_mode']=='READ_ONLY' and reg['staging'] is False and reg['application_performed'] is False
active=[p for p in reg['packages'] if p['status']=='ACTIVE'];assert len(active)==10
keys=[]; inserts=[]; results=[]; per={}; executions=[]
for pkg in active:
 path=R/pkg['path'];ops=json.loads((path/'corrections.json').read_text());per[pkg['package_id']]=ops
 assert len(ops)==pkg['field_operations'],(pkg['package_id'],len(ops),pkg['field_operations'])
 assert pkg['classification'] in ('RESTORED','ESTIMATED')
 assert pkg['user_approval']=='NOT_APPROVED' and pkg['actual_weather_mcp_dry_run']=='NOT_RUN' and pkg['actual_application']=='NOT_APPLIED'
 man=json.loads((path/'manifest.json').read_text());assert man.get('database_writes',0)==0
 entries=man.get('files',man.get('artifacts',[]))
 if isinstance(entries,dict): entries=[{'path':v.get('path',k),'bytes':v['bytes'],'sha256':v['sha256']} for k,v in entries.items()]
 for f in entries:
  b=(path/f['path']).read_bytes();assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],(pkg['package_id'],f['path'])
 for o in ops:
  assert o['reason'].startswith(pkg['classification']+';'),(pkg['package_id'],o)
  assert 'not_approved' not in o['reason'].lower() or pkg['user_approval']=='NOT_APPROVED'
  k=(int(o['timestamp']),o['variable']);keys.append((pkg['package_id'],k,o['operation']))
  if o['operation']=='insert':inserts.append(k)
  assert o.get('source_database') and o.get('source_time') is not None and o.get('source_value') is not None,(pkg['package_id'],k)
  if pkg['classification']=='RESTORED':assert 'provenance' in o['reason'].lower()
  if pkg['classification']=='ESTIMATED':assert ('uncertainty' in o['reason'].lower() or 'quantile' in o['reason'].lower() or 'interval' in o['reason'].lower())
  assert o.get('expected_old_value') is None
  assert o.get('interval_minutes') in (None,5,6)
  assert o.get('us_units') in (None,16,17)
  if o['operation']=='insert': assert o.get('us_units')==16, (pkg['package_id'],k,'target archive us_units must be METRIC=16')
 declared={(int(o['timestamp']),o['variable'],o['operation'],o['new_value'],o.get('expected_old_value')) for o in pkg['operation_keys']}
 actual={(int(o['timestamp']),o['variable'],o['operation'],o['new_value'],o.get('expected_old_value')) for o in ops}
 assert actual==declared,(pkg['package_id'],'payload differs from registry')
 registry_by_key={(int(x['timestamp']),x['variable']):x for x in pkg['operation_keys']}
 for o in ops:
  k=(int(o['timestamp']),o['variable']);rk=registry_by_key[k]
  if o.get('us_units') is not None: assert rk.get('target_us_units')==o.get('us_units'),(pkg['package_id'],k,'target unit declaration mismatch')
  else: assert rk.get('target_us_units') in (16,17),(pkg['package_id'],k,'existing-row target unit system must be known')
  assert rk.get('source_unit_system') and ('target_us_units' in rk),(pkg['package_id'],k,'source/target unit systems must be explicit')
  expected_source_system='METRICWX usUnits=17' if o.get('source_database') in ('old_weewx','weewx_WH1080') else ('METRIC usUnits=16' if o.get('source_database') in ('pocasi-loucka.eu_old','pocasi-loucka.eu','pocasi-loucka.eu_GW1000','loucka_reconstruction') else None)
  assert expected_source_system and expected_source_system.split('usUnits=')[1] in rk['source_unit_system'],(pkg['package_id'],k,'source archive unit system mismatch')
  if o['operation']=='insert': assert o.get('us_units')==16 and rk['target_us_units']==16,(pkg['package_id'],k,'physical insert target must be usUnits=16 METRIC')
 # Each package's own manifest validates its reproducible evidence files.
 for cmd in ([pkg.get('local_validation',{}).get('command')] if isinstance(pkg.get('local_validation'),dict) else []):
  if cmd: assert (R/cmd.split()[1]).exists(),cmd
 if pkg['package_id'] in ('restored-source-only-2022-august-outtemp','restored-source-only-2023-may-outtemp'):
  md=json.loads((path/'candidate_metadata.json').read_text());assert len(md)==len(ops)
  by={int(x['timestamp']):x for x in md};assert set(by)=={int(x['timestamp']) for x in ops}
  for ts,x in by.items():
   ev=x['source_evidence'];assert ev['archive']=='pocasi-loucka.eu_old' and ev.get('source_interval_minutes')==5
   assert (ev.get('source_unit',ev.get('source_usUnits')))==16
   assert ev['target_row_exists_in_reconstruction'] is False
   assert all(v is False for db,v in ev['archive_row_presence_by_database'].items() if db!='pocasi-loucka.eu_old')
   assert ev['archive_row_presence_by_database']['pocasi-loucka.eu_old'] is True
   if '2023' in pkg['package_id']: assert ev['archive_row_presence_by_database']=={'loucka_reconstruction':False,'pocasi-loucka.eu':False,'pocasi-loucka.eu_GW1000':False,'pocasi-loucka.eu_old':True,'old_weewx':False,'weewx_WH1080':False}
   assert ev.get('reconstruction_change_events',ev.get('target_change_events_all_variables'))==0
   assert ev['source_values']['outTemp'] is not None
   assert x['classification']=='RESTORED' and x.get('confidence')=='MODERATE' and x.get('uncertainty')
   checks=ev['quality_checks']
   required={'five_minute_grid','outTemp_nonnull','outTemp_zero','physical_temperature_range_c','source_row_dynamic'} if '2022' in pkg['package_id'] else {'five_minute_grid','source_interval_is_5','source_units_metric_16','outTemp_nonnull','outTemp_is_zero','source_archive_row_present','target_absent_in_other_five_archives','change_event_count','exact_luhamet_pair','physical_temperature_range_C'}
   assert required<=set(checks),(pkg['package_id'],ts,required-set(checks))
   if '2023' in pkg['package_id']:assert ev['exact_luhamet']['temperature_c'] is not None and ev['row_completeness'].startswith('new archive row')
  results.append({'package_id':pkg['package_id'],'rows':len(md),'per_row_source_target_unit_history_plausibility':'PASS'})
 results.append({'package_id':pkg['package_id'],'operation_count':len(ops),'manifest':'PASS','provenance_reasons':'PASS'})
 if not a.no_execute:
  validate=path/'validate.py';assert validate.exists()
  cmd=[sys.executable,str(validate.relative_to(R))]
  p=subprocess.run(cmd,cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180);executions.append({'package_id':pkg['package_id'],'command':'python3 '+str(validate.relative_to(R)),'returncode':p.returncode,'output':p.stdout.strip()[-700:]});assert p.returncode==0,(pkg['package_id'],p.stdout)
  for sim in ('simulate.py','simulate_v2_1.py'):
   if (path/sim).exists():
    cmd=[sys.executable,str((path/sim).relative_to(R))]
    if sim=='simulate_v2_1.py':cmd+=['--output','/tmp/p3_final_simulation.json']
    p=subprocess.run(cmd,cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180);executions.append({'package_id':pkg['package_id'],'command':'python3 '+' '.join(cmd),'returncode':p.returncode,'output':p.stdout.strip()[-500:]});assert p.returncode==0,(pkg['package_id'],p.stdout)
from datetime import datetime,timezone
protected=lambda ts: (datetime.fromtimestamp(ts,timezone.utc).year==2021 or (datetime.fromtimestamp(ts,timezone.utc).year==2018 and datetime.fromtimestamp(ts,timezone.utc).month<=3))
for test_ts in (1514764800,1517443200,1519862400):assert protected(test_ts)
assert not protected(1522540800)
all_keys=[k for _,k,_ in keys];assert len(all_keys)==324 and len(set(all_keys))==324
assert len(inserts)==311 and len(set(inserts))==311
assert (reg['active_operation_count'],reg['active_restored_operations'],reg['active_estimated_operations'],reg['active_unique_timestamps'],reg['active_physical_new_database_rows_if_applied'],reg['active_update_operations'])==(324,303,21,315,311,13)
assert all(not(__import__('datetime').datetime.fromtimestamp(k[0],__import__('datetime').timezone.utc).year==2018 and __import__('datetime').datetime.fromtimestamp(k[0],__import__('datetime').timezone.utc).month<=3) for k in all_keys)
assert not any(__import__('datetime').datetime.fromtimestamp(k[0],__import__('datetime').timezone.utc).year==2021 for k in all_keys)
sets={p['package_id']:{int(o['timestamp']) for o in per[p['package_id']]} for p in active}
assert not (sets['restored-source-only-2020-isolated-outtemp'] & sets['restored-source-only-2020-march-outtemp-v2'])
assert not (sets['p3-temperature-v2.1'] & sets['restored-source-only-2020-isolated-outtemp'])
assert not (sets['p3-temperature-v2.1'] & sets['restored-source-only-2020-march-outtemp-v2'])
# Explicit dependency ordering for new-row then field-fill 2013 sequence.
p13=per['restored-source-only-2013-july-pilot'];seen=set()
for o in p13:
 key=(int(o['timestamp']),o['variable'])
 if o['operation']=='update' and int(o['timestamp']) in (1373319000,1373319600,1373320200):assert (int(o['timestamp']),'outTemp') in seen
 seen.add(key)
batch_check=subprocess.run([sys.executable,'scripts/validate_batch_payload_equality.py'],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);assert batch_check.returncode==0,batch_check.stdout
summary={'status':'PASS','batch_payload_equality':'PASS','target_insert_us_units':'all METRIC=16','packages':len(active),'operations':len(all_keys),'RESTORED':303,'ESTIMATED':21,'unique_timestamp_variable_keys':len(set(all_keys)),'unique_physical_inserts':len(set(inserts)),'unique_timestamps':315,'updates':13,'q1_2018_operations':0,'year_2021_operations':0,'2020_package_overlap_timestamps':0,'p3_2020_overlap_timestamps':0,'dependency_order_2013':'PASS','per_package':results,'executions':executions,'database_access':'NONE','MCP_dry_run':'NOT_RUN','staging':False,'application':'NOT_APPLIED'}
if a.output:a.output.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
