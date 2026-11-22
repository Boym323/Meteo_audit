#!/usr/bin/env python3
"""Build the single checksummed A/B/C handoff archive."""
from pathlib import Path
import tempfile,shutil,zipfile,hashlib
R=Path(__file__).resolve().parents[1]
FILES='''
LOUCKA_REMAINING_COMPLETION_FINAL_REPORT.md
EXACT_SOURCE_RESTORATION_FINAL_REVIEW.md
C_PERIOD_SCREEN_README.md
STATISTICAL_COMPLETENESS_POLICY.md
UNIFIED_ARCHIVE_FINAL_REPORT.md
UNIFIED_ARCHIVE_STATUS.md
UNIFIED_ARCHIVE_PROGRESS.json
ARCHIVE_GAP_INTERVALS.csv
ARCHIVE_TIME_COVERAGE.csv
ARCHIVE_STATISTICAL_QUALITY_MATRIX.csv
OWNER_FINAL_APPROVAL_PACKAGE.md
approvals/THREE_SEPARATE_APPROVALS.md
scripts/package_remaining_completion.py
scripts/classify_post_reconstruction_gaps.py
scripts/validate_remaining_completion.py
scripts/validate_gw3000_backfill_payload.py
scripts/build_remaining_period_screen.py
scripts/build_daily_statistical_readiness.py
scripts/build_post_reconstruction_readiness.py
scripts/merge_exact_source_history.py
scripts/archive_sync_cli.py
scripts/run_archive_sync_mariadb_integration.sh
SYNC_DEPLOYMENT_CHECKLIST.md
SYNC_MONITORING_CHECKLIST.md
SYNC_ROLLBACK_PLAN.md
src/meteo_audit/archive_sync.py
src/meteo_audit/archive_sync_writer.py
src/meteo_audit/__init__.py
tests/test_archive_sync.py
tests/test_statistical_readiness_outputs.py
tests/integration/test_archive_sync_mariadb.py
sql/readonly/exact_source_remaining_candidates.sql
sql/readonly/exact_source_candidate_history.sql
sql/readonly/gw3000_insert_only_backfill_snapshot.sql
sql/readonly/remaining_period_statistics.sql
sql/readonly/daily_core_statistical_coverage.sql
sql/migrations/proposed_archive_sync_v1.sql
requirements-sync.txt
data/REMAINING_EXACT_SOURCE_CANDIDATES.csv
data/EXACT_SOURCE_COHORT_DECISIONS.json
data/EXACT_SOURCE_RECONSTRUCTION_HISTORY.json
data/EXACT_SOURCE_PENDING_COHORT_INTERSECTIONS.json
data/GW3000_INSERT_ONLY_BACKFILL_MANIFEST.json
data/GW3000_INSERT_ONLY_BACKFILL_PAYLOAD.jsonl
data/final_readiness_matrix_77x18.csv
data/post_reconstruction_coverage_77x18.json
data/annual_source_archive_field_availability_2009_2020.json
data/post_reconstruction_cadence_histogram.json
data/remaining_monthly_period_screen.csv
data/remaining_annual_period_screen.csv
data/daily_applied_change_counts.json
data/applied_change_counts_all_periods.csv
data/applied_estimated_operations.json
data/additional_primary_change_counts.csv
data/wind_direction_daily_circular.csv
data/daily_archive_additional_primary_2009_2011.csv
data/daily_archive_additional_primary_2012_2014.csv
data/daily_archive_additional_primary_2015_2017.csv
data/daily_archive_additional_primary_2018_2020.csv
data/daily_archive_additional_primary_2021_2023.csv
data/daily_archive_additional_primary_2024_2026.csv
data/archive_unit_interval_distribution.csv
data/monthly_interval_histogram_2009_2026.csv
data/DAILY_STATISTICAL_COVERAGE.csv
data/MONTHLY_STATISTICAL_READINESS.csv
data/ANNUAL_STATISTICAL_READINESS.csv
data/STATISTICAL_READINESS_API.json
reports/2026-11-13-annual-archive-field-availability-2009-2026.csv
reports/2026-11-13-monthly-archive-field-availability-2009-2026.csv
reports/2026-11-13-readiness-77-fields-expanded.json
reports/2026-11-13-annual-archive-field-availability-2009-2026.json
reports/v1_2/approved_operations_322.json
'''.strip().splitlines()
FILES += [f'data/daily_archive_core_{y}.csv' for y in range(2009,2027)]
FILES=list(dict.fromkeys(FILES))
README='''# Loucka remaining completion handoff

This archive contains A/B/C evidence and code. Database artifacts are read-only snapshots. Extraction does not authorize a database change.

## Offline replay (Python 3.10+)

Run: python3 scripts/validate_remaining_completion.py
Run: python3 scripts/validate_gw3000_backfill_payload.py
Run: python3 scripts/build_daily_statistical_readiness.py
Run: python3 scripts/build_remaining_period_screen.py
Run: python3 -m unittest tests.test_statistical_readiness_outputs -v
Run: PYTHONPATH=src python3 -m unittest tests.test_archive_sync -v
Run: python3 scripts/classify_post_reconstruction_gaps.py
Run: python3 scripts/build_post_reconstruction_readiness.py

The readiness replay uses data/final_readiness_matrix_77x18.csv, data/post_reconstruction_coverage_77x18.json, and reports/v1_2/approved_operations_322.json; expected output is 1,386 cells.

The MariaDB 11.8.6 transaction integration suite was run against a throwaway local instance on loopback and passed 7/7. No production or staging database was used. The reproducible Docker runner is scripts/run_archive_sync_mariadb_integration.sh.

C outputs cover eight primary variables; raw values remain review-only where estimated values or unresolved provenance are present. See C_PERIOD_SCREEN_README.md and STATISTICAL_COMPLETENESS_POLICY.md. Other fields remain availability-only and rainfall stays protected under E4.
'''
stage=Path(tempfile.mkdtemp(prefix='loucka-handoff-stage-'))
try:
 for rel in FILES:
  src=R/rel
  if not src.exists():raise FileNotFoundError(rel)
  dst=stage/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 (stage/'BUNDLE_README.md').write_text(README)
 manifest=[]
 for p in sorted(x for x in stage.rglob('*') if x.is_file()):manifest.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(stage).as_posix()}')
 (stage/'SHA256SUMS.txt').write_text('\n'.join(manifest)+'\n')
 out=R/'loucka_remaining_completion_v1.zip'
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(x for x in stage.rglob('*') if x.is_file()):z.write(p,p.relative_to(stage).as_posix())
 print(f'files={len(manifest)} zip_bytes={out.stat().st_size} zip_sha256={hashlib.sha256(out.read_bytes()).hexdigest()}')
finally:shutil.rmtree(stage)
