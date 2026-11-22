#!/usr/bin/env python3
"""Validate final Loucka audit ZIP content, clean extraction, active package validators and offline sims."""
import argparse, hashlib, json, subprocess, sys, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_REPORTS=[
 'MASTER_AUDIT_REPORT.md','DATABASE_INVENTORY.md','TIME_CONTINUITY_AUDIT.md','TEMPERATURE_AUDIT.md','HUMIDITY_AUDIT.md','PRECIPITATION_AUDIT.md','SECONDARY_SENSORS_AUDIT.md','REFERENCE_DATA_INVENTORY.md','MODEL_VALIDATION_REPORT.md','RECONSTRUCTION_HISTORY_AUDIT.md','DERIVED_VARIABLES_REPORT.md','DATA_QUALITY_CLASSIFICATION.md','CONSOLIDATED_CORRECTIONS_REPORT.md','LOCAL_SIMULATION_REPORT.md','FINAL_ARCHIVE_READINESS.md','PROTECTED_YEAR_2021_DIAGNOSTICS.md','ACTIVE_2018_RECONSTRUCTION_STATUS.md','NEXT_STEPS.md']
COMMANDS=[
 ['scripts/validate_active_packages_final.py'],
 ['scripts/validate_active_proposal_deduplication.py'],
 ['scripts/validate_batch_payload_equality.py'],
 ['scripts/validate_source_first_active_proposals.py'],
 ['scripts/validate_active_proposal_quality_provenance.py'],
 ['scripts/validate_final_readiness_matrix.py'],
 ['scripts/validate_o4_readiness_matrix.py'],
 ['scripts/validate_expert_review_register.py'],
 ['scripts/validate_source_only_2010_nearest_slot_review.py'],
 ['scripts/validate_source_only_2012_nearest_slot_review.py'],
 ['scripts/validate_source_only_2013_nearest_slot_review.py'],
 ['scripts/validate_historical_wind_2020_anomaly_review.py'],
 ['scripts/validate_gw1000_gw3000_rainrate_mismatch_patterns.py'],
 ['scripts/validate_b5_2019_short_gap_source_disposition.py'],
 ['proposals/restored_source_only_2022_august_outtemp/validate.py'],
 ['proposals/restored_source_only_2023_may_outtemp/validate.py']]

def run(cwd, cmd):
 r=subprocess.run([sys.executable,*cmd],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 return {'command':'python3 '+' '.join(cmd),'returncode':r.returncode,'output':r.stdout[-4000:]}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--output',type=Path);a=ap.parse_args()
 with zipfile.ZipFile(a.archive) as z:
  names=set(z.namelist()); assert len(names)==len(z.namelist()),'duplicate zip members'
  assert 'FINAL_BUNDLE_MANIFEST.json' in names
  man=json.loads(z.read('FINAL_BUNDLE_MANIFEST.json')); entries=man['files']
  assert len(entries)+1==len(names), f'manifest count {len(entries)} vs {len(names)}'
  for x in entries:
   b=z.read(x['path']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],x['path']
  assert not any(n.lower().endswith('.zip') for n in names),'nested archives must be excluded'
  for f in REQUIRED_REPORTS: assert 'reports/'+f in names,f
  inv=json.loads(z.read('reports/required-report-inventory.json'));assert inv['required_report_count']==18
  progress=json.loads(z.read('PROGRESS.json')); assert progress['overall']['verified_subtasks']==141 and progress['overall']['defined_subtasks']==142
  assert progress['overall']['status']=='COMPLETED_WITH_LIMITATIONS'
  assert progress['overall']['blocked_stages']==1 and progress['overall']['in_progress_stages']==0
  reg=json.loads(z.read('config/active_proposal_registry.json'))
  assert (reg['active_operation_count'],reg['active_restored_operations'],reg['active_estimated_operations'],reg['active_unique_timestamps'],reg['active_physical_new_database_rows_if_applied'],reg['active_update_operations'])==(324,303,21,315,311,13)
  assert reg['application_performed'] is False and reg['staging'] is False
  assert all(not (datetime.fromtimestamp(int(o['timestamp']),timezone.utc).year==2018 and datetime.fromtimestamp(int(o['timestamp']),timezone.utc).month<=3) and datetime.fromtimestamp(int(o['timestamp']),timezone.utc).year!=2021 for pkg in reg['packages'] if pkg['status']=='ACTIVE' for o in pkg['operation_keys'])
  protected=lambda ts: (datetime.fromtimestamp(ts,timezone.utc).year==2021 or (datetime.fromtimestamp(ts,timezone.utc).year==2018 and datetime.fromtimestamp(ts,timezone.utc).month<=3))
  for test_ts in (1514764800,1517443200,1519862400): assert protected(test_ts)
  assert not protected(1522540800)
  assert all(x['user_approval']=='NOT_APPROVED' and x['actual_weather_mcp_dry_run']=='NOT_RUN' and x['actual_application']=='NOT_APPLIED' for x in reg['packages'] if x['status']=='ACTIVE')
  assert 'reports/E4_RAIN_SEMANTICS_BLOCKER_FINAL.md' in names
  assert 'FUTURE_RECONSTRUCTION_PLAN.md' in names and 'PRE_APPLICATION_CHECKLIST.md' in names
  with tempfile.TemporaryDirectory(prefix='loucka-final-clean-') as td:
   z.extractall(td)
   results=[]
   for c in COMMANDS:
    x=run(td,c);results.append(x)
    if x['returncode']!=0: raise SystemExit(json.dumps(x,indent=2,ensure_ascii=False))
   # Package-wide deterministic validator executes all active package validators and offline simulators.
   safety={'database_access':'NONE','MCP_dry_run':'NOT_RUN','staging':False,'application':False}
  out={'status':'PASS','archive':a.archive.name,'verified_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'members':len(names),'sha256_entries_checked':len(entries),'clean_extract':True,'required_main_reports':18,'operations':324,'RESTORED':303,'ESTIMATED':21,'unique_timestamps':315,'physical_inserts':311,'updates':13,'validation_commands':results,'safety':safety}
  if a.output:a.output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
  print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
