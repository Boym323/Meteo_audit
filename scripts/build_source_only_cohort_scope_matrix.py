#!/usr/bin/env python3
"""Catalog source-only evidence cohorts without conflating target-archive definitions."""
import json
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1]
annual=json.loads((R/'data/source_only_2009_2020_cross_archive_summary.json').read_text())
annual_counts={str(x['utc_year']):int(x['timestamp_count']) for x in annual['availability_by_year']}
items=[]
def add(year,rows,target,scope,kind,fields=0,notes=''):
 items.append({'year':year,'period':scope,'source_only_rows':rows,'target_archive_definition':target,'scope_kind':kind,'fields_partitioned':fields,'notes':notes})
# Exact recon-target scopes with complete field matrices.
for y,n in [(2009,3811),(2010,1989),(2011,5016),(2012,8424),(2013,2025)]:add(y,n,'loucka_reconstruction.archive','full UTC year', 'RECONSTRUCTION_TARGET_FIELD_MATRIX',50,'Exact timestamp shared by old_weewx and WH1080 and absent from reconstruction; derived/query-aggregated evidence. Q1 2018 protection does not apply.')
add(2014,1071,'pocasi-loucka.eu_old.archive','full UTC year','EU_OLD_TARGET_FIELD_MATRIX',50,'Exact source key absent from eu_old. Reconstruction exact-key and projected-slot states were explicitly not inferred. Separate from the 11,698 reconstruction-target source-only annual total.')
add(2015,2147,'pocasi-loucka.eu_old.archive AND loucka_reconstruction.archive','full UTC year','DUAL_TARGET_FIELD_MATRIX',10,'Exact source key absent from both targets; subset of the 48,778 reconstruction-target 2015 cohort.')
add(2016,16330,'pocasi-loucka.eu_old.archive','full UTC year','EU_OLD_TARGET_FIELD_MATRIX',50,'Not equivalent to the 75,547 reconstruction-target 2016 cohort.')
add(2017,28015,'pocasi-loucka.eu_old.archive','full UTC year','EU_OLD_TARGET_FIELD_MATRIX',50,'Not equivalent to the 39,082 reconstruction-target 2017 cohort.')
add(2018,422,'loucka_reconstruction.archive','2018-04-01 through 2019-01-01 UTC only','RECONSTRUCTION_TARGET_FIELD_MATRIX_PARTIAL_YEAR',50,'Q1 2018 deliberately excluded. Contains 421 interval-5 off-grid keys and one interval-6 row. All 421 interval-5 keys have occupied nearest projected targets.')
add(2019,814,'loucka_reconstruction.archive','full UTC year','RECONSTRUCTION_TARGET_FIELD_MATRIX',50,'Exact timestamp shared by old_weewx and WH1080 and absent from reconstruction.')
add(2020,1466,'loucka_reconstruction.archive','full UTC year','RECONSTRUCTION_TARGET_FIELD_MATRIX',50,'Exact timestamp shared by old_weewx and WH1080 and absent from reconstruction.')
# Existing bounded overlap—not an additional cohort count.
strict=json.loads((R/'data/source_only_outtemp_2016_2017_exact_grid_screen.json').read_text())
overlap={'period':'2016-2017 exact-grid strict source-only subset','rows':30271,'target_archive':'loucka_reconstruction.archive','scope_kind':'OVERLAPPING_LIMITED_QUALITY_SCREEN','fields_reviewed':['outTemp','outHumidity','rain','rainRate','windSpeed'],'notes':'Subset of reconstruction-target annual cohorts; overlaps annual matrices and must not be added to their totals. Not a 50-field matrix.'}
full_rows=sum(x['source_only_rows'] for x in items if x['scope_kind'].startswith('RECONSTRUCTION_TARGET') or x['scope_kind']=='DUAL_TARGET_FIELD_MATRIX')
out={'schema':'source-only-cohort-scope-matrix-v1','recorded_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'authoritative_global_cohort':{'rows':annual['unique_timestamps'],'definition':annual['source_only_scope'],'yearly_counts':annual_counts},'field_matrix_scopes':items,'overlapping_limited_scopes':[overlap],'reconstruction_target_field_matrix_records_represented':full_rows,'coverage_warning':'This is not complete coverage of the 207,182-record global cohort. The 2014/2016/2017 full-year matrices target pocasi-loucka.eu_old, 2018 is partial, and the 2016-2017 strict screen overlaps the annual cohorts. Do not add scopes with different targets or overlapping periods.','safety':{'database_writes':0,'staging':False,'application':False,'q1_2018_in_new_scope':False,'year_2021_included':False}}
(R/'data/source_only_cohort_scope_matrix.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
lines=['# Mapa rozsahů source-only kohort','',f"Globální autoritativní kohorta: **{annual['unique_timestamps']:,}** přesných timestampů v letech 2009–2020, definovaných jako přítomné v old_weewx a WH1080 a chybějící v `loucka_reconstruction.archive`.",'','## Existující field-level matice','', '| Rok/období | Řádky | Cílový archiv definice | Pole | Interpretace rozsahu |','|---|---:|---|---:|---|']
for x in items:lines.append(f"| {x['period']} {x['year']} | {x['source_only_rows']:,} | `{x['target_archive_definition']}` | {x['fields_partitioned']} | {x['scope_kind']}: {x['notes']} |")
lines+=['','## Překryvy a omezení','',f"Reconstruction-target full-year/partial scopes v této matici představují {full_rows:,} záznamů napříč vybranými kohortami; nejde o dokončený ani kompletní audit 207,182 záznamů. Roční matice 2014, 2016 a 2017 cílí na `pocasi-loucka.eu_old`, a proto nejsou zaměnitelné s rekonstrukčně source-only ročními počty. 2015 dual-target subset je uvnitř globálního ročního počtu. 2018 zahrnuje jen Q2–Q4; chráněný Q1 nebyl znovu dotazován.",'',"Strict aligned screen 2016–2017 s 30,271 řádky je podmnožinou reconstruction-target ročních kohort a pokrývá jen pět polí. Nesmí se přičíst k ročním maticím.",'','Absence přesného zdrojového timestampu neznamená absenci nejbližšího projektovaného cílového řádku. Dostupnost a shoda archivních kopií neprokazují identitu nezávislých senzorů, kvalitu měření ani příčinu historického vynechání. Žádná korekce z této scope matice nevyplývá.','', 'Machine-readable: `data/source_only_cohort_scope_matrix.json`; validator: `scripts/validate_source_only_cohort_scope_matrix.py`.']
(R/'reports/2026-11-14-source-only-cohort-scope-matrix.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'global_records':annual['unique_timestamps'],'scopes':len(items),'reconstruction_target_matrix_records':full_rows,'status':'BUILT'},indent=2))
