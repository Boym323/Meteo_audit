#!/usr/bin/env python3
"""Validate short (<=1h) gap source evidence and write its reproducibility manifest."""
from __future__ import annotations
import csv,hashlib,json,re
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
gap=R/'reports/2026-11-12-gap-event-catalog.csv'
expected={}; q1=(1514764800,1522540800)
with gap.open(newline='',encoding='utf-8') as f:
 for r in csv.DictReader(f):
  y=int(r['utc_year']);l=int(r['prev_ts']);rr=int(r['target_ts']);d=int(r['delta_seconds'])
  if not 2009<=y<=2020 or r['exceeds_both_steps']!='1' or d%300 or d<=300 or d>3600:continue
  gid=f'{y}:{l}:{rr}'
  for t in range(l+300,rr,300):expected[t]=(l,rr,d,gid,'PROTECTED_Q1_2018_DIAGNOSTIC' if q1[0]<=t<q1[1] else 'NORMAL')
errors=[];sql_manifest=[];result_manifest=[]
for index_path,result_prefix,sql_dir,sql_prefix in [
 ('data/short_gap_source_detail_query_index.json','short_gap_source_detail_results_','sql/readonly/short_gap_source_detail/','short_gap_source_detail_'),
 ('data/exact_hour_source_detail_query_index.json','exact_hour_source_detail_results_','sql/readonly/exact_hour_source_detail/','exact_hour_source_detail_')]:
 idx=json.loads((R/index_path).read_text())
 for q in idx['chunks']:
  sp=R/q['sql'];rp=R/'data'/f'{result_prefix}{q["chunk"]:03d}.json'
  if not sp.is_file() or not rp.is_file():errors.append(f'missing chunk input/output {q["chunk"]} {index_path}');continue
  sqlb=sp.read_bytes();resb=rp.read_bytes();sql=sqlb.decode()
  sql_clean=re.sub(r'--[^\n]*','',sql).lower()
  if not sql_clean.lstrip().startswith('with'):errors.append(f'query not SELECT/CTE: {sp}')
  if re.search(r'\b(insert|update|delete|replace|alter|drop|truncate|create)\b',sql_clean):errors.append(f'write/DDL token: {sp}')
  if hashlib.sha256(sqlb).hexdigest()!=q['sql_sha256']:errors.append(f'SQL hash mismatch {sp}')
  data=json.loads(resb)
  if 'error_code' in data:errors.append(f'MCP error {rp}')
  result_manifest.append({'path':str(rp.relative_to(R)),'bytes':len(resb),'sha256':hashlib.sha256(resb).hexdigest(),'source_rows':len(data.get('result',[]))})
  sql_manifest.append({'path':str(sp.relative_to(R)),'bytes':len(sqlb),'sha256':hashlib.sha256(sqlb).hexdigest()})
records=json.loads((R/'data/short_gap_source_detail_per_target.json').read_text())['records']
source_rows=0; source_db=Counter(); years=Counter(); zero_targets=0; nonzero_targets=0; p3=Counter()
for x in records:
 t=int(x['timestamp'])
 if t not in expected:errors.append(f'unexpected target {t}');continue
 l,rr,d,gid,scope=expected[t]
 if (x['left_endpoint'],x['right_endpoint'],x['gap_seconds'],x['gap_id'],x['protection_scope'])!=(l,rr,d,gid,scope):errors.append(f'target context mismatch {t}')
 if t>=1609459200:errors.append(f'2021 target {t}')
 if x['target_row_state']!='MISSING_FROM_RECONSTRUCTION_AT_QUERY_TIME':errors.append(f'target state {t}')
 if x['change_event_count']!=0:errors.append(f'history event on {t}')
 if x['disposition']!='REVIEW_REQUIRED_SOURCE_VS_ESTIMATED':errors.append(f'unexpected disposition {t}')
 if x['p3_v2_disposition']:p3[x['p3_v2_disposition']]+=1
 source_temps=[]
 for db,s in x['source_archives'].items():
  source_rows+=1;source_db[db]+=1
  if db not in {'old_weewx','weewx_WH1080'}:errors.append(f'unexpected source database {db}')
  if s['usUnits']!=17 or s['interval']!=5:errors.append(f'unexpected units/cadence {t} {db}')
  if s['source_time_matches_target'] is not True:errors.append(f'nonexact source timestamp {t} {db}')
  if s['fields']['outTemp'] is not None:source_temps.append(float(s['fields']['outTemp']))
 if not x['source_archives']:errors.append(f'empty source evidence target {t}')
 if any(v==0 for v in source_temps):zero_targets+=1
 if any(v!=0 for v in source_temps):nonzero_targets+=1
 years[x['utc_year']]+=1
if len(expected)!=29931:errors.append(f'expected candidate denominator mismatch {len(expected)}')
if len(records)!=5588:errors.append(f'target count mismatch {len(records)}')
if source_rows!=11163:errors.append(f'source row count mismatch {source_rows}')
if dict(source_db)!={'old_weewx':5575,'weewx_WH1080':5588}:errors.append(f'source db counts {dict(source_db)}')
if zero_targets!=5416 or nonzero_targets!=172:errors.append(f'temperature state mismatch zero={zero_targets} nonzero={nonzero_targets}')
if p3!={'REVIEW_REQUIRED_SOURCE_VS_ESTIMATED_CONFLICT':83}:errors.append(f'P3 overlap mismatch {dict(p3)}')
if any(x['protection_scope']=='PROTECTED_Q1_2018_DIAGNOSTIC' and not 1514764800<=int(x['timestamp'])<1522540800 for x in records):errors.append('Q1 protected range mismatch')
if errors:
 print(json.dumps({'status':'FAIL','errors':errors[:100],'error_count':len(errors)},indent=2));raise SystemExit(1)
manifest={'status':'PASS','scope':'2009-2020 conditional <=1h gap interior targets; exact source rows only; Q1 2018 diagnostic','candidate_target_slots':len(expected),'source_covered_targets':len(records),'source_archive_rows':source_rows,'source_rows_by_database':dict(source_db),'targets_with_zero_outTemp':zero_targets,'targets_with_nonzero_outTemp':nonzero_targets,'p3_v2_overlap':dict(p3),'query_count':len(sql_manifest),'queries':sql_manifest,'results':result_manifest,'detail_json_sha256':hashlib.sha256((R/'data/short_gap_source_detail_per_target.json').read_bytes()).hexdigest(),'detail_csv_sha256':hashlib.sha256((R/'reports/2026-11-13-short-gap-source-detail.csv').read_bytes()).hexdigest(),'report_sha256':hashlib.sha256((R/'reports/2026-11-13-short-gap-source-detail.md').read_bytes()).hexdigest(),'database_mutations':0,'interpretation':'All source-backed targets are REVIEW_REQUIRED; no RESTORED or ESTIMATED operation emitted.'}
(R/'data/short_gap_source_detail_validation.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:manifest[k] for k in ['status','candidate_target_slots','source_covered_targets','source_archive_rows','source_rows_by_database','targets_with_zero_outTemp','targets_with_nonzero_outTemp','p3_v2_overlap','query_count','database_mutations']},indent=2))
