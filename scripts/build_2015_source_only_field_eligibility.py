#!/usr/bin/env python3
"""Build a field-scoped eligibility matrix from the existing 2015 source-only snapshots."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
cohort=json.loads((R/'data/2015_source_only_cohort.json').read_text())
rows=list(csv.DictReader((R/'data/2015_source_only_row_dispositions.csv').open()))
outtemp=list(csv.DictReader((R/'data/2015_source_only_outtemp_field_disposition.csv').open()))
assert cohort['counts']['source_only_rows']==2147 and len(rows)==len(outtemp)==2147
A=cohort['primary_field_availability']; N=2147
exact={}
for f in ['rain','rainRate','windSpeed','altimeter']:
 w,o='wh_'+f,'old_'+f
 paired=[r for r in rows if r[w]!='' and r[o]!='']
 exact[f]={'paired_nonnull':len(paired),'equal':sum(float(r[w])==float(r[o]) for r in paired),'conflict':sum(float(r[w])!=float(r[o]) for r in paired)}
assert exact['rain']=={'paired_nonnull':2145,'equal':2145,'conflict':0}
assert exact['rainRate']=={'paired_nonnull':2147,'equal':2147,'conflict':0}
assert exact['altimeter']=={'paired_nonnull':2147,'equal':0,'conflict':2147}
assert exact['windSpeed']=={'paired_nonnull':1,'equal':1,'conflict':0}
q={}
for r in outtemp:q[r['field_quality_disposition']]=q.get(r['field_quality_disposition'],0)+1
assert q=={'SOURCE_SENSOR_STUCK_SUSPECTED':997,'SOURCE_ZERO_REGIONAL_CONFLICT_REVIEW':28,'SOURCE_ZERO_UNRESOLVED':1122}
fields=[]
def add(field,old_n,wh_n,paired=None,classification='UNRESOLVED_SOURCE_ONLY',limitation=''):
 fields.append({'field':field,'old_weewx_nonnull':old_n,'weewx_WH1080_nonnull':wh_n,'paired_nonnull':paired['paired_nonnull'] if paired else None,'paired_equal':paired['equal'] if paired else None,'paired_conflict':paired['conflict'] if paired else None,'eligibility':classification,'limitation':limitation})
add('outTemp',A['outTemp']['old_weewx_nonnull'],A['outTemp']['weewx_WH1080_nonnull'],classification='REVIEW_REQUIRED_FIELD_CONFLICT',limitation='WH1080 is zero at every target; old_weewx is NULL. 997 exact-zero neighbor plateaus, 28 regional disagreement-only cases, 1,122 unresolved; no restoration.')
add('outHumidity',0,0,classification='MISSING_IN_BOTH_SOURCE_COPIES',limitation='No source value to restore.')
add('rain',2145,2147,exact['rain'],classification='REVIEW_REQUIRED_RAIN_SEMANTICS',limitation='2,145 paired values agree; two WH1080-only zero values. E4 gauge/counter/driver semantics unresolved; no source-only row insertion.')
add('rainRate',2147,2147,exact['rainRate'],classification='REVIEW_REQUIRED_RAIN_SEMANTICS',limitation='All paired values agree, but interval/driver semantics and omission cause are unresolved; no insertion.')
add('windSpeed',1,2147,exact['windSpeed'],classification='REVIEW_REQUIRED_TRANSFORMATION_AND_LINEAGE',limitation='Only one paired value; owner attests historical wind recalculation. No row-level transform/epoch proof for this cohort.')
add('windGust',5,2147,classification='REVIEW_REQUIRED_TRANSFORMATION_AND_LINEAGE',limitation='Only five old-source values; current row snapshot does not establish paired value concordance. Historical wind recalculation is owner-attested.')
add('windDir',1,2147,classification='REVIEW_REQUIRED_TRANSFORMATION_AND_LINEAGE',limitation='Only one old-source value; no adequate paired row-level evidence.')
add('barometer',0,2147,classification='REVIEW_REQUIRED_SOURCE_ONLY',limitation='WH1080-only availability; no independent copy or target row; restoration/removal cause unknown.')
add('pressure',2147,2147,{'paired_nonnull':2147,'equal':A['pressure']['equal_both_nonnull'],'conflict':0},classification='REVIEW_REQUIRED_SOURCE_ONLY',limitation='Exact cross-copy equality for all 2,147 rows, but the copies are not independent measurement lineages and intentional historical removal cannot be excluded.')
add('altimeter',2147,2147,exact['altimeter'],classification='REVIEW_REQUIRED_SOURCE_CONFLICT',limitation='All 2,147 paired values conflict; do not infer which copy is correct.')
obj={'schema':'source-only-field-eligibility-v1','created_from':'Existing read-only 2015 source-only snapshots; no new DB query','year_utc':2015,'source_only_timestamp_count':N,'definition':'Exact timestamp exists in old_weewx and weewx_WH1080, absent from pocasi-loucka.eu_old and reconstruction.','archives':['old_weewx','weewx_WH1080','pocasi-loucka.eu_old','loucka_reconstruction'],'evidence_class':'TECHNICALLY_OBSERVED_SNAPSHOT_DERIVATION','owner_lineage':'OWNER_ATTESTED historical merges, repairs, outlier removal and wind recalculation; exact chronology/rules unknown.','fields':fields,'outTemp_disposition_counts':q,'decision':'No new RESTORED or ESTIMATED operation. These records are source-only; even exact copy agreement does not establish original lineage, historical retention intent, or target meteorological correctness.','safety':{'database_access':'NONE','writes':0,'staging':False,'application':False,'q1_2018_queried':False,'year_2021_queried':False}}
(R/'data/2015_source_only_field_eligibility.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-2015-source-only-field-eligibility.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields[0].keys());w.writeheader();w.writerows(fields)
lines=['# 2015 source-only field eligibility','',f'**Scope:** {N:,} exact timestamps present in `old_weewx` and `weewx_WH1080`, absent from `pocasi-loucka.eu_old` and `loucka_reconstruction`. This review derives only from already stored read-only snapshots; no new database query was run.','', '## Field decisions','']
for x in fields:
 lines += [f"### `{x['field']}` — {x['eligibility']}",'',f"- Non-NULL counts: old_weewx {x['old_weewx_nonnull']:,}; WH1080 {x['weewx_WH1080_nonnull']:,}."]
 if x['paired_nonnull'] is not None: lines += [f"- Paired values: {x['paired_nonnull']:,}; equal {x['paired_equal']:,}; conflict {x['paired_conflict']:,}."]
 lines += [f"- Gate: {x['limitation']}",'']
lines += ['## OutTemp triage','',f"The 2,147 WH1080 values are zero and the old_weewx field is NULL. Existing row-level evidence classifies {q['SOURCE_SENSOR_STUCK_SUSPECTED']:,} as stuck-sensor suspected, {q['SOURCE_ZERO_REGIONAL_CONFLICT_REVIEW']:,} as regional-context review, and {q['SOURCE_ZERO_UNRESOLVED']:,} as unresolved. These are review labels, not proof of deletion or sensor failure.",'','## Decision and limits','','No new correction proposal is eligible. Rain fields remain within the E4 semantics block; wind fields remain subject to owner-attested historical recalculation with no cohort-specific transform evidence; pressure copy agreement does not establish independent lineage or retention intent. Source-only absence may reflect prior removal.','', 'Machine-readable details: `data/2015_source_only_field_eligibility.json` and the CSV beside this report. Validation: `scripts/validate_2015_source_only_field_eligibility.py`.']
(R/'reports/2026-11-14-2015-source-only-field-eligibility.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'PASS','rows':N,'fields':len(fields),'no_proposals':True,'outTemp':q},indent=2))
