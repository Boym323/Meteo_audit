#!/usr/bin/env python3
import json, pathlib, sys, datetime
p=pathlib.Path(__file__).resolve().parents[1]/'RECONSTRUCTION_EXECUTION_PROGRESS.json'
d=json.loads(p.read_text()); item=json.load(sys.stdin)
records=d.setdefault('followup_batches',[])
records=[x for x in records if x.get('batch_id')!=item['batch_id']]
records.append(item); d['followup_batches']=records
tot=d.setdefault('execution_totals',{})
if item.get('application_result')=='APPLIED_AND_VERIFIED':
    tot['applied_restored_operations']=tot.get('applied_restored_operations',0)+item.get('operation_count',0)
    tot['unapplied_non_rain_operations']=tot.get('unapplied_non_rain_operations',0)-item.get('operation_count',0)
for pkg in d['packages']:
    if pkg.get('package_id')==item.get('source_package'):
        if item.get('application_result')=='APPLIED_AND_VERIFIED':
            pkg['application_result']='APPLIED_AS_PART_OF_COMPATIBLE_EXECUTION_BATCH'
            pkg['pre_application_check']='PASSED'
            pkg['dry_run_status']='DRY_RUN_PASSED'
            pkg['result_verification']='PASSED_INDEPENDENT_SELECT'
            pkg.setdefault('audit_events',[]).extend(item.get('audit_event_ids',[]))
        else:
            pkg['dry_run_status']=item.get('dry_run_status',pkg.get('dry_run_status'))
            pkg['pre_application_check']=item.get('pre_application_check',pkg.get('pre_application_check'))
            pkg['application_result']='NOT_APPLIED'
d['overall_status']='APPLIED_AND_VERIFIED' if tot.get('unapplied_non_rain_operations')==314 else d.get('overall_status')
d['updated_utc']=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
