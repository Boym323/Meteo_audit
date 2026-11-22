#!/usr/bin/env python3
"""Build final use-case readiness decisions from the frozen 77x18 availability audit."""
import csv,json
from datetime import datetime as dt,timezone as tz
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
base=json.loads((R/'reports/2026-11-13-readiness-77-fields-expanded.json').read_text())
annual=json.loads((R/'reports/2026-11-13-annual-archive-field-availability-2009-2026.json').read_text())
source=json.loads((R/'data/annual_source_archive_field_availability_2009_2020.json').read_text())
monthly={}
with (R/'reports/2026-11-13-monthly-archive-field-availability-2009-2026.csv').open(newline='') as f:
 for x in csv.DictReader(f):
  if int(x['nonnull_rows'])>0:monthly.setdefault(x['variable'],[]).append(f"{int(x['year']):04d}-{int(x['month_utc']):02d}")
src={}
for archive,yrrows in source['data'].items():
 for yr in yrrows:
  for field,counts in yr['fields'].items():src[(int(yr['year']),field,archive)]=int(counts['nonnull'])
reg=json.loads((R/'config/active_proposal_registry.json').read_text())
ops=defaultdict(int); proposed_sources=defaultdict(Counter)
for pkg in reg['packages']:
 if pkg['status']!='ACTIVE':continue
 for op in pkg.get('operation_keys',[]):
  import datetime
  y=datetime.datetime.fromtimestamp(int(op['timestamp']),datetime.timezone.utc).year
  ops[(y,op['variable'])]+=1
  proposed_sources[(y,op['variable'])][pkg['package_id']]+=1
records=[]
for b in base['records']:
 y=int(b['utc_year']);f=b['variable'];nn=int(b['nonnull_rows']); ar=int(b['archive_rows']); source_info={}
 for a in ('old_weewx','weewx_WH1080'):
  val=src.get((y,f,a));
  if val is not None:source_info[a]={'nonnull_rows_in_annual_archive':val,'scope':'annual archive counts; not exact timestamp join; copies are not independent'}
 source_nonnull=sum(x['nonnull_rows_in_annual_archive'] for x in source_info.values()) if source_info else None
 if nn>0:
  origin='NOT_CLASSIFIED'; q='REVIEW_REQUIRED'; availability='PRESENT_IN_RECONSTRUCTION_SNAPSHOT'
  missing_cause='NOT_APPLICABLE_VALUE_PRESENT'
 elif source_nonnull and source_nonnull>0:
  origin='NOT_AVAILABLE';q='REVIEW_REQUIRED';availability='NO_NONNULL_IN_TARGET; LEGACY_SOURCE_VALUES_EXIST'
  missing_cause='SOURCE_ARCHIVE_VALUES_EXIST_BUT_EXACT_TARGET_COVERAGE_AND_CAUSE_UNRESOLVED'
 elif source_info and source_nonnull==0:
  origin='NOT_AVAILABLE';q='REVIEW_REQUIRED';availability='NO_NONNULL_IN_TARGET_OR_TWO_LEGACY_ANNUAL_SNAPSHOTS'
  missing_cause='SENSOR_EPOCH_VS_LOSS_UNRESOLVED'
 else:
  origin='NOT_AVAILABLE';q='REVIEW_REQUIRED';availability='NO_NONNULL_IN_TARGET; CROSS_ARCHIVE_SOURCE_STATE_NOT_AVAILABLE_FOR_THIS_CELL'
  missing_cause='SENSOR_EPOCH_VS_LOSS_UNRESOLVED'
 if y==2021:
  protection='DIAGNOSTIC_ONLY'; display=graph=stats=ext=trend=atlas='DIAGNOSTIC_ONLY'
 elif y==2018:
  protection='Q1_2018_PROTECTED_ANNUAL_CELL_CONTAINS_INTERIM_PERIOD'; display=graph=stats=ext=trend=atlas='REVIEW_REQUIRED_PROTECTED_Q1_2018'
 else:
  protection='NONE'
  display='READY_WITH_LIMITATIONS_RAW_AS_RECORDED' if nn else 'NOT_AVAILABLE'
  graph='READY_WITH_LIMITATIONS_BREAK_GAPS_NO_IMPUTATION' if nn else 'NOT_AVAILABLE'
  stats='REVIEW_REQUIRED' if nn else 'NOT_AVAILABLE'
  ext='REVIEW_REQUIRED_NO_RECORD_CERTIFICATION' if nn else 'NOT_AVAILABLE'
  trend='REVIEW_REQUIRED_EPOCH_UNITS_AND_MISSINGNESS' if nn else 'NOT_AVAILABLE'
  atlas='REVIEW_REQUIRED_QUALITY_GEOREFERENCE_AND_REFERENCE_RIGHTS' if nn else 'NOT_AVAILABLE'
 observed=monthly.get(f,[])
 records.append({'utc_year':y,'variable':f,'archive_rows':ar,'nonnull_rows':nn,'null_rows':int(b['null_rows']),
  'active_unapproved_proposal_operations':ops[(y,f)],'active_proposal_packages':dict(proposed_sources[(y,f)]),
  'raw_origin_classification':origin,'quality_review_status':q,'availability_state':availability,
  'source_archives_annual_nonnull':source_info,'source_annual_counts_are_not_unique_union':True,
  'availability_interpretation':missing_cause,'observed_nonnull_archive_period_months':{'first':min(observed) if observed else None,'last':max(observed) if observed else None,'continuous_sensor_epoch_proven':False},
  'raw_value_display':display,'historical_graph':graph,'daily_statistics':stats,'monthly_statistics':stats,'annual_statistics':('REVIEW_REQUIRED_PARTIAL_YEAR_AND_DATA_QC' if y==2026 and nn else ('NOT_AVAILABLE' if y==2026 else stats)),
  'records_and_extremes':ext,'long_term_trends':trend,'meteorological_atlas':atlas,'protection_status':protection,'year_completeness':'PARTIAL_YEAR' if y==2026 else 'FULL_UTC_CALENDAR_YEAR_AVAILABILITY_SNAPSHOT',
  'missing_classification_rule':'Do not assign MISSING from an empty year-field cell; only use MISSING for an exact expected slot inside an independently supported operating cadence/epoch.',
  'proposal_state_note':'Active proposal operations are not in the reconstruction archive and are not approved/applied.' if ops[(y,f)] else None})
