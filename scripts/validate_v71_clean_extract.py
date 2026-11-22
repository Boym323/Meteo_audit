#!/usr/bin/env python3
"""Validate checkpoint manifest, clean extraction, and active package invariants."""
import argparse, hashlib, json, subprocess, sys, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,default=ROOT/'loucka_historical_audit_and_priority_corrections_v71.zip');ap.add_argument('--output',type=Path);a=ap.parse_args()
 with zipfile.ZipFile(a.archive) as z:
  names=set(z.namelist());m=json.loads(z.read('MANIFEST.json'))
  assert m['main_report_count']==18 and len(m['contents'])+1==len(names)
  assert (m['active_correction_operation_count'],m['active_restored_operations'],m['active_estimated_operations'])==(65,44,21)
  assert (m['active_unique_timestamps'],m['active_physical_new_database_rows_if_applied'],m['active_update_operations'])==(56,52,13)
  assert (m['approval'],m['actual_weather_mcp_dry_run'],m['application'])==('NOT_APPROVED','NOT_RUN','NOT_APPLIED')
  for x in m['contents']:
   b=z.read(x['path']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],x['path']
  inv=json.loads(z.read('reports/required-report-inventory.json'));assert inv['required_report_count']==18
  for p in ('data/source_only_2010_2011_field_aggregates.json','data/2010_source_only_field_eligibility.json','data/2011_source_only_field_eligibility.json','sql/readonly/source_only_2010_2011_field_aggregates/part01.sql','data/2019_source_only_field_eligibility.json','data/2020_source_only_field_eligibility.json','reports/2026-11-14-2018-q2-q4-source-only-field-eligibility.md'):assert p in names
 with tempfile.TemporaryDirectory(prefix='loucka-v71-clean-') as td:
  with zipfile.ZipFile(a.archive) as z:z.extractall(td)
  cmds=[['scripts/validate_2018_q2_q4_source_only_field_eligibility.py'],['scripts/validate_source_only_2011_two_outtemp_conflicts.py'],['scripts/validate_2010_2011_source_only_field_eligibility.py'],['scripts/validate_2009_2012_2013_source_only_field_eligibility.py'],['scripts/validate_2019_2020_source_only_field_eligibility.py'],['proposals/estimated_short_temperature_gaps_v2/validate.py'],['proposals/estimated_short_temperature_gaps_v2/simulate_v2_1.py','--output','/tmp/v71_p3_simulation.json'],['proposals/restored_source_only_2013_july_pilot/validate.py'],['scripts/validate_2018_dec31_restored_update_pilot.py'],['proposals/restored_source_only_2019_may30_outtemp/validate.py'],['proposals/restored_source_only_2020_isolated_outtemp/validate.py'],['proposals/restored_rh_2014_boundary_pilot/validate.py'],['proposals/restored_rh_2014_midpoint_pilot/validate.py'],['scripts/validate_active_proposal_deduplication.py'],['scripts/validate_source_first_active_proposals.py']]
  results=[]
  for c in cmds:
   r=subprocess.run([sys.executable,*c],cwd=td,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   results.append({'command':'python3 '+' '.join(c),'returncode':r.returncode,'output':r.stdout.strip()[-1200:]})
   if r.returncode:raise SystemExit(json.dumps(results[-1],indent=2))
 out={'status':'PASS','archive':a.archive.name,'verified_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'members':len(names),'manifest_entries_verified':len(m['contents']),'clean_extraction':True,'main_reports':18,'active_operations':65,'RESTORED':44,'ESTIMATED':21,'unique_timestamps':56,'physical_inserts':52,'updates':13,'commands':results,'database_access':'NONE','MCP_dry_run':'NOT_RUN','staging':False,'application':False}
 if a.output:a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
