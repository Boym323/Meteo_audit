#!/usr/bin/env python3
"""Record verified CHMI P4 checkpoint in PROGRESS.json and render STATUS.md."""
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN='20261113T102301Z-chmi-p4-winter'
p=ROOT/'PROGRESS.json';d=json.loads(p.read_text())
by={s['id']:s for s in d['stages']}
def add_task(stage_id,tid,task):
 s=by[stage_id]
 if not any(x['id']==tid for x in s['subtasks']):s['subtasks'].append({'id':tid,'task':task,'status':'COMPLETED','verified':True,'records_analyzed':136512 if tid=='G5' else 5608,'outputs':['data/chmi-rh-winter-validation/manifest.json','reports/2026-11-13-chmi-winter-rh-reference-validation.md','scripts/validate_chmi_rh_winter_validation.py']})
add_task('G','G5','Official CHMI Jan–Feb winter T/RH cache for 2019–2022, metadata quality-code screening, hashes and exact source manifest')
add_task('H','H7','Independent CHMI winter context joined at exact UTC hours; outage coverage, historical epoch stability and frost/high-RH reference limits documented; no model/candidates')
by['G']['analyzed_records'].update({'CHMI_winter_files':32,'CHMI_winter_element_records':136512,'CHMI_metadata_files':2})
by['H']['analyzed_records'].update({'CHMI_winter_station_timestamps':68256,'exact_hour_local_rows':5608,'2022_outage_exact_hour_rows':695,'2022_outage_LuhaMet_RH_exact_hours':693,'P4_candidates_created':0})
by['D']['analyzed_records'].update({'CHMI_winter_station_timestamps':68256,'2022_outage_exact_hour_rows':695,'2022_outage_local_RH_nonnull':0,'2022_outage_LuhaMet_RH_exact_hours':693})
outputs={
'G':['data/chmi-rh-winter-validation/manifest.json','data/chmi-rh-winter-validation/validation.json','data/chmi-rh-winter-validation/source_history_summary.json','sql/readonly/chmi_rh_winter_local_history_counts.sql','reports/2026-11-13-chmi-winter-rh-reference-validation.md','scripts/fetch_chmi_rh_winter_validation.py','scripts/analyze_chmi_rh_winter_validation.py','scripts/validate_chmi_rh_winter_validation.py'],
'H':['sql/readonly/chmi_rh_winter_reference_join.sql','sql/readonly/chmi_rh_winter_local_history_counts.sql','data/chmi-rh-winter-validation/loucka_hourly_complete_cases.json','data/chmi-rh-winter-validation/source_history_summary.json','reports/2026-11-13-chmi-winter-rh-reference-validation.json','reports/2026-11-13-chmi-winter-rh-reference-validation.md','scripts/analyze_chmi_rh_winter_validation.py','scripts/validate_chmi_rh_winter_validation.py'],
'D':['reports/2026-11-13-chmi-winter-rh-reference-validation.md','reports/2026-11-13-chmi-winter-rh-reference-validation.json','EXPERT_REVIEW_REQUIRED.md','HUMAN_INPUT_REQUIRED.md']}
for sid,paths in outputs.items():
 s=by[sid]; seen={x['path'] for x in s['tracked_outputs']}
 for path in paths:
  if path not in seen:s['tracked_outputs'].append({'path':path,'created':True,'verified':True,'verified_by':{'run_id':RUN,'manifest':f'runs/{RUN}/manifest.json'}})
 s['created_outputs']=sum(x['created'] for x in s['tracked_outputs']);s['verified_outputs']=sum(x['verified'] for x in s['tracked_outputs'])
for s in d['stages']:
 s['defined_subtasks']=len(s['subtasks']);s['verified_subtasks']=sum(bool(x['verified']) for x in s['subtasks'])
 s['subtask_completion_percent']=round(100*s['verified_subtasks']/s['defined_subtasks'],1)
 s['completed_subtasks']=[x['task'] for x in s['subtasks'] if x['verified']]
 s['remaining_subtasks']=[{'task':x['task'],'state':x['status']} for x in s['subtasks'] if not x['verified']]
 s['status']='COMPLETED' if s['verified_subtasks']==s['defined_subtasks'] else ('NOT_STARTED' if not s['verified_subtasks'] and all(x['status']=='NOT_STARTED' for x in s['subtasks']) else 'IN_PROGRESS')
