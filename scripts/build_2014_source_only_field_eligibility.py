#!/usr/bin/env python3
import csv,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=json.loads((R/'data/2014_target_absent_source_field_availability.json').read_text())
N=s['source_only_rows']; assert N==1071 and len(s['common_fields'])==50
result=[]
for field in s['common_fields']:
 c=s['field_counts'][field];old=int(c['old_nonnull']);wh=int(c['wh1080_nonnull']);eq=int(c['both_equal']);conf=int(c['both_conflict']);paired=eq+conf
 old_only=old-paired;wh_only=wh-paired;both_null=N-(old+wh-paired)
 assert min(old,wh,eq,conf,old_only,wh_only,both_null)>=0 and old_only+wh_only+both_null+paired==N,(field,c)
 if conf:status='REVIEW_REQUIRED_SOURCE_CONFLICT'
 elif paired==N:status='REVIEW_REQUIRED_COPY_MATCH_PROVENANCE_UNKNOWN'
 elif paired:status='REVIEW_REQUIRED_PARTIAL_OR_ASYMMETRIC_FIELD'
 elif old+wh:status='REVIEW_REQUIRED_SINGLE_COPY_ONLY'
 else:status='MISSING_IN_BOTH_COPIES'
 result.append({'field':field,'old_nonnull':old,'wh1080_nonnull':wh,'paired_nonnull':paired,'paired_equal':eq,'paired_conflict':conf,'old_only_nonnull':old_only,'wh1080_only_nonnull':wh_only,'both_null':both_null,'classification':status,'eligible_for_restoration':False,'reason':'Whole-row omission cause, historical cleaning intent, physical sensor identity and field-specific correctness are not proven by this availability/concordance snapshot.'})
assert len(result)==50
obj={'schema':'source-only-field-eligibility-v1','year_utc':2014,'source_only_rows':N,'target_absence_definition':'Exact timestamp is absent from pocasi-loucka.eu_old; reconstruction exact-time and projected-slot status are separate and must not be inferred from this matrix.','source_archives':['old_weewx','weewx_WH1080'],'evidence_source':'data/2014_target_absent_source_field_availability.json; snapshot as_of_utc='+s['as_of_utc'],'processed_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'fields':result,'summary':{'field_count':50,'source_conflict_fields':sum(x['classification']=='REVIEW_REQUIRED_SOURCE_CONFLICT' for x in result),'copy_match_provenance_unknown_fields':sum(x['classification']=='REVIEW_REQUIRED_COPY_MATCH_PROVENANCE_UNKNOWN' for x in result),'all_fields_review_required_or_missing':True,'restored_proposals':0,'estimated_proposals':0},'interpretation':'Availability and exact paired-value concordance are technical archive facts. Two copies are not independent measurements; historical removals/cleaning are acknowledged by owner and current event history cannot exclude pre-audit deletion. This is not row-level physical QC or restoration approval.','safety':{'database_access':'NONE; derived from existing READ-ONLY snapshot','writes':0,'staging':False,'application':False,'q1_2018_queried':False,'year_2021_queried':False}}
(R/'data/2014_source_only_field_eligibility.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
with (R/'reports/2026-11-14-2014-source-only-field-eligibility.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=result[0].keys());w.writeheader();w.writerows(result)
lines=['# 2014 source-only field eligibility matrix','',f"Processed UTC: {obj['processed_at_utc']}. Derived solely from the previously frozen read-only archive snapshot; no new database query was made.",'','## Scope and method','', 'The cohort has 1,071 exact timestamps present in old_weewx and WH1080 but absent from pocasi-loucka.eu_old at the same exact key. This matrix describes per-field non-NULL availability and copy equality/conflict; target exact-key, nearest-slot and reconstruction states are separate checks. For each field, paired/equal/conflicting and one-sided NULL categories are reconciled to 1,071.','', '## Summary','',f"- Numeric/common fields: 50.",'']
for x in result:
 if x['classification'] in ('REVIEW_REQUIRED_SOURCE_CONFLICT','REVIEW_REQUIRED_SINGLE_COPY_ONLY') or x['paired_nonnull']==N:
  lines.append(f"- {x['field']}: {x['classification']}; old={x['old_nonnull']}, WH1080={x['wh1080_nonnull']}, paired={x['paired_nonnull']}, equal={x['paired_equal']}, conflict={x['paired_conflict']}, old-only={x['old_only_nonnull']}, WH-only={x['wh1080_only_nonnull']}.")
conf=[x for x in result if x['paired_conflict']]
lines += ['',f"Fields with any paired-value conflict: {len(conf)}; each field's exact counts are in the CSV/JSON. Fields with full paired concordance do not establish source independence.",'', '## Eligibility','', 'No field in this cohort is approved for RESTORED or ESTIMATED based on this matrix. The owner has attested that historical merges, stuck-sensor repairs and outlier removals occurred, but exact row-level intent is unknown; current reconstruction_changes cannot exclude prior deletion. Some WH1080 outTemp values are zero-valued and have already received separate anomaly screening. Primary rain, wind, pressure and derived fields require their own semantics/provenance gates. Thus this matrix narrows field-specific review, but no source-only timestamp is emitted as a correction.', '', 'Reproduction: scripts/build_2014_source_only_field_eligibility.py. Deterministic validator: scripts/validate_2014_source_only_field_eligibility.py. Machine-readable outputs: data/2014_source_only_field_eligibility.json and reports/2026-11-14-2014-source-only-field-eligibility.csv.']
(R/'reports/2026-11-14-2014-source-only-field-eligibility.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'PASS','rows':N,'fields':len(result),'conflict_fields':len(conf),'fully_concordant_fields':sum(x['paired_nonnull']==N and x['paired_conflict']==0 for x in result),'restored':0,'estimated':0},indent=2))
