#!/usr/bin/env python3
import csv,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
allrows=[];summaries={}
for year in [2016,2017]:
 src=json.loads((R/f'data/{year}_target_absent_source_field_availability.json').read_text());n=src['source_only_rows'];fields=[]
 assert n in (16330,28015) and len(src['common_fields'])==50
 for field in src['common_fields']:
  c=src['field_counts'][field];old=int(c['old_nonnull']);wh=int(c['wh1080_nonnull']);eq=int(c['both_equal']);conf=int(c['both_conflict']);paired=eq+conf
  old_only=old-paired;wh_only=wh-paired;both_null=n-(old+wh-paired)
  assert min(old,wh,eq,conf,old_only,wh_only,both_null)>=0 and old_only+wh_only+both_null+paired==n,(year,field,c)
  if conf:cls='REVIEW_REQUIRED_SOURCE_CONFLICT'
  elif paired==n:cls='REVIEW_REQUIRED_COPY_MATCH_PROVENANCE_UNKNOWN'
  elif paired:cls='REVIEW_REQUIRED_PARTIAL_OR_ASYMMETRIC_FIELD'
  elif old+wh:cls='REVIEW_REQUIRED_SINGLE_COPY_ONLY'
  else:cls='MISSING_IN_BOTH_COPIES'
  row={'year_utc':year,'field':field,'source_only_timestamps':n,'old_nonnull':old,'wh1080_nonnull':wh,'paired_nonnull':paired,'paired_equal':eq,'paired_conflict':conf,'old_only_nonnull':old_only,'wh1080_only_nonnull':wh_only,'both_null':both_null,'classification':cls,'eligible_for_restoration':False,'reason':'Exact copy agreement does not authenticate independent source lineage or exclude historical removal; field-level correctness and applicable transforms remain separately gated.'}
  fields.append(row);allrows.append(row)
 obj={'schema':'source-only-field-eligibility-v1','year_utc':year,'source_only_timestamps':n,'cohort_definition':src['scope'],'source_archives':['old_weewx','weewx_WH1080'],'target_archive':'pocasi-loucka.eu_old','source_snapshot_as_of_utc':src['as_of_utc'],'processed_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'fields':fields,'summary':{'field_count':50,'conflict_fields':sum(x['paired_conflict']>0 for x in fields),'fully_paired_and_equal_fields':sum(x['paired_nonnull']==n and x['paired_conflict']==0 for x in fields),'all_fields_restoration_eligible':False,'restored':0,'estimated':0},'interpretation':'All field partitions reconcile to the source-only row count. This is archive availability/concordance, not per-row physical QC or proof of historical retention intent.','safety':{'database_access':'NONE; derived from frozen READ_ONLY snapshot','writes':0,'staging':False,'application':False,'q1_2018_queried':False,'year_2021_queried':False}}
 (R/f'data/{year}_source_only_field_eligibility.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 summaries[str(year)]=obj['summary']
with (R/'reports/2026-11-14-2016-2017-source-only-field-eligibility.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=allrows[0].keys());w.writeheader();w.writerows(allrows)
lines=['# 2016–2017 source-only field eligibility matrices','', 'Processed from the already frozen annual source-only field snapshots; no new database query was run.','', '## Scope','']
for year in [2016,2017]:
 o=json.loads((R/f'data/{year}_source_only_field_eligibility.json').read_text());s=o['summary'];lines.append(f"- {year}: {o['source_only_timestamps']:,} exact source-copy timestamps absent from pocasi-loucka.eu_old; {s['field_count']} fields; {s['conflict_fields']} fields have paired value conflicts; {s['fully_paired_and_equal_fields']} fields are non-NULL and equal in both copies for every timestamp.")
lines += ['', '## Field-level interpretation','', 'Every field partition (both copies NULL, one-sided non-NULL, paired equal, paired conflict) reconciles to its year-specific row denominator. Fields with complete copy agreement remain REVIEW_REQUIRED because the archives are duplicate historical sources, owner-attested cleaning/merges may predate current change history, and no independent sensor truth is established. Asymmetric fields and conflicts are explicitly separated. An all-NULL field is MISSING_IN_BOTH_COPIES, not a repair candidate.','', 'No RESTORED or ESTIMATED proposal is generated from these matrices. A field may need additional timestamp, unit, physical plausibility, neighbor and historical removal review before candidate-level eligibility. Q1 2018 and 2021 are outside these year scopes.','', 'Machine-readable files: data/2016_source_only_field_eligibility.json, data/2017_source_only_field_eligibility.json; combined table: reports/2026-11-14-2016-2017-source-only-field-eligibility.csv; validator: scripts/validate_2016_2017_source_only_field_eligibility.py.']
(R/'reports/2026-11-14-2016-2017-source-only-field-eligibility.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'PASS','years':summaries,'field_rows':len(allrows)},indent=2))