d['as_of_utc']=datetime.now(timezone.utc).isoformat(timespec='seconds')
d['overall']['defined_subtasks']=sum(s['defined_subtasks'] for s in d['stages']);d['overall']['verified_subtasks']=sum(s['verified_subtasks'] for s in d['stages'])
d['overall']['subtask_completion_percent']=round(100*d['overall']['verified_subtasks']/d['overall']['defined_subtasks'],1)
d['overall']['completed_stages']=sum(s['status']=='COMPLETED' for s in d['stages']);d['overall']['completed_with_limitations_stages']=sum(s['status']=='COMPLETED_WITH_LIMITATIONS' for s in d['stages']);d['overall']['in_progress_stages']=sum(s['status']=='IN_PROGRESS' for s in d['stages']);d['overall']['blocked_stages']=sum(s['status']=='BLOCKED' for s in d['stages']);d['overall']['not_started_stages']=sum(s['status']=='NOT_STARTED' for s in d['stages'])
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
# Render from current machine-readable state (not the older static task catalogue).
o=d['overall'];lines=['## Aktuální matice etap A–O (vygenerována z PROGRESS.json)','',f"Snapshot: `{d['as_of_utc']}`. Definované podúkoly ověřené **{o['verified_subtasks']}/{o['defined_subtasks']} ({o['subtask_completion_percent']}%)**; procento zahrnuje jen explicitní ověřené podúkoly.",'','| Etapa | Stav | Ověřené podúkoly | Analyzované záznamy / rozsah | Výstupy vytvořené / ověřené | Zbývající práce | Závislosti |','|---|---|---:|---|---:|---|---|']
for s in d['stages']:
 rec='; '.join(f'{k}={v}' for k,v in s['analyzed_records'].items() if not isinstance(v,dict))
 lines.append(f"| {s['id']} — {s['name']} | `{s['status']}` | {s['verified_subtasks']}/{s['defined_subtasks']} | {rec} | {s['created_outputs']}/{s['verified_outputs']} z {len(s['tracked_outputs'])} | {s['remaining_analytical_effort_hours']['min']}–{s['remaining_analytical_effort_hours']['max']} h | {', '.join(s['dependencies']) or '—'} |")
lines+=['','### Etapové podúkoly a blokátory','']
for s in d['stages']:
 done='; '.join(s['completed_subtasks']) or 'zatím nic';remain='; '.join(x['task']+' ['+x['state']+']' for x in s['remaining_subtasks']) or 'nic'
 blockers='; '.join(s['current_blockers']) or 'žádné známé'
 lines += [f"#### Etapa {s['id']} — {s['name']} (`{s['status']}`)",'',f'**Dokončeno:** {done}','','**Zbývá:** '+remain,'',f'**Blokátory:** {blockers}','',f"**Náročnost:** {s['remaining_analytical_effort_hours']['min']}–{s['remaining_analytical_effort_hours']['max']} h; **závislosti:** {', '.join(s['dependencies']) or 'žádné'}.",'']
e=d['estimated_remaining_effort_hours'];f=d['calendar_forecast'];lines += ['### Odhad dokončení','',f"Zbývá {e['min']}–{e['max']} analytických hodin; orientačně {f['range']} při uvedeném tempu. Nejistota: {f['uncertainty']}. Předpoklady: {f['pace_basis']}.",'','Viz `PROGRESS.json` pro strojově čitelnou evidenci; bezpečnostní omezení jsou v souboru zachována.','']
sp=ROOT/'STATUS.md';old=sp.read_text();a='<!-- PROGRESS_MATRIX_START -->';b='<!-- PROGRESS_MATRIX_END -->';block=a+'\n'+'\n'.join(lines)+'\n'+b
if a in old and b in old:old=old[:old.index(a)]+block+old[old.index(b)+len(b):]
else:old=old+'\n'+block+'\n'
sp.write_text(old)
print(f"progress={o['verified_subtasks']}/{o['defined_subtasks']} ({o['subtask_completion_percent']}%)")
