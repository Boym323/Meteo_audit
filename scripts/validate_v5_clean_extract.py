#!/usr/bin/env python3
"""Clean-extract v5, verify manifest and run active package validators/simulators."""
import hashlib,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ARCHIVE=ROOT/'loucka_historical_audit_and_priority_corrections_v5.zip'
with zipfile.ZipFile(ARCHIVE) as z:
 names=set(z.namelist());m=json.loads(z.read('MANIFEST.json'));assert m['main_report_count']==18
 assert len(m['contents'])==m['file_count_excluding_manifest']
 assert m['active_correction_operation_count']==63 and m['active_restored_operations']==42 and m['active_estimated_operations']==21
 assert m['active_unique_timestamps']==54 and m['active_physical_rows_if_applied']==52 and m['active_update_operations']==11
 inventory=json.loads(z.read('reports/required-report-inventory.json'));assert inventory['required_report_count']==18
 assert all('reports/'+x['report'] in names for x in inventory['reports'])
 for item in m['contents']:
  b=z.read(item['path']);assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],item['path']
 reg=json.loads(z.read('config/active_proposal_registry.json'))
 assert reg['packages'][0]['local_validation']['command']=='python3 proposals/estimated_short_temperature_gaps_v2/validate.py'
 assert next(x for x in reg['packages'] if x['package_id']=='restored-source-only-2013-july-pilot')['local_validation']['command']=='python3 proposals/restored_source_only_2013_july_pilot/validate.py'
 assert 'loucka_historical_audit_and_priority_corrections_v3.zip' not in names
 assert 'proposals/estimated_short_temperature_gaps_v2/simulate_v2_1.py' in names
 assert 'proposals/restored_source_only_2020_isolated_outtemp/per_target_archive_presence.csv' in names
with tempfile.TemporaryDirectory(prefix='loucka-v5-clean-') as td:
 with zipfile.ZipFile(ARCHIVE) as z:z.extractall(td)
 base=Path(td)
 commands=[
  ['scripts/validate_active_proposal_deduplication.py'],['scripts/validate_source_first_active_proposals.py'],
  ['proposals/estimated_short_temperature_gaps_v2/simulate_v2_1.py','--output','proposals/estimated_short_temperature_gaps_v2/offline_simulation_v2_1.json'],
  ['proposals/estimated_short_temperature_gaps_v2/validate.py'],['proposals/restored_source_only_2013_july_pilot/validate.py'],
  ['scripts/validate_2018_dec31_restored_update_pilot.py'],['proposals/restored_source_only_2019_may30_outtemp/validate.py'],
  ['proposals/restored_source_only_2020_isolated_outtemp/validate.py'],['proposals/restored_source_only_rows_v2/validate.py'],
  ['scripts/validate_final_report_bundle.py'],['proposals/restored_source_only_2013_july_pilot/simulate.py'],
  ['proposals/restored_source_only_2019_may30_outtemp/simulate.py'],['proposals/restored_source_only_2020_isolated_outtemp/simulate.py']]
 results=[]
 for cmd in commands:
  proc=subprocess.run([sys.executable,*cmd],cwd=base,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  results.append({'command':'python3 '+' '.join(cmd),'returncode':proc.returncode,'output':proc.stdout[-1800:]})
  if proc.returncode:print(json.dumps({'status':'FAIL','failed':results[-1]},indent=2));raise SystemExit(proc.returncode)
 for cmd in [['proposals/restored_source_only_2013_july_pilot/validate.py'],['proposals/restored_source_only_2019_may30_outtemp/validate.py'],['proposals/restored_source_only_2020_isolated_outtemp/validate.py']]:
  proc=subprocess.run([sys.executable,*cmd],cwd=base,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);results.append({'command':'python3 '+' '.join(cmd)+' post-simulation','returncode':proc.returncode,'output':proc.stdout[-900:]})
  if proc.returncode:print(json.dumps({'status':'FAIL','failed':results[-1]},indent=2));raise SystemExit(proc.returncode)
out={'status':'PASS','archive':ARCHIVE.name,'members':len(names),'manifest_files_verified':len(m['contents']),'clean_extraction':True,'active_packages':5,'active_operations':63,'restored':42,'estimated':21,'unique_timestamps':54,'physical_inserts':52,'updates':11,'commands':results,'database_access':'NONE','mcp_dry_run':'NOT_RUN','staging':False,'application':False}
# Detached result is intentionally not part of the ZIP to avoid a self-referential hash cycle.
(ROOT/'reports/2026-11-13-v5-clean-extract-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='commands'},indent=2))
