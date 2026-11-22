#!/usr/bin/env python3
"""Build a reproducible v2 audit ZIP without changing the preserved v1 archive."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1]
inv=json.loads((R/'reports/required-report-inventory.json').read_text())
paths={R/'reports'/x['report'] for x in inv['reports']}
paths|={R/x for x in ['MASTER_PLAN.md','GOAL_ADDENDUM.md','STATUS.md','PROGRESS.json','EXPERT_REVIEW_REQUIRED.md','reports/required-report-inventory.json','reports/MASTER_AUDIT_REPORT.md','reports/CONSOLIDATED_CORRECTIONS_REPORT.md','reports/NEXT_STEPS.md','reports/P3_INDEPENDENT_REVIEW.md','reports/SOURCE_ONLY_ROWS_2009_2020.md','reports/2026-11-13-source-only-field-availability-2009-2020.csv','reports/SOURCE_FIRST_RECONSTRUCTION_FRAMEWORK.md','reports/2026-11-13-temperature-short-gap-interpolation-holdout-2019-07.md']}
for pkg in ['restored_temperature','restored_humidity','estimated_short_temperature_gaps','estimated_short_temperature_gaps_v2','estimated_humidity_2022','restored_secondary_sensors','restored_source_only_rows_v2']:
 d=R/'proposals'/pkg
 if d.exists(): paths.update(p for p in d.rglob('*') if p.is_file())
paths|={p for p in (R/'archives/v1').rglob('*') if p.is_file()}
paths|={p for p in (R/'data/p3_independent_review').rglob('*') if p.is_file()}
paths|={R/p for p in [
 'loucka_historical_audit_and_priority_corrections_v1.zip',
 'src/meteo_audit/source_first.py','tests/test_source_first_guard.py',
 'config/reconstruction_source_first_policy.json','config/active_proposal_registry.json',
 'scripts/build_p3_conditional_holdout_sql.py','scripts/build_p3_source_first_v2.py','scripts/build_p3_review_artifacts.py',
 'scripts/simulate_p3_source_first_v2.py','scripts/validate_source_first_active_proposals.py','scripts/reproduce_p3_v2_clean.py',
 'scripts/validate_p3_source_first_v2.py','scripts/validate_source_only_review_package.py',
 'scripts/build_priority_corrections_v2_zip.py','scripts/simulate_estimated_short_temperature_proposals.py',
 'scripts/build_progress_overview.py','scripts/build_expert_review_register.py','scripts/validate_expert_review_register.py',
 'reports/2026-11-13-expert-review-register.csv',
 'scripts/summarize_source_only_common_fields.py','sql/readonly/source_only_common_numeric_fields_2009_2020.sql',
 'scripts/run_audit_checkpoint.py','config/source-only-common-fields-checkpoint.json','runs/20261113T084454Z-922430ad/manifest.json',
 'sql/readonly/p3_short_temperature_gap_candidates_2019_2020.sql',
 'sql/readonly/p3_conditional_holdout_10m_2019_2020.sql','sql/readonly/p3_conditional_holdout_15m_2019_2020.sql','sql/readonly/p3_conditional_holdout_20m_2019_2020.sql','sql/readonly/p3_conditional_holdout_25m_2019_2020.sql',
 'sql/readonly/p3_extrema_holdout_10m_2019_2020.sql','sql/readonly/p3_extrema_holdout_15m_2019_2020.sql','sql/readonly/p3_extrema_holdout_20m_2019_2020.sql','sql/readonly/p3_extrema_holdout_25m_2019_2020.sql',
 'sql/readonly/p3_cross_archive_source_availability_107.sql','sql/readonly/p3_change_event_counts_107.sql','sql/readonly/p3_source_only_nearby_offsets_24.sql','sql/readonly/source_only_primary_availability_2009_2020.sql']}
paths={p for p in paths if p.is_file()}
out=R/'loucka_historical_audit_and_priority_corrections_v2.zip'
files=sorted(paths,key=lambda p:p.relative_to(R).as_posix())
manifest={'archive':out.name,'status':'PRIORITY_AUDIT_AND_P3_SOURCE_FIRST_REVISION_WITH_LIMITATIONS','required_main_reports':18,'required_reports_included':sum((R/'reports'/x['report']).is_file() for x in inv['reports']),'p3_v2_counts':{'targets':107,'RESTORED':0,'ESTIMATED':24,'REVIEW_REQUIRED':83,'MISSING':0},'source_only_2009_2020_unique_timestamps':207182,'p3_v1_preserved':True,'batch_limit':50,'database_access':'READ_ONLY_SELECT_ONLY','database_writes_or_staging':0,'q1_2018':'excluded/protected','year_2021':'diagnostic_only','publication':False,'contents':[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
assert manifest['required_reports_included']==18
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in files:z.write(p,p.relative_to(R).as_posix())
 z.writestr('MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
ext={'archive':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'entries':len(files)+1,'required_main_reports':18,'p3_v2_counts':manifest['p3_v2_counts'],'source_only_2009_2020_unique_timestamps':207182,'limitations':['P3 v2 has 83 unresolved exact-source conflicts; no restoration is emitted.','24 ESTIMATED values have condition-specific synthetic holdout summaries, not guaranteed intervals.','Source-only aggregate is screening evidence, not approved restoration.','No database writes, staging, Q1 2018, 2021 correction, derived-variable mutation or publication.']}
(R/'reports/2026-11-13-priority-v2-zip-manifest.json').write_text(json.dumps(ext,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(ext,ensure_ascii=False,indent=2))
