#!/usr/bin/env python3
"""Record the bounded 2009 source-only row-review checkpoint."""
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RUN='20261113T104500Z-source-only-cohort'
p=ROOT/'PROGRESS.json';d=json.loads(p.read_text());by={s['id']:s for s in d['stages']}
a=by['A']
if not any(t['id']=='A8' for t in a['subtasks']):
 a['subtasks'].append({'id':'A8','task':'Row-level review of the strict 2009 source-only three-archive cohort (100 timestamps): units, five primary fields, source neighbors, change history, anomaly and field-specific conflicts','status':'COMPLETED','verified':True,'records_analyzed':100,'outputs':['reports/2026-11-13-source-only-pilot-2009-strong-concordance.md','reports/2026-11-13-source-only-pilot-2009-row-evidence.csv','data/source_only_pilot_2009_strong_copy_concordance_summary.json','data/source_only_pilot_2009_validation.json']})
a['analyzed_records'].update({'source_only_strict_2009_three_archive_targets':100,'source_only_strict_2009_review_required':100,'source_only_strict_2009_restored':0,'source_only_strict_2009_estimated':0,'source_only_strict_2009_missing':0})
a['subtasks'][4]['evidence_checkpoint']='Full container-visible local lineage filename search found no historical config/archive/dump/backup files; separate 100-row 2009 strict source cohort is row-reviewed but remains REVIEW_REQUIRED due constant runs, neighbor temperature anomaly, rain discordance and unauthenticated export identity.'
for sid in ('A','K','L'):
 s=by[sid]
 if sid=='A':paths=['sql/readonly/source_only_pilot_2009_strict_copy_cohort.sql','data/source-only-pilot-2009-strong-copy-concordance.json','data/source_only_pilot_2009_strong_copy_concordance_summary.json','data/source_only_pilot_2009_validation.json','reports/2026-11-13-source-only-pilot-2009-strong-concordance.md','reports/2026-11-13-source-only-pilot-2009-row-evidence.csv','scripts/analyze_source_only_pilot_2009.py','scripts/validate_source_only_pilot_2009.py']
 elif sid=='K':paths=['EXPERT_REVIEW_REQUIRED.md','reports/2026-11-13-expert-review-register.csv','scripts/validate_expert_review_register.py','reports/2026-11-13-source-only-pilot-2009-strong-concordance.md','reports/2026-11-13-source-only-pilot-2009-row-evidence.csv']
 else:paths=['reports/2026-11-13-source-only-pilot-2009-strong-concordance.md','reports/2026-11-13-source-only-pilot-2009-row-evidence.csv','data/source_only_pilot_2009_strong_copy_concordance_summary.json','data/source_only_pilot_2009_validation.json']
 seen={x['path'] for x in s['tracked_outputs']}
 for path in paths:
  if path not in seen:s['tracked_outputs'].append({'path':path,'created':True,'verified':True,'verified_by':{'run_id':RUN,'manifest':f'runs/{RUN}/manifest.json'}})
 s['created_outputs']=sum(x['created'] for x in s['tracked_outputs']);s['verified_outputs']=sum(x['verified'] for x in s['tracked_outputs'])
by['L']['analyzed_records'].update({'source_only_strict_2009_review_required':100,'source_only_strict_2009_candidate_operations':0})
by['K']['analyzed_records'].update({'expert_review_groups':35,'separate_expert_followups':1,'classified_register_rows':36})
for t in by['K']['subtasks']:
 if t['id']=='K2':t['task']='35 expert-review issue groups plus one masked-extrema follow-up; scope, impact, affected records/proposals and evidence mapped; register validated'
for s in d['stages']:
 s['defined_subtasks']=len(s['subtasks']);s['verified_subtasks']=sum(bool(x.get('verified')) for x in s['subtasks'])
 s['subtask_completion_percent']=round(100*s['verified_subtasks']/s['defined_subtasks'],1)
 s['completed_subtasks']=[x['task'] for x in s['subtasks'] if x.get('verified')]
 s['remaining_subtasks']=[{'task':x['task'],'state':x['status']} for x in s['subtasks'] if not x.get('verified')]
 s['status']='COMPLETED' if s['verified_subtasks']==s['defined_subtasks'] else 'IN_PROGRESS'
d['as_of_utc']=datetime.now(timezone.utc).isoformat(timespec='seconds')
o=d['overall'];o['defined_subtasks']=sum(s['defined_subtasks'] for s in d['stages']);o['verified_subtasks']=sum(s['verified_subtasks'] for s in d['stages']);o['subtask_completion_percent']=round(100*o['verified_subtasks']/o['defined_subtasks'],1)
o['completed_stages']=sum(s['status']=='COMPLETED' for s in d['stages']);o['completed_with_limitations_stages']=sum(s['status']=='COMPLETED_WITH_LIMITATIONS' for s in d['stages']);o['in_progress_stages']=sum(s['status']=='IN_PROGRESS' for s in d['stages']);o['blocked_stages']=sum(s['status']=='BLOCKED' for s in d['stages']);o['not_started_stages']=sum(s['status']=='NOT_STARTED' for s in d['stages'])
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(f"progress={o['verified_subtasks']}/{o['defined_subtasks']} ({o['subtask_completion_percent']}%)")
