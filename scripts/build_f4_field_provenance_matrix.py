#!/usr/bin/env python3
"""Consolidate existing source/unit/epoch evidence for every numeric archive field."""
import csv,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
ANNUAL=R/'reports/2026-11-13-annual-archive-field-availability-2009-2026.json'
MONTHLY=R/'reports/2026-11-13-monthly-archive-field-availability-2009-2026.csv'
UNITS=R/'reports/2026-11-12-archive-unit-system-mapping.csv'
CORE=R/'data/historical_migration_core_exact_concordance_2009_2020.json'
WIND=R/'data/historical_wind_transformation_annual.json'
CONV=R/'data/historical_migration_conversion_factor_2009_2020.json'
OWNER=R/'SOURCE_LINEAGE_OWNER_STATEMENT.md'
INV=R/'source_inventory.json'
MIG2014=R/'data/f4_migration_concordance_2014.json'
MIG2014_SQL=R/'sql/readonly/f4_migration_concordance_2014.sql'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_csv(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
annual=json.loads(ANNUAL.read_text()); fields=sorted({x['variable'] for x in annual['records']})
assert len(fields)==77
availability={field:[] for field in fields}
for r in read_csv(MONTHLY):
 if int(r['nonnull_rows'])>0: availability.setdefault(r['variable'],[]).append((int(r['year']),int(r['month_utc']),int(r['nonnull_rows'])))
assert set(availability)==set(fields)
unit_rows=read_csv(UNITS);unit_map={r['archive']:r for r in unit_rows}
assert len(unit_map)==6
core=json.loads(CORE.read_text());core_fields=set(core['fields'])
wind=json.loads(WIND.read_text());wind_fields={'windSpeed','windGust','windrun'}
conv=json.loads(CONV.read_text());factor_fields=set(conv['fields'])
mig2014=json.loads(MIG2014.read_text());mig2014_by_field={x['variable']:x for x in mig2014['fields']}
annual_by_field={}
for field in fields:
 rs=[r for r in annual['records'] if r['variable']==field]
 annual_by_field[field]={'years_present':sum(int(r['nonnull_rows'])>0 for r in rs),'total_nonnull_year_rows':sum(int(r['nonnull_rows']) for r in rs)}
rows=[]
for field in fields:
 ep=availability.get(field,[])
 if field in wind_fields:
  kind='FIELD_EPOCH_RATIO_SCREENED_AND_2014_CONCORDANCE' if field in mig2014_by_field else 'FIELD_EPOCH_RATIO_SCREENED'
  if field=='windSpeed': detail='METRICWX→METRIC comparison: raw ratio 1 in 2009–2012; mixed through 2013; dominant 3.6 in 2014–2019; 2020 exceptions.'
  elif field=='windGust': detail='Separate gust ratio screen: raw ratio 1 in 2009–2012; mixed through 2013; dominant 3.6 in 2014–2019; 2020 exceptions.'
  else: detail='Separate windrun ratio screen: roughly 1/3.6 before 2013 transition; ratio 1 thereafter; 2020 exceptions. Do not apply windSpeed factor.'
 elif field in factor_fields:
  kind='FIELD_FACTOR_SCREENED_WITH_EXCEPTIONS_AND_2014_CONCORDANCE' if field in mig2014_by_field else 'FIELD_FACTOR_SCREENED_WITH_EXCEPTIONS'
  detail='Expected unit factor is screened but observed ratios are nonuniform; counter/interval/aggregation and exceptions prevent a blanket conversion.'
 elif field in mig2014_by_field:
  kind='2014_EXACT_FIELD_CONCORDANCE_SCREENED'
  detail='One bounded exact-time aggregate covers the shared field in old_weewx, weewx_WH1080 and eu_old for 2014; copy equality, NULL coverage and merged equality/differences are recorded. This single year does not establish the historical transform rule.'
 elif field in core_fields:
  kind='CORE_EXACT_TIMESTAMP_CONCORDANCE_AVAILABLE'
  detail='Included in exact-timestamp source-copy and merged-value aggregate; per-year field equality/conflicts are documented in the core concordance JSON. This is not proof of physical sensor identity or correctness.'
 else:
  kind='NO_SHARED_LEGACY_FIELD_OR_MIGRATION_CROSSWALK'
  detail='This numeric archive field is not shared by all three legacy schemas in the 2014 metadata snapshot; no field-specific migration crosswalk is available for this cohort.'
 if not ep:
  first=last='NO_NON_NULL_ARCHIVE_MONTH';months=0;nonnull=0
 else:
  min_y,min_m=min((x[0],x[1]) for x in ep);max_y,max_m=max((x[0],x[1]) for x in ep)
  first=f'{min_y:04d}-{min_m:02d}'
  last=f'{max_y:04d}-{max_m:02d}'
  months=len(ep);nonnull=sum(x[2] for x in ep)
 rows.append({
 'variable':field,
 'observed_first_utc_month':first,'observed_last_utc_month':last,'months_with_nonnull':months,'nonnull_rows_in_monthly_availability_matrix':nonnull,
 'archive_years_with_nonnull':annual_by_field[field]['years_present'],'annual_nonnull_rows_sum':annual_by_field[field]['total_nonnull_year_rows'],
 'database_unit_codes_global':'; '.join(f"{a}={unit_map[a]['usUnits_decimal']}({unit_map[a]['standard_weewx_encoding']})" for a in sorted(unit_map)),
 'unit_evidence_scope':'DATABASE_LEVEL_ONLY; no per-field stored-unit tag is available in archive rows',
 'migration_evidence_class':kind,'migration_evidence_summary':detail,
 '2014_source_timestamp_pairs':mig2014['source_timestamp_pairs'] if field in mig2014_by_field else None,
 '2014_source_old_nonnull':mig2014_by_field[field]['old_nonnull'] if field in mig2014_by_field else None,
 '2014_source_wh_nonnull':mig2014_by_field[field]['wh_nonnull'] if field in mig2014_by_field else None,
 '2014_source_both_nonnull':mig2014_by_field[field]['both_nonnull'] if field in mig2014_by_field else None,
 '2014_source_equal':mig2014_by_field[field]['source_equal'] if field in mig2014_by_field else None,
 '2014_source_conflict':mig2014_by_field[field]['source_conflict'] if field in mig2014_by_field else None,
 '2014_merged_nonnull':mig2014_by_field[field]['merged_nonnull'] if field in mig2014_by_field else None,
 '2014_merged_matches_old':mig2014_by_field[field]['merged_matches_old'] if field in mig2014_by_field else None,
 '2014_merged_matches_wh':mig2014_by_field[field]['merged_matches_wh'] if field in mig2014_by_field else None,
 '2014_merged_matches_neither':mig2014_by_field[field]['merged_matches_neither'] if field in mig2014_by_field else None,
 'physical_sensor_identity':'UNVERIFIED_FOR_THIS_FIELD',
 'driver_config_epoch':'NOT_AVAILABLE; exact historical configurations and migration rules are not identified',
 'owner_attestation':'OWNER_ATTESTED general historical cleaning/merging and wind recalculation; no field-specific operation log',
 'source_lineage_confidence':'FIELD_SPECIFIC_LINEAGE_UNRESOLVED',
 'quality_or_transform_decision':'NO_AUTOMATIC_RECONSTRUCTION_OR_TRANSFORM',
 'source_evidence_refs':'source_inventory.json; reports/2026-11-12-archive-unit-system-mapping.csv; reports/2026-11-13-monthly-archive-field-availability-2009-2026.csv; HISTORICAL_MIGRATION_AND_CLEANING_REPORT.md',
 'specific_evidence_refs':'; '.join(x for x in (('HISTORICAL_WIND_TRANSFORMATION_REPORT.md; data/historical_wind_transformation_annual.json' if field in wind_fields else ''),('data/historical_migration_conversion_factor_2009_2020.json' if field in factor_fields else ''),('data/historical_migration_core_exact_concordance_2009_2020.json' if field in core_fields else ''),('data/f4_migration_concordance_2014.json; sql/readonly/f4_migration_concordance_2014.sql' if field in mig2014_by_field else '')) if x),
 'protected_year_policy':'2021_DIAGNOSTIC_ONLY; Q1_2018_PROTECTED'
 })

summary={'schema':'f4-field-unit-lineage-matrix-v1','fields':fields,'field_count':len(fields),'evidence_scope':'Existing archive metadata, exact-time migration concordance, annual source-unit factor screens, monthly non-NULL availability spans, and one new bounded 2014 exact-time source/merge comparison.',
 '2014_migration_comparison':{'year':2014,'shared_fields':mig2014['field_count'],'exact_source_timestamp_pairs':mig2014['source_timestamp_pairs'],'query_execution_utc':mig2014.get('query_execution_utc'),'writes':0},
 'archive_unit_codes':{a:{'usUnits':int(r['usUnits_decimal']),'weewx_name':r['standard_weewx_encoding'],'distribution':r['unit_distribution_status']} for a,r in unit_map.items()},
 'migration_evidence_class_counts':{},'physical_sensor_identity':'UNVERIFIED_FOR_ALL_FIELDS','driver_configuration':'HISTORICAL_FILES_UNAVAILABLE_OWNER_ATTESTED; FIELD-SPECIFIC_RULES_UNRESOLVED',
 'owner_statements':'OWNER_ATTESTED; exact database origins, transition dates and merge/clean rules unknown; historical wind recalculation, stuck-value repair and extreme removal reported.',
 'rows':rows,'input_sha256':{str(p.relative_to(R)):sha(p) for p in (ANNUAL,MONTHLY,UNITS,CORE,WIND,CONV,OWNER,INV,MIG2014,MIG2014_SQL)},
 'limitations':['Global usUnits distributions do not establish that every field was expressed in that unit for every historical epoch.','Source-copy or merged-archive concordance does not establish independent sensors or meteorological correctness.','Field-specific physical identity and exact driver/config transformations are unavailable.','The matrix inventories known evidence and explicit gaps; it does not license any conversion or RESTORED proposal.','No database query, write, staging, application, or publication occurred.']}
from collections import Counter
summary['migration_evidence_class_counts']=dict(Counter(x['migration_evidence_class'] for x in rows))
with (R/'data/f4_field_unit_lineage_matrix.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(R/'data/f4_field_unit_lineage_matrix.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'fields':len(rows),'classes':summary['migration_evidence_class_counts']}))
