#!/usr/bin/env python3
"""SUPERSEDED: historical P3 v2 clean-extract reproducer; not active v2.1."""
raise SystemExit('SUPERSEDED P3 v2 clean reproduction; use scripts/validate_v3_clean_extract.py and the active v2.1 package validator')
import hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'proposals/estimated_short_temperature_gaps_v2'
m=json.loads((P/'manifest.json').read_text())
for name,rec in m['artifacts'].items():
 b=(P/name).read_bytes()
 assert len(b)==rec['bytes'] and hashlib.sha256(b).hexdigest()==rec['sha256'],name
for rel in ['sql/readonly/p3_short_temperature_gap_candidates_2019_2020.sql','scripts/simulate_estimated_short_temperature_proposals.py','reports/2026-11-13-temperature-short-gap-interpolation-holdout-2019-07.md','sql/readonly/p3_cross_archive_source_availability_107.sql','sql/readonly/p3_change_event_counts_107.sql','sql/readonly/p3_source_only_nearby_offsets_24.sql','sql/readonly/source_only_primary_availability_2009_2020.sql','scripts/build_p3_source_first_v2.py','scripts/build_p3_review_artifacts.py','scripts/simulate_p3_source_first_v2.py','scripts/validate_source_first_active_proposals.py','scripts/validate_source_only_review_package.py','src/meteo_audit/source_first.py','config/reconstruction_source_first_policy.json','config/active_proposal_registry.json','proposals/estimated_short_temperature_gaps_v2/validate.py','proposals/restored_source_only_rows_v2/validate.py','archives/v1/estimated_short_temperature_gaps/corrections.json']:
 assert (R/rel).is_file(),rel
subprocess.run([sys.executable,str(R/'scripts/simulate_p3_source_first_v2.py')],check=True,capture_output=True,text=True)
subprocess.run([sys.executable,str(R/'scripts/validate_p3_source_first_v2.py')],check=True,capture_output=True,text=True)
subprocess.run([sys.executable,str(R/'scripts/validate_source_first_active_proposals.py')],check=True,capture_output=True,text=True)
subprocess.run([sys.executable,str(R/'scripts/validate_source_only_review_package.py')],check=True,capture_output=True,text=True)
subprocess.run([sys.executable,str(P/'validate.py')],check=True,capture_output=True,text=True)
subprocess.run([sys.executable,str(R/'proposals/restored_source_only_rows_v2/validate.py')],check=True,capture_output=True,text=True)
sys.path.insert(0,str(R/'src'))
spec=importlib.util.spec_from_file_location('test_source_first_guard',R/'tests/test_source_first_guard.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
suite=unittest.defaultTestLoader.loadTestsFromModule(module)
res=unittest.TextTestRunner(verbosity=0).run(suite)
assert res.wasSuccessful()
print(json.dumps({'clean_extract_reproduction':'PASS','manifest_files_verified':len(m['artifacts']),'p3_targets':107,'estimates':24,'review_required':83,'restored':0,'missing':0,'unit_tests':res.testsRun,'db_access':'none'},indent=2))