counts={k:Counter(x[k] for x in records) for k in ('raw_value_display','historical_graph','daily_statistics','records_and_extremes','long_term_trends','meteorological_atlas','availability_state')}
out={'schema':'loucka-final-readiness-matrix-v1','created_utc':dt.now(tz.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'scope':{'database_snapshot':'loucka_reconstruction annual archive availability snapshot 2009–2026' ,'variables':77,'utc_years':list(range(2009,2027)),'cells':len(records),'active_operation_count':reg['active_operation_count'],'proposal_included_in_availability':False,'partial_years':[2026]},
 'policy':{'raw_display':'Show existing values only exactly as stored, labeled ORIGINAL_UNVERIFIED/NOT_CLASSIFIED; show gaps and review flags. Exclude unapproved proposals. This is not a claim of accuracy.',
 'historical_graphs':'May plot existing values with gaps broken and no interpolated line; show source/quality annotations. Q1 2018 excluded; 2021 diagnostic-only.',
 'daily_monthly_annual_statistics':'REVIEW_REQUIRED until per-record quality, expected cadence/denominator and all relevant corrections are reconciled.',
 'records_extremes':'REVIEW_REQUIRED; never certify records/maxima/minima from an unverified or partially reconstructed series.',
 'long_term_trends':'REVIEW_REQUIRED until epoch, units, historical transforms, missingness and source lineage are cleared.',
 'atlas':'REVIEW_REQUIRED until data QC, source attribution, site coordinates and reference-data rights are cleared.',
 'missing_vs_sensor_absence':'No non-NULL annual cell is NOT_AVAILABLE in that archive snapshot, not proof of absent sensor or lost observation. Source archives can show possible source-only values but not intention or truth.',
 'origin_classes':'ORIGINAL is not asserted for raw values without row-level provenance; active proposals use RESTORED/ESTIMATED only in sidecars; CORRECTED only for an applied auditable correction; MISSING only for confirmed expected slots; NOT_AVAILABLE only for a target cell with no value.',
 'protected_periods':'2018 annual cells held because Q1 is protected and not separated by this year-level matrix; 2021 diagnostic only.'},
 'readiness_counts':{k:dict(v) for k,v in counts.items()},'limitations':['Matrix covers annual availability and explicit use-case policy; it is not a physical validation of all values.','Observed first/last months are archive presence, not sensor installation/operating epochs.','Source annual counts from two legacy archives are not unique row unions and are not timestamp-aligned to reconstruction.','No value is classified MISSING at annual-cell granularity.','No statistics, record extremes, trends or atlas products are quality-certified by this audit.'], 'records':records}
(R/'data/final_readiness_matrix_77x18.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with (R/'data/final_readiness_matrix_77x18.csv').open('w',newline='',encoding='utf-8') as f:
 fields=['utc_year','variable','archive_rows','nonnull_rows','null_rows','active_unapproved_proposal_operations','raw_origin_classification','quality_review_status','availability_state','availability_interpretation','raw_value_display','historical_graph','daily_statistics','monthly_statistics','annual_statistics','records_and_extremes','long_term_trends','meteorological_atlas','protection_status','observed_first_month','observed_last_month']
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for x in records:w.writerow({k:x.get(k) for k in fields if k not in ('observed_first_month','observed_last_month')} | {'observed_first_month':x['observed_nonnull_archive_period_months']['first'],'observed_last_month':x['observed_nonnull_archive_period_months']['last']})
print(json.dumps({'cells':len(records),'counts':{k:dict(v) for k,v in counts.items()},'fields':len(base['variables']),'years':len(base['years'])},indent=2))
