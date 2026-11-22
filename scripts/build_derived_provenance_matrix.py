#!/usr/bin/env python3
"""Build per-field historical-vs-current-standard evidence matrix (never asserts historic use)."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=list(csv.DictReader((R/'reports/2026-11-13-derived-variable-schema-map.csv').open()))
standard={
 'dewpoint':('StdWXCalculate / StdWXXTypes','outTemp; outHumidity','Current WeeWX documented formula family; units follow usUnits.'),
 'inDewpoint':('StdWXCalculate / StdWXXTypes','inTemp; inHumidity','Current WeeWX documented indoor dewpoint calculation.'),
 'windchill':('StdWXCalculate / StdWXXTypes','outTemp; windSpeed; usUnits','Current code selects a unit-system-specific formula.'),
 'heatindex':('StdWXCalculate / StdWXXTypes','outTemp; outHumidity; usUnits; configurable algorithm','Current docs allow new/old algorithm selection.'),
 'appTemp':('StdWXCalculate / StdWXXTypes','outTemp; outHumidity; windSpeed; usUnits','Current documented calculation.'),
 'humidex':('StdWXCalculate / StdWXXTypes','outTemp; outHumidity; usUnits','Current documented calculation.'),
 'cloudbase':('StdWXCalculate / StdWXXTypes','outTemp; outHumidity; station altitude; usUnits','Current documented calculation.'),
 'altimeter':('StdWXCalculate / PressureCooker','barometer/gauge pressure; station altitude; configured algorithm','Current docs identify multiple possible altimeter algorithms.'),
 'windrun':('StdWXCalculate / StdWXXTypes','windSpeed; interval; usUnits','Current code has unit-specific windrun calculation.'),
 'ET':('StdWXCalculate / ETXType','outTemp; outHumidity; radiation; windSpeed; interval; time window; station metadata/options','Windowed; current defaults include a 3600 s period and tunable constants.'),
 'maxSolarRad':('StdWXCalculate / StdWXXTypes','dateTime; station latitude/longitude/altitude; configured algorithm/options','Theoretical maximum radiation; current docs offer Bras or Ryan–Stolzenbach options.')
}
empirical={
 'inDewpoint':'433,955 non-2021 values within 0.1 C of a Magnus screening formula from current inTemp/inHumidity; strong numerical consistency, not producer proof.',
 'dewpoint':'Present after many RH edits/clears; persistence is a stale-dependency indicator only, not formula verification.',
 'heatindex':'Presence checked in RH cascade inventory; historical source/calculation and refresh state unresolved.',
 'humidex':'Presence checked in RH cascade inventory; historical source/calculation and refresh state unresolved.',
 'cloudbase':'Presence checked in RH cascade inventory; historical source/calculation and refresh state unresolved.',
 'appTemp':'Presence checked in RH cascade inventory; historical source/calculation and refresh state unresolved.',
 'vpd':'Availability and RH-cascade presence audited; no historical formula/producer established.',
 'wbgt':'Availability and RH-cascade presence audited; no historical formula/producer established.',
 'outHumAbs':'Availability and RH-cascade presence audited; no historical formula/producer established.',
 'outThetaE':'Availability and RH-cascade presence audited; no historical formula/producer established.'
}
rows=[]
for r in source:
 v=r['variable']; calc,inputs,detail=standard.get(v,('Not in current StdWXCalculate default list; custom XType/hardware/import possible','Unknown from local evidence','No stable current-core formula/producer contract inferred.'))
 rows.append({
  'variable':v,'archive_schema_count':r['archive_schema_count'],'archive_schemas':r['archive_schemas'],
  'current_documented_producer_class':calc,'current_documented_candidate_inputs':inputs,
  'current_documentation_note':detail,'local_empirical_evidence':empirical.get(v,'No field-specific formula evidence beyond schema/availability/cascade inventory.'),
  'historical_loucka_formula': 'UNVERIFIED','historical_producer_version_config_epoch':'UNVERIFIED',
  'hardware_vs_software_preference':'UNVERIFIED','refresh_semantics':'UNVERIFIED',
  'recalculation_disposition':'DO_NOT_RECALCULATE_WITHOUT_EPOCH_FORMULA_AND_INPUT_QUALITY_APPROVAL'
 })
if len(rows)!=21 or len({r['variable'] for r in rows})!=21: raise ValueError('Expected one row per each of 21 mapped variables')
jsonout={'schema':'derived-variable-historical-provenance-v1','as_of_utc':'2026-11-13','source_schema_map':'reports/2026-11-13-derived-variable-schema-map.csv','official_current_reference':'https://weewx.com/docs/5.2/reference/weewx-options/stdwxcalculate/','historical_claim':'None: current documentation and numerical consistency do not establish historical Loucka producer/configuration.','rows':rows}
(R/'data/derived_variable_historical_provenance_matrix.json').write_text(json.dumps(jsonout,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-13-derived-variable-historical-provenance-matrix.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps({'fields':len(rows),'current_standard_fields':sum(r['current_documented_producer_class'].startswith('StdWXCalculate') for r in rows),'custom_or_unknown':sum(not r['current_documented_producer_class'].startswith('StdWXCalculate') for r in rows),'historical_producer_unverified':sum(r['historical_producer_version_config_epoch']=='UNVERIFIED' for r in rows)},indent=2))
