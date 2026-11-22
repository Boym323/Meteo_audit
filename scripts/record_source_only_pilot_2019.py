#!/usr/bin/env python3
"""Record the bounded 2019 source-only pilot-lane review."""
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RUN='20261113T105155Z-source-only-2019'
p=ROOT/'PROGRESS.json';d=json.loads(p.read_text());by={s['id']:s for s in d['stages']}
a=by['A']
if not any(t['id']=='A9' for t in a['subtasks']):a['subtasks'].append({'id':'A9','task':'Row-level review of the 2019 strict source-only cohort (233 timestamps): copy/unit/grid status, five primary fields, complete episodes, source neighbors, target history and third-archive presence','status':'COMPLETED','verified':True,'records_analyzed':233,'outputs':['reports/2026-11-13-source-only-pilot-2019-strong-concordance.md','reports/2026-11-13-source-only-pilot-2019-row-evidence.csv','data/source_only_pilot_2019_validation.json','data/source_only_pilot_2019_validation_result.json']})
a['analyzed_records'].update({'source_only_strict_2019_three_archive_targets':233,'source_only_strict_2019_review_required':233,'source_only_strict_2019_restored':0,'source_only_strict_2019_estimated':0,'source_only_strict_2019_missing':0})
paths=['sql/readonly/source_only_pilot_2019_strict_copy_cohort.sql','data/source-only-pilot-2019-strict-copy-concordance.json','data/source_only_pilot_2019_validation.json','data/source_only_pilot_2019_validation_result.json','reports/2026-11-13-source-only-pilot-2019-strong-concordance.md','reports/2026-11-13-source-only-pilot-2019-row-evidence.csv','scripts/analyze_source_only_pilot_2019.py','scripts/validate_source_only_pilot_2019.py']
seen={x['path'] for x in a['tracked_outputs']}
for path in paths:
 existing=next((x for x in a['tracked_outputs'] if x['path']==path),None)
 if existing:existing.update({'created':True,'verified':True,'verified_by':{'run_id':RUN,'manifest':f'runs/{RUN}/manifest.json'}})
 else:a['tracked_outputs'].append({'path':path,'created':True,'verified':True,'verified_by':{'run_id':RUN,'manifest':f'runs/{RUN}/manifest.json'}})
a['created_outputs']=sum(x['created'] for x in a['tracked_outputs']);a['verified_outputs']=sum(x['verified'] for x in a['tracked_outputs'])
by['L']['analyzed_records'].update({'source_only_strict_2019_review_required':233,'source_only_strict_2019_candidate_operations':0})
for s in d['stages']:
 s['defined_subtasks']=len(s['subtasks']);s['verified_subtasks']=sum(bool(x.get('verified')) for x in s['subtasks']);s['subtask_completion_percent']=round(100*s['verified_subtasks']/s['defined_subtasks'],1);s['completed_subtasks']=[x['task'] for x in s['subtasks'] if x.get('verified')];s['remaining_subtasks']=[{'task':x['task'],'state':x['status']} for x in s['subtasks'] if not x.get('verified')];s['status']='COMPLETED' if s['verified_subtasks']==s['defined_subtasks'] else 'IN_PROGRESS'
d['as_of_utc']=datetime.now(timezone.utc).isoformat(timespec='seconds');o=d['overall'];o['defined_subtasks']=sum(s['defined_subtasks'] for s in d['stages']);o['verified_subtasks']=sum(s['verified_subtasks'] for s in d['stages']);o['subtask_completion_percent']=round(100*o['verified_subtasks']/o['defined_subtasks'],1);o['completed_stages']=sum(s['status']=='COMPLETED' for s in d['stages']);o['completed_with_limitations_stages']=sum(s['status']=='COMPLETED_WITH_LIMITATIONS' for s in d['stages']);o['in_progress_stages']=sum(s['status']=='IN_PROGRESS' for s in d['stages']);o['blocked_stages']=sum(s['status']=='BLOCKED' for s in d['stages']);o['not_started_stages']=sum(s['status']=='NOT_STARTED' for s in d['stages'])
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(f"progress={o['verified_subtasks']}/{o['defined_subtasks']} ({o['subtask_completion_percent']}%)")
