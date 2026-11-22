#!/usr/bin/env python3
"""Validate F4 field matrix coverage and conservative lineage/unit claims."""
import csv,json
import hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=json.loads((R/'reports/2026-11-13-annual-archive-field-availability-2009-2026.json').read_text())
matrix=json.loads((R/'data/f4_field_unit_lineage_matrix.json').read_text())
with (R/'data/f4_field_unit_lineage_matrix.csv').open(newline='',encoding='utf-8') as f: csvrows=list(csv.DictReader(f))
expected=sorted({r['variable'] for r in source['records']})
mig=json.loads((R/'data/f4_migration_concordance_2014.json').read_text());mig_by={x['variable']:x for x in mig['fields']}
assert len(expected)==77 and matrix['field_count']==77 and matrix['fields']==expected
rows=matrix['rows'];assert len(rows)==len(csvrows)==77
assert [r['variable'] for r in rows]==expected
assert len({r['variable'] for r in csvrows})==77
assert sum(matrix['migration_evidence_class_counts'].values())==77
assert matrix['physical_sensor_identity']=='UNVERIFIED_FOR_ALL_FIELDS'
assert matrix['driver_configuration'].startswith('HISTORICAL_FILES_UNAVAILABLE_OWNER_ATTESTED')
for row in rows:
 assert row['unit_evidence_scope']=='DATABASE_LEVEL_ONLY; no per-field stored-unit tag is available in archive rows'
 assert row['physical_sensor_identity']=='UNVERIFIED_FOR_THIS_FIELD'
 assert row['source_lineage_confidence']=='FIELD_SPECIFIC_LINEAGE_UNRESOLVED'
 assert row['quality_or_transform_decision']=='NO_AUTOMATIC_RECONSTRUCTION_OR_TRANSFORM'
 assert 'Q1_2018_PROTECTED' in row['protected_year_policy'] and '2021_DIAGNOSTIC_ONLY' in row['protected_year_policy']
 if row['variable'] in {'windSpeed','windGust','windrun'}:
  assert row['migration_evidence_class'].startswith('FIELD_EPOCH_RATIO_SCREENED')
  assert 'HISTORICAL_WIND_TRANSFORMATION_REPORT.md' in row['specific_evidence_refs']
 if row['variable'] in {'rain','rainRate'}:
  assert row['migration_evidence_class'].startswith('FIELD_FACTOR_SCREENED_WITH_EXCEPTIONS')
  assert 'blanket conversion' in row['migration_evidence_summary']
 if row['variable'] in mig_by:
  assert row['2014_source_timestamp_pairs']==mig['source_timestamp_pairs']
  assert row['2014_source_conflict']==mig_by[row['variable']]['source_conflict']
  assert 'data/f4_migration_concordance_2014.json' in row['specific_evidence_refs']
 else: assert row['2014_source_timestamp_pairs'] is None
 if row['variable'] in {'outTemp','outHumidity','rain','rainRate','windSpeed','windGust','windDir','barometer','pressure','altimeter'}:
  assert 'data/historical_migration_core_exact_concordance_2009_2020.json' in row['specific_evidence_refs']
by={r['variable']:r for r in rows}
for r in csvrows:
 j=by[r['variable']]
 for k in ('migration_evidence_class','physical_sensor_identity','driver_config_epoch','source_lineage_confidence','quality_or_transform_decision'):
  assert r[k]==j[k]
assert matrix['input_sha256']['source_inventory.json']
assert matrix['input_sha256']['SOURCE_LINEAGE_OWNER_STATEMENT.md']
assert matrix['input_sha256']['data/f4_migration_concordance_2014.json']
assert mig['field_count']==50 and mig['source_timestamp_pairs']==97228
assert sum(x['merged_nonnull']>0 for x in mig['fields'])==13
sql=R/'sql/readonly/f4_migration_concordance_2014.sql'
assert sql.exists() and sql.read_text().count('SUM(')==50*9
assert matrix['input_sha256']['sql/readonly/f4_migration_concordance_2014.sql']==hashlib.sha256(sql.read_bytes()).hexdigest()
classes={k:sum(r['migration_evidence_class']==k for r in rows) for k in sorted({r['migration_evidence_class'] for r in rows})}
print(json.dumps({'status':'PASS','fields':77,'classes':classes,'2014_shared_fields':50,'2014_timestamp_pairs':mig['source_timestamp_pairs'],'2014_fields_with_merged_values':sum(x['merged_nonnull']>0 for x in mig['fields']),'sensor_identity_verified':0,'automatic_transform_authorized':0,'database_access':'NONE'}))
