#!/usr/bin/env python3
import csv,json
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];allrows=[]
for year in (2019,2020):
 src=json.loads((R/f'data/{year}_source_only_field_month.json').read_text());n=src['source_only_rows'];months=src['monthly'];fields=sorted(months[0]['fields'])
 assert n in (814,1466) and len(fields)==50
 assert sum(m['source_only_rows'] for m in months)==n
 result=[]
 for field in fields:
  old=sum(int(m['fields'][field]['old_nonnull']) for m in months)
  wh=sum(int(m['fields'][field]['wh_nonnull']) for m in months)
  eq=sum(int(m['fields'][field]['both_equal']) for m in months)
  conf=sum(int(m['fields'][field]['both_conflict']) for m in months)
  paired=eq+conf;old_only=old-paired;wh_only=wh-paired;both_null=n-(old+wh-paired)
  assert min(old,wh,eq,conf,old_only,wh_only,both_null)>=0 and old_only+wh_only+both_null+paired==n,(year,field)
  if conf:cls='REVIEW_REQUIRED_SOURCE_CONFLICT'
  elif paired==n:cls='REVIEW_REQUIRED_COPY_MATCH_PROVENANCE_UNKNOWN'
  elif paired:cls='REVIEW_REQUIRED_PARTIAL_OR_ASYMMETRIC_FIELD'
  elif old+wh:cls='REVIEW_REQUIRED_SINGLE_COPY_ONLY'
  else:cls='MISSING_IN_BOTH_COPIES'
  result.append({'field':field,'old_nonnull':old,'wh1080_nonnull':wh,'paired_nonnull':paired,'paired_equal':eq,'paired_conflict':conf,'old_only_nonnull':old_only,'wh1080_only_nonnull':wh_only,'both_null':both_null,'classification':cls,'eligible_for_restoration':False,'reason':'Exact source-copy equality does not prove independent lineage, correct local measurement or exclusion of historical cleaning/removal.'})
 obj={'schema':'source-only-field-eligibility-v1','year_utc':year,'source_only_timestamps':n,'cohort_definition':src['definition'],'source_archives':['old_weewx','weewx_WH1080'],'target_archive':'loucka_reconstruction.archive','source_snapshot_evidence':'data/'+f'{year}_source_only_field_month.json','processed_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'),'fields':result,'separate_alignment_evidence':{k:src.get(k) for k in ['off_grid_rows','on_grid_rows','projected_target_rows_present','projected_target_rows_absent','projected_temperature_equal','projected_temperature_conflict'] if k in src},'summary':{'field_count':50,'conflict_fields':sum(x['paired_conflict']>0 for x in result),'fully_paired_and_equal_fields':sum(x['paired_nonnull']==n and x['paired_conflict']==0 for x in result),'all_fields_restoration_eligible':False,'restored':0,'estimated':0},'interpretation':'The matrix covers exact source-only timestamps and field availability/equality only. It does not count projected-slot occupancy as exact-key restoration, prove reason for omission, or certify meteorological correctness.','safety':{'database_access':'NONE; derived from frozen READ_ONLY monthly snapshots','writes':0,'staging':False,'application':False,'q1_2018_queried':False,'year_2021_queried':False}}
 (R/f'data/{year}_source_only_field_eligibility.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 allrows.extend([{'year_utc':year,**x} for x in result])
with (R/'reports/2026-11-14-2019-2020-source-only-field-eligibility.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=allrows[0].keys());w.writeheader();w.writerows(allrows)
lines=['# 2019–2020 source-only field eligibility','', 'Derived from the existing monthly exact-source-copy snapshots; no new database query was run.','']
for y in (2019,2020):
 d=json.loads((R/f'data/{y}_source_only_field_eligibility.json').read_text());s=d['summary']
 lines.append(f"- {y}: {d['source_only_timestamps']:,} exact source-only timestamps; 50 common fields; {s['conflict_fields']} fields have one or more paired value conflicts; {s['fully_paired_and_equal_fields']} fields are fully paired and equal.")
lines+=['','## Scope and decision','', 'Every field partition reconciles to the annual source-only timestamp count: both NULL, old-only, WH1080-only, paired equal or paired conflicting. This remains a source availability/concordance matrix. Exact target absence does not mean projected target-slot absence; the separate alignment evidence is retained. In 2020, some projected target rows exist, so no insertion may be inferred from exact-key absence alone.','', 'No field is approved for RESTORED or ESTIMATED. Exact-copy equality does not prove independence, owner-attested historical cleaning intent, sensor epoch, or local physical correctness. Existing 2019 LuhaMet conflicts and 2020 endpoint context remain separate per-case gates.','', 'Machine-readable: data/2019_source_only_field_eligibility.json, data/2020_source_only_field_eligibility.json; CSV: reports/2026-11-14-2019-2020-source-only-field-eligibility.csv; validator: scripts/validate_2019_2020_source_only_field_eligibility.py.']
(R/'reports/2026-11-14-2019-2020-source-only-field-eligibility.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status':'PASS','years':{str(y):json.loads((R/f'data/{y}_source_only_field_eligibility.json').read_text())['summary'] for y in (2019,2020)},'csv_rows':len(allrows)},indent=2))
