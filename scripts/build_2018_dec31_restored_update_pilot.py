#!/usr/bin/env python3
"""Build update-only RESTORED proposal for the single 2018-12-31 source row."""
import csv,hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
E=json.loads((R/'data/2018_dec31_source_restore_evidence.json').read_text())
P=R/'proposals/restored_source_only_2018_dec31_primary'
P.mkdir(parents=True,exist_ok=True)
ts=E['timestamp']; selected=E['selected_fields']
reasons={
 'outHumidity':'Original measured relative humidity; both source copies agree; percent unchanged.',
 'rain':'Original rain value; both source copies agree; METRICWX mm to METRIC cm factor 0.1 (zero remains zero).',
 'rainRate':'Original rain-rate value; both source copies agree; METRICWX-to-METRIC factor 0.1 (zero remains zero).',
 'windSpeed':'Original measured wind speed; both copies agree; supported 2014-2020 METRICWX-to-METRIC factor 3.6.',
 'windGust':'Original measured wind gust; both copies agree; supported 2014-2020 METRICWX-to-METRIC factor 3.6.',
 'windDir':'Original measured direction in degrees; both copies agree; unchanged by unit conversion.',
 'barometer':'Original barometer channel; both copies agree; same stored hPa value as adjacent reconstruction rows.'}
corrections=[]
for var,x in selected.items():
 corrections.append({'operation':'update','timestamp':ts,'variable':var,'new_value':x['proposed_target_value'],'expected_old_value':None,'source_database':'old_weewx','source_time':ts,'source_value':x['source_value'],'reason':reasons[var]})
