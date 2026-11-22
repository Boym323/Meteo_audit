#!/usr/bin/env python3
"""Validate v94 checkpoint manifest, clean extraction, and active package invariants."""
import argparse, hashlib, json, subprocess, sys, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,default=ROOT/'loucka_historical_audit_and_priority_corrections_v94.zip');ap.add_argument('--output',type=Path);a=ap.parse_args()
 with zipfile.ZipFile(a.archive) as z:
  names=set(z.namelist());m=json.loads(z.read('MANIFEST.json'))
  assert m['main_report_count']==18 and len(m['contents'])+1==len(names)
  assert (m['active_correction_operation_count'],m['active_restored_operations'],m['active_estimated_operations'])==(324,303,21)
  assert (m['active_unique_timestamps'],m['active_physical_new_database_rows_if_applied'],m['active_update_operations'])==(315,311,13)
  assert (m['approval'],m['actual_weather_mcp_dry_run'],m['application'])==('NOT_APPROVED','NOT_RUN','NOT_APPLIED')
  for x in m['contents']:
   b=z.read(x['path']);assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'],x['path']
  inv=json.loads(z.read('reports/required-report-inventory.json'));assert inv['required_report_count']==18
  pr=json.loads(z.read('PROGRESS.json'));assert pr['overall']['verified_subtasks']==137 and pr['overall']['defined_subtasks']==142
  assert (pr['checkpoint']['consolidated_archive'],pr['checkpoint']['clean_extract_validation'])==(m['archive'],'PENDING_POST_BUILD')
  for st in pr['stages']:
   assert st['verified_subtasks']==sum(x.get('verified') is True for x in st.get('subtasks',[])),st['id']
   assert st['defined_subtasks']==len(st.get('subtasks',[])),st['id']
   expected=[x for x in st.get('subtasks',[]) if x.get('status') not in ('COMPLETED','COMPLETED_WITH_LIMITATIONS')]
   assert len(st.get('remaining_subtasks',[]))==len(expected),st['id']
  assert 'reports/2026-11-14-stage-closeout-review-v88.md' in names
  for path in ('data/source_only_2012_nearest_slot_review.json','sql/readonly/source_only_2012_nearest_slot_review.sql','reports/2026-11-14-source-only-2012-nearest-slot-review.md','scripts/validate_source_only_2012_nearest_slot_review.py','reports/2026-11-14-source-only-2012-nearest-slot-validation.json','reports/v93_validation_metadata_erratum.md'): assert path in names
  align12=json.loads(z.read('data/source_only_2012_nearest_slot_review.json'))
  assert align12['cohort']['target_absent_source_pairs']==8424 and align12['alignment']['unique_nearest_target_slots']==8421 and len(align12['projection_collisions'])==3
  assert align12['decision']['restored_proposals']==0 and align12['decision']['estimated_proposals']==0
  for path in ('data/source_only_2010_nearest_slot_review.json','sql/readonly/source_only_2010_nearest_slot_review.sql','reports/2026-11-14-source-only-2010-nearest-slot-review.md','scripts/validate_source_only_2010_nearest_slot_review.py','reports/2026-11-14-source-only-2010-nearest-slot-validation.json'): assert path in names
  align=json.loads(z.read('data/source_only_2010_nearest_slot_review.json'))
  assert align['cohort']['target_absent_source_pairs']==1989 and align['alignment']['unique_nearest_target_slots']==1983 and len(align['projection_collisions'])==6
  assert align['decision']['restored_proposals']==0 and align['decision']['estimated_proposals']==0
  for path in ('data/historical_wind_2020_aug20_sep1_review.json','sql/readonly/historical_wind_2020_aug20_sep1_review.sql','reports/2026-11-14-historical-wind-2020-anomaly-review.md','scripts/validate_historical_wind_2020_anomaly_review.py','reports/2026-11-14-historical-wind-2020-anomaly-validation.json'): assert path in names
  wind=json.loads(z.read('data/historical_wind_2020_aug20_sep1_review.json'))
  assert wind['evidence']['windSpeed_ratio_3_6_within_0_001']==801 and wind['evidence']['windGust_ratio_3_6_within_0_001']==1906
  assert wind['decision']['disposition']=='REVIEW_REQUIRED' and wind['decision']['correction_proposals']==0
  for p in ('data/b5_2019_short_gap_exact_slot_source_review.json','data/b5_2019_short_gap_exact_slot_source_disposition.json','sql/readonly/b5_2019_short_gap_exact_slot_source_review.sql','reports/2026-11-14-B5-2019-short-gap-source-disposition.md','scripts/validate_b5_2019_short_gap_source_disposition.py','EXPERT_REVIEW_REQUIRED.md','scripts/validate_expert_review_register.py'):assert p in names
  disp=json.loads(z.read('data/b5_2019_short_gap_exact_slot_source_disposition.json')); assert disp['dispositions']['REVIEW_REQUIRED_POSSIBLE_HISTORICAL_OUTTEMP_NULLING'] + disp['dispositions']['REVIEW_REQUIRED_SOURCE_RH_CONFLICT_AND_LOCAL_TEMP_OFFSET']==9
  assert m['clean_extract_validation']=='PENDING_POST_BUILD'
  for p in ('reports/2026-11-14-gw1000-gw3000-rainrate-disposition.md','data/gw1000_gw3000_rainrate_mismatch_patterns_2009_2020.json','data/gw1000_gw3000_rainrate_nonzero_ratio_profile_2009_2020.json','sql/readonly/gw1000_gw3000_rainrate_mismatch_patterns_2009_2020.sql','sql/readonly/gw1000_gw3000_rainrate_ratio_profile_2009_2020.sql','scripts/export_gw1000_gw3000_rainrate_mismatch_patterns.py','scripts/validate_gw1000_gw3000_rainrate_mismatch_patterns.py','reports/2026-11-14-B5-short-gap-zero-temperature-2016-2017.md','data/b5_short_gap_zero_outtemp_2016_2017_review.json','scripts/review_short_gap_zero_temperature_2016_2017.py','scripts/validate_short_gap_zero_temperature_2016_2017.py','reports/2026-11-14-B5-short-gap-zero-temperature-2014-2015.md','data/b5_short_gap_zero_outtemp_2014_2015_review.json','scripts/review_short_gap_zero_temperature_2014_2015.py','scripts/validate_short_gap_zero_temperature_2014_2015_review.py','reports/2026-11-14-B5-2016-2017-nonzero-temperature-review.md','data/b5_2016_2017_nonzero_temperature_candidates.json','scripts/validate_b5_2016_2017_nonzero_temperature_review.py','data/b5_2014_2015_gap_episode_quality.json','data/b5_2014_2015_nonzero_candidate_context.json','reports/2026-11-14-B5-2014-2015-temperature-episode-review.md','data/source_only_2010_2011_field_aggregates.json','data/2010_source_only_field_eligibility.json','data/2011_source_only_field_eligibility.json','sql/readonly/source_only_2010_2011_field_aggregates/part01.sql','data/2019_source_only_field_eligibility.json','data/2020_source_only_field_eligibility.json','reports/2026-11-14-source-only-cohort-scope-matrix.md'):assert p in names
 with tempfile.TemporaryDirectory(prefix='loucka-v94-clean-') as td:
  with zipfile.ZipFile(a.archive) as z:z.extractall(td)
  cmds=[['scripts/validate_source_only_cohort_scope_matrix.py'],['scripts/validate_b5_2009_2013_gap_dispositions.py'],['scripts/validate_b5_2009_on_grid_candidate_temperature.py'],['scripts/validate_b5_2009_2013_gap_availability.py'],['scripts/validate_2014_source_only_scope_reconciliation.py'],['scripts/validate_2018_q2_q4_source_only_field_eligibility.py'],['scripts/validate_source_only_2011_two_outtemp_conflicts.py'],['scripts/validate_2010_2011_source_only_field_eligibility.py'],['scripts/validate_2009_2012_2013_source_only_field_eligibility.py'],['scripts/validate_2019_2020_source_only_field_eligibility.py'],['proposals/estimated_short_temperature_gaps_v2/validate.py'],['proposals/estimated_short_temperature_gaps_v2/simulate_v2_1.py','--output','/tmp/v72_p3_simulation.json'],['proposals/restored_source_only_2013_july_pilot/validate.py'],['scripts/validate_2018_dec31_restored_update_pilot.py'],['proposals/restored_source_only_2019_may30_outtemp/validate.py'],['proposals/restored_source_only_2020_isolated_outtemp/validate.py'],['proposals/restored_rh_2014_boundary_pilot/validate.py'],['proposals/restored_rh_2014_midpoint_pilot/validate.py'],['scripts/validate_active_proposal_deduplication.py'],['scripts/validate_source_first_active_proposals.py'],['proposals/restored_source_only_2022_august_outtemp/validate.py'],['proposals/restored_source_only_2022_august_outtemp/simulate.py'],['scripts/validate_b5_2014_2015_temperature_episode_review.py'],['scripts/validate_b5_2016_2017_nonzero_temperature_review.py'],['scripts/validate_short_gap_zero_temperature_2014_2015_review.py'],['scripts/validate_short_gap_zero_temperature_2016_2017.py'],['scripts/validate_gw1000_gw3000_rainrate_mismatch_patterns.py'],['proposals/restored_source_only_2023_may_outtemp/validate.py'],['proposals/restored_source_only_2023_may_outtemp/simulate.py'],['proposals/restored_source_only_2020_march_outtemp/validate.py'],['proposals/restored_source_only_2020_march_outtemp/simulate.py'],['proposals/restored_source_only_2020_march_outtemp_v2/validate.py'],['proposals/restored_source_only_2020_march_outtemp_v2/simulate.py'],['scripts/validate_o4_readiness_matrix.py'],['scripts/validate_source_only_remaining_strict_copy_current.py'],['scripts/validate_b5_2024_2025_no_source_gaps.py'],['scripts/validate_b5_2019_short_gap_source_disposition.py'],['scripts/validate_expert_review_register.py'],['scripts/validate_historical_wind_2020_anomaly_review.py'],['scripts/validate_source_only_2010_nearest_slot_review.py'],['scripts/validate_source_only_2012_nearest_slot_review.py']]
  results=[]
  for c in cmds:
   r=subprocess.run([sys.executable,*c],cwd=td,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
   results.append({'command':'python3 '+' '.join(c),'returncode':r.returncode,'output':r.stdout.strip()[-1200:]})
   if r.returncode:raise SystemExit(json.dumps(results[-1],indent=2))
 out={'status':'PASS','archive':a.archive.name,'verified_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'members':len(names),'manifest_entries_verified':len(m['contents']),'clean_extraction':True,'main_reports':18,'active_operations':324,'RESTORED':303,'ESTIMATED':21,'unique_timestamps':315,'physical_inserts':311,'updates':13,'commands':results,'database_access':'NONE','MCP_dry_run':'NOT_RUN','staging':False,'application':False}
 if a.output:a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