(P/'corrections.json').write_text(json.dumps(corrections,ensure_ascii=False,indent=2)+'\n')
with (P/'corrections.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(corrections[0]));w.writeheader();w.writerows(corrections)
batch={'batch_id':'restored-source-only-20181231T230000Z-primary-update-v1','classification':'RESTORED','max_batch_size':50,'corrections':corrections,'execution':'NOT_RUN','database_writes':0}
(P/'weather_mcp_batches.json').write_text(json.dumps([batch],ensure_ascii=False,indent=2)+'\n')
source_meta={'classification':'RESTORED','confidence':'MODERATE','target_timestamp':ts,'target_timestamp_utc':E['timestamp_utc'],'source_archives':['old_weewx','weewx_WH1080'],'source_role':'historical source copies with matching per-field payload; owner confirms archive merging and cleaning but exact origins are unknown','source_copy_relation':'matching copies are provenance/integrity evidence, not independent measurements','source_units':17,'target_units':16,'source_interval_minutes':5,'target_interval_minutes':5,'selected_fields':selected,'unit_contract':E['unit_contract'],'target_expected_old_state':{v:None for v in selected},'existing_outTemp_event':E['existing_change_history'][0],'row_state':'target row already exists from an earlier applied outTemp restoration; this proposal only updates seven NULL variables','provenance_limit':E['provenance_limit']}
(P/'source_metadata.json').write_text(json.dumps(source_meta,ensure_ascii=False,indent=2)+'\n')
shutil.copyfile(R/'data/2018_dec31_source_restore_evidence.json',P/'evidence_snapshot.json')
review=[]
for f in E['copy_identical_fields']+E['copy_conflict_fields']:
 if f in selected or f=='outTemp':continue
 if f in ('dewpoint','heatindex','windchill'):reason='Derived quantity; excluded from database reconstruction proposal.'
 elif f in ('pressure','altimeter'):reason='Pressure/altimeter conversion epoch and transformation contract remain unresolved.'
 elif f=='windGustDir':reason='Source value is concordant, but neighboring reconstruction rows are NULL for this field; target field coverage is not established.'
 elif f in ('inTemp','inHumidity','extraTemp1','extraTemp2','extraTemp3','extraTemp4','extraHumid1','extraHumid2'):reason='Secondary sensor channel; hardware/epoch lineage or target coverage is not established.'
 elif f in E['copy_conflict_fields']:reason='Source copies conflict in value or NULL status; keep REVIEW_REQUIRED.'
 else:reason='Not part of conservative primary-field pilot; field-specific provenance or target coverage is insufficient.'
 review.append({'variable':f,'classification':'REVIEW_REQUIRED','reason':reason})
# Include any common-field not encountered due list union deduplication.
for f in E['copy_identical_fields']+E['copy_conflict_fields']:
 if f not in selected and f!='outTemp' and all(x['variable']!=f for x in review):review.append({'variable':f,'classification':'REVIEW_REQUIRED','reason':'Not selected in the conservative pilot; per-variable target/source eligibility has not been established.'})
(P/'review_required.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
with (P/'excluded_cases.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['variable','classification','reason']);w.writeheader()
 w.writerow({'variable':'outTemp','classification':'ALREADY_RESTORED','reason':'Existing applied reconstruction_changes event 119668 restores source value -1.26666666666667; not duplicated.'})
 w.writerows(review)
validation={'classification':'RESTORED','source_checks':{'exact_timestamp_match':True,'old_weewx_wh1080_selected_field_values_equal':True,'source_usUnits':17,'source_interval_minutes':5,'source_fields_nonnull':True,'change_history_for_selected_fields':'no events; one prior applied outTemp event only'},'target_checks':{'row_exists':True,'target_usUnits':16,'target_interval_minutes':5,'numeric_fields':77,'nonnull_before':1,'nonnull_before_field':'outTemp','all_seven_expected_old_values_null':True},'physical_and_context_checks':{'outTemp':'already restored and adjacent source/target values are plausible','outHumidity':'58%; source copies and neighboring measurements consistent','rain_and_rainRate':'both zero and neighboring rows zero','windSpeed':'0.66666998119205 m/s ×3.6; matches original unit contract and surrounding pattern','windGust':'1.4000069605033 m/s ×3.6; plausible and matches the source epoch factor','windDir':'22.5°; neighboring target values stable','barometer':'1005.5201172259 hPa; adjacent target values agree with source archive'},'uncertainty':'MODERATE provenance confidence. Two matching source copies are not independent; owner does not know exact archive origins or merge rule. No regional reference was used. No predictive interval applies to restored measurements.','limitations':['No assumption that missing merged row was deliberately deleted.','Only seven primary fields are proposed; other fields remain review-required.','Existing outTemp event must remain applied for this update-only batch dependency.','This proposal is not approval or a database write.']}
(P/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
dep={'dependencies':['Existing target row at 1546297200; outTemp event 119668 is already applied.','Current expected value for each proposed target field remains NULL.','Field-specific unit mapping: METRICWX 17 to METRIC 16.'],'operations':corrections,'insert_dependency_order':'none; target row already exists','batch_id':batch['batch_id'],'duplicate_policy':'one update per (timestamp, variable); outTemp already applied and omitted','must_not_run_if':'target row is absent, any target field is non-NULL, event 119668 is rolled back, or source/unit snapshot changes'}
(P/'dependency_metadata.json').write_text(json.dumps(dep,ensure_ascii=False,indent=2)+'\n')
sim={'mode':'offline_in_memory_only','database_access':'none','database_writes':0,'staging':False,'existing_target_row':True,'numeric_field_count':77,'nonnull_before':1,'existing_outTemp_value':-1.26666666666667,'proposed_updates':len(corrections),'simulated_updated_fields':[x['variable'] for x in corrections],'nonnull_after':1+len(corrections),'insert_operations':0,'estimates':0,'status':'PASS'}
(P/'simulation.json').write_text(json.dumps(sim,ensure_ascii=False,indent=2)+'\n')
readme=f'''# RESTORED update pilot — 2018-12-31 23:00 UTC\n\nThis package proposes seven field-level updates to an existing row. It does **not** insert a row, stage a batch, or write to any database. The timestamp's outTemp was already restored in applied audit event 119668; this package excludes it to prevent a duplicate.\n\nThe two historical source copies agree on all seven proposed measured values, with usUnits=17 and interval=5. The existing target row is usUnits=16/interval=5, contains only outTemp among 77 numeric fields, and has NULL in each proposed field. Adjacent target rows are locally continuous after the supported field-specific unit conversions. The 50-field source snapshot has 22 other copy conflicts; those and derived/secondary/ambiguous fields remain REVIEW_REQUIRED.\n\n**Confidence: MODERATE.** The matching copies may share lineage, and the owner cannot identify exact source DB origins or merge rules. Missing from merged archives does not prove deliberate removal. A prior audited outTemp restoration supports the row's temperature provenance but is not treated as independent sensor evidence.\n\n## Contents and validation\n\n- `corrections.json` / `.csv`: seven update operations, expected old value NULL.\n- `weather_mcp_batches.json`: one batch of seven (maximum allowed 50); execution NOT_RUN.\n- `evidence_snapshot.json`, source/validation/dependency metadata, offline simulation, exclusions and review-required variables.\n- Run `python3 validate.py` from this directory.\n\nRow completeness after hypothetical approval would be 8/77 numeric values (one existing outTemp plus seven proposals); this is not a whole-row completion. No rain or other values are filled beyond these measured source values. No derived values are proposed.\n'''
(P/'README.md').write_text(readme)
# Package-local deterministic validator; no database access.
validator='''#!/usr/bin/env python3
import csv,hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
P=Path(__file__).resolve().parent
E=json.loads((P/'evidence_snapshot.json').read_text())
C=json.loads((P/'corrections.json').read_text())
M=json.loads((P/'manifest.json').read_text())
assert E['timestamp']==1546297200 and E['timestamp_utc']=='2018-12-31T23:00:00Z'
assert 2018 != 2021 and not E['timestamp_utc'].startswith('2018-01')
assert E['source_rows']['old_weewx']['usUnits']==17 and E['source_rows']['weewx_WH1080']['usUnits']==17
assert E['source_rows']['old_weewx']['interval']==5 and E['source_rows']['weewx_WH1080']['interval']==5
assert E['archive_presence']['loucka_reconstruction'] is True
assert E['archive_presence']['pocasi_loucka_eu_old'] is False and E['archive_presence']['pocasi_loucka_eu'] is False and E['archive_presence']['pocasi_loucka_eu_GW1000'] is False
assert E['target_row']['numeric_field_count']==77 and E['target_row']['nonnull_fields']==['outTemp']
assert len(E['existing_change_history'])==1 and E['existing_change_history'][0]['id']==119668 and E['existing_change_history'][0]['variable']=='outTemp'
assert E['copy_conflict_fields'] and len(E['copy_conflict_fields'])==22
assert len(C)==7 and len({(x['timestamp'],x['variable']) for x in C})==7
review=json.loads((P/'review_required.json').read_text())
assert len(review)==42 and len({x['variable'] for x in review})==42
assert not ({x['variable'] for x in C} & {x['variable'] for x in review})
assert M['classification_counts']=={'RESTORED':7,'ESTIMATED':0,'REVIEW_REQUIRED':42,'MISSING':0,'ALREADY_RESTORED':1}
assert all(x['operation']=='update' and x['expected_old_value'] is None for x in C)
assert all(x['timestamp']==E['timestamp'] and x['source_time']==E['timestamp'] and x['source_database']=='old_weewx' for x in C)
assert all(E['source_rows']['old_weewx'][x['variable']]==E['source_rows']['weewx_WH1080'][x['variable']]==x['source_value'] for x in C)
for x in C:
 var=x['variable'];meta=E['selected_fields'][var]
 assert math.isclose(x['new_value'],meta['proposed_target_value'],rel_tol=0,abs_tol=1e-12)
 assert E['target_row']['values'][var] is None
assert {x['variable'] for x in C}==set(E['selected_fields'])
# Validate matching transformations against adjacent source and local target rows.
source={r['dateTime']:r for r in E['source_neighbors']['old_weewx']}
target={r['dateTime']:r for r in E['target_neighbors']}
for x in C:
 factor=E['unit_contract']['factors'][x['variable']]
 for ts in (E['timestamp']-900,E['timestamp']-600,E['timestamp']-300,E['timestamp']+300,E['timestamp']+600,E['timestamp']+900):
  assert ts in source and ts in target
  sv=source[ts][x['variable']];tv=target[ts][x['variable']]
  assert sv is not None and tv is not None
  assert math.isclose(float(sv)*factor,float(tv),rel_tol=0,abs_tol=1e-8),(x['variable'],ts,sv,tv,factor)
B=json.loads((P/'weather_mcp_batches.json').read_text());assert len(B)==1 and len(B[0]['corrections'])==7 and len(B[0]['corrections'])<=50 and B[0]['execution']=='NOT_RUN'
assert not any(x['operation']=='insert' for x in C)
S=json.loads((P/'simulation.json').read_text());assert S['database_access']=='none' and S['database_writes']==0 and S['staging'] is False and S['nonnull_before']==1 and S['nonnull_after']==8 and S['insert_operations']==0
with (P/'corrections.csv').open() as f: assert sum(1 for _ in csv.DictReader(f))==7
with (P/'excluded_cases.csv').open() as f: assert any(x['variable']=='outTemp' and x['classification']=='ALREADY_RESTORED' for x in csv.DictReader(f))
for item in M['artifacts'].values():
 b=(P/item['path']).read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],item['path']
print('PASS: seven RESTORED updates, provenance, unit conversions, neighbors, no duplicate insert, offline simulation, and package artifact hashes.')
'''
(P/'validate.py').write_text(validator)
# Manifest last, hashes every package file other than manifest itself.
arts={}
for q in sorted(P.iterdir()):
 if q.is_file() and q.name!='manifest.json':
  b=q.read_bytes();arts[q.name]={'path':q.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
manifest={'package':'restored_source_only_2018_dec31_primary','scope':'one existing 2018-12-31 23:00 UTC target row; seven measured-variable updates only','classification_counts':{'RESTORED':7,'ESTIMATED':0,'REVIEW_REQUIRED':42,'MISSING':0,'ALREADY_RESTORED':1},'review_scope':'50 common source fields; one variable already restored; 42 remain withheld/review-required','operations':{'updates':7,'inserts':0,'maximum_batch_size':50,'batches':1},'current_row_completeness':{'numeric_fields':77,'nonnull':1,'existing_nonnull_field':'outTemp'},'hypothetical_after_approval':{'numeric_fields':77,'nonnull':8,'remaining_fields_null_or_unreviewed':69},'database_access':'READ_ONLY_SELECT_ONLY','writes_or_staging':False,'publication':False,'protected_2018_q1':'excluded; this is Q4 2018','protected_2021':'not queried','confidence':'MODERATE','prior_applied_event_excluded':119668,'validator':'python3 validate.py','artifacts':arts}
(P/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('built',P)
