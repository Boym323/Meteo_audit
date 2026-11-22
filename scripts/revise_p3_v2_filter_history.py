#!/usr/bin/env python3
"""SUPERSEDED: one-time P3 v2.1 revision; active package is already finalized."""
raise SystemExit('SUPERSEDED one-time P3 v2.1 builder; use the package validator and simulate_v2_1.py')
import csv, hashlib, json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'proposals/estimated_short_temperature_gaps_v2'
H=json.loads((R/'data/p3_filter_input_history_2019_2020.json').read_text())['result']
VARS=['outTemp','outHumidity','rain','rainRate','windSpeed']
REVIEW={1556184600,1556184900,1556185200}
# Reconstruct endpoint-role records and the exact events returned for each variable.
by={}
for row in H:
    key=(int(row['event_time']),row['event_role'])
    obj=by.setdefault(key,{'time':key[0],'row_present':False,'usUnits':row.get('usUnits'),'interval':row.get('interval'),'values':{},'history':{v:{'event_count':0,'events':[]} for v in VARS}})
    obj['row_present']=obj['row_present'] or row.get('archive_row_present') is not None
    obj['usUnits']=row.get('usUnits') if row.get('usUnits') is not None else obj['usUnits']
    obj['interval']=row.get('interval') if row.get('interval') is not None else obj['interval']
    v=row['variable'];obj['values'][v]=row.get(v)
    if row.get('change_id') is not None:
        event={k:row.get(k) for k in ['change_id','change_state','batch_key','old_value','new_value','source_database','source_time','source_value','reason','created_at','applied_at']}
        obj['history'][v]['events'].append(event);obj['history'][v]['event_count']+=1
for o in by.values():
    for v in VARS:o['history'][v]['events'].sort(key=lambda e:(e.get('created_at') or '',e.get('change_id') or 0))
meta=json.loads((P/'candidate_metadata.json').read_text())
ops=json.loads((P/'corrections.json').read_text())
assert len(ops) in (21,24) and len(meta)==107
change_rows=json.loads((P/'change_event_counts_107.json').read_text())['rows']
target_changes={int(x['target_time']):int(x['all_change_events']) for x in change_rows}
est={int(x['timestamp']) for x in meta if 'filter_input_history' in x}
assert len(est)==24 and REVIEW <= est
# Construct audit context for every existing estimate, keeping target and endpoint provenance separate.
for m in meta:
    ts=int(m['timestamp'])
    if ts not in est:continue
    left=int(m['left']['t']);right=int(m['right']['t'])
    lhs=by[(left,'LEFT_ENDPOINT')];rhs=by[(right,'RIGHT_ENDPOINT')]
    events=[{'endpoint_role':role,'endpoint_time':obj['time'],'variable':v,**e}
            for role,obj in [('LEFT_ENDPOINT',lhs),('RIGHT_ENDPOINT',rhs)]
            for v,d in obj['history'].items() for e in d['events']]
    count=len(events)
    status='REVIEW_REQUIRED_FILTER_INPUT_PROVENANCE' if ts in REVIEW else 'NO_LOGGED_ENDPOINT_FILTER_INPUT_CHANGES'
    audit={'target_time':ts,'target_row_present':False,'target_history_scope':'all variables in reconstruction_changes','target_change_events_all_variables':target_changes.get(ts,0),'filter_variables':VARS,'left_endpoint':lhs,'right_endpoint':rhs,'endpoint_filter_history_event_count':count,'context_history_events':events,'status':status,'interpretation':'A missing event means no recorded reconstruction change, not proof of measurement certainty.'}
    m['target_change_history_all_variables_checked']=True
    m['target_change_history_all_variables_count']=target_changes.get(ts,0)
    m['filter_input_history']=audit
    m['contextual_input_uncertainty']={'status':'NOT_NUMERICALLY_CALIBRATED','variables':VARS,'description':'Endpoint context measurement uncertainty is not represented by interpolation holdout residual quantiles.'}
    if 'gates' in m:
        m['gates'].pop('no_history',None)
        m['gates']['target_change_history_all_variables_checked']=True
        m['gates']['target_change_history_clear']=target_changes.get(ts,0)==0
        m['gates']['endpoint_filter_input_history_checked']=True
        m['gates']['endpoint_filter_input_history_clear']=count==0
    if 'uncertainty_abs_error_c' in m:
        m['uncertainty_legacy_general_validation_abs_error_c']=m.pop('uncertainty_abs_error_c')
        m['uncertainty_legacy_general_validation_source']='2019–2020 seasonal masked-block 1h holdout; not conditioned on selected candidate filters.'
    m['uncertainty_contract']={'conditional_holdout':m.get('uncertainty'),'contextual_inputs':'NOT_NUMERICALLY_CALIBRATED','individual_prediction_interval_guaranteed':False,'display_policy':'Label ESTIMATED; show empirical holdout scope, sample size and quantile. Never present as an individual prediction interval.'}
    if ts in REVIEW:
        m['classification']='REVIEW_REQUIRED';m['source_first_status']='REVIEW_REQUIRED_INPUT_PROVENANCE';m['p3_v2_status']='REVIEW_REQUIRED_FILTER_INPUT_PROVENANCE'
        m['methodological_review_required']='One or both endpoint outHumidity inputs were applied as ESTIMATED in humidity-2019-apr-month-097-v3; validate RH-filter sensitivity/input uncertainty before considering this temperature estimate.'
    else:
        m['p3_v2_status']='ESTIMATED';m['filter_input_history_status']='No reconstruction_changes events for the five filter variables at either endpoint.'
# Read-only query audit has exactly two events; both are applied estimated RH at the two endpoints.
assert len([r for r in H if r.get('change_id') is not None])==2
assert {int(r['event_time']) for r in H if r.get('change_id') is not None}=={1556184300,1556185500}
# Exclude only the three affected estimates from active correction operations.
active=[o for o in ops if int(o['timestamp']) not in REVIEW]
assert len(active)==21
(P/'candidate_metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
(P/'corrections.json').write_text(json.dumps(active,ensure_ascii=False,indent=2)+'\n')
with (P/'corrections.csv').open(newline='',encoding='utf-8') as f:
    rd=csv.DictReader(f);cols=rd.fieldnames;rows=[r for r in rd if int(r['timestamp']) not in REVIEW]
with (P/'corrections.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
# Add the 3 input-provenance reviews while retaining all 83 source-conflict reviews.
with (P/'review_required.csv').open(newline='',encoding='utf-8') as f:
    rd=csv.DictReader(f);review_cols=rd.fieldnames;reviews=list(rd)
by_meta={int(m['timestamp']):m for m in meta}
existing_review_ts={int(r['timestamp']) for r in reviews}
for ts in sorted(REVIEW-existing_review_ts):
    m=by_meta[ts];a=m['filter_input_history'];lh=a['left_endpoint'];rh=a['right_endpoint']
    reviews.append({'timestamp':ts,'utc_year':2019,'gap_seconds':m['gap_s'],'left_endpoint_utc':m['left']['t'],'right_endpoint_utc':m['right']['t'],'interpolation_c':m['interpolation_value_c'],'old_weewx_outTemp':'','weewx_WH1080_outTemp':'','old_weewx_abs_diff_c':'','weewx_WH1080_abs_diff_c':'','old_weewx_outHumidity':'','weewx_WH1080_outHumidity':'','old_weewx_rain':'','weewx_WH1080_rain':'','old_weewx_rainRate':'','weewx_WH1080_rainRate':'','old_weewx_interval':'','wh1080_interval':'','old_weewx_usUnits':'','wh1080_usUnits':'','old_prev_outTemp':lh['values'].get('outTemp'),'old_next_outTemp':rh['values'].get('outTemp'),'wh_prev_outTemp':'','wh_next_outTemp':'','disposition':'REVIEW_REQUIRED_FILTER_INPUT_PROVENANCE','reason':'Endpoint RH includes applied ESTIMATED reconstruction history (humidity-2019-apr-month-097-v3); assess RH-filter dependence and contextual uncertainty.'})
with (P/'review_required.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=review_cols);w.writeheader();w.writerows(reviews)
# Explicit per-target provenance fields, without implying 83 source-conflict endpoints were checked.
with (P/'per_target_source_evidence.csv').open(newline='',encoding='utf-8') as f:
    rd=csv.DictReader(f);oldcols=rd.fieldnames;evrows=list(rd)
newcols=oldcols+['target_history_all_variables_checked','target_history_all_variables_event_count','filter_input_history_checked','filter_input_history_event_count','filter_input_history_status']
for r in evrows:
    ts=int(r['timestamp'])
    if ts in est:
        a=by_meta[ts]['filter_input_history'];r.update(target_history_all_variables_checked='true',target_history_all_variables_event_count=str(a['target_change_events_all_variables']),filter_input_history_checked='true',filter_input_history_event_count=str(a['endpoint_filter_history_event_count']),filter_input_history_status=a['status'])
    else:r.update(target_history_all_variables_checked='false',target_history_all_variables_event_count='',filter_input_history_checked='false',filter_input_history_event_count='',filter_input_history_status='NOT_CHECKED_FOR_SOURCE_CONFLICT_SCREEN')
with (P/'per_target_source_evidence.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=newcols);w.writeheader();w.writerows(evrows)
# Summarized exact query evidence.
summary={'query_result_rows':len(H),'target_estimates_audited':len(est),'target_change_events':sum(target_changes.get(t,0) for t in est),'endpoint_filter_variables':VARS,'endpoint_history_events':2,'affected_candidates':sorted(REVIEW),'affected_input_events':[{'time':int(r['event_time']),'variable':r['variable'],'new_value':r['new_value'],'state':r['change_state'],'batch_key':r['batch_key']} for r in H if r.get('change_id') is not None],'remaining_clear_candidates':21,'scope':'All 24 ESTIMATED candidates; both endpoints; outTemp, outHumidity, rain, rainRate, windSpeed; target history across all variables.'}
(R/'data/p3_filter_input_history_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
# Correct physical insert semantics and per-variable completeness.
dep=json.loads((P/'dependency_metadata.json').read_text());dep.update({'proposal_operations':21,'physical_archive_rows_created_if_applied':21,'whole_row_inserts':21,'row_completeness':'Each INSERT creates a new archive row and supplies required dateTime/usUnits/interval plus outTemp. Other primary variables remain NULL unless independently proposed.','per_variable_completeness':'outTemp is supplied for each of the 21 rows; outHumidity, rain, rainRate, windSpeed and other fields are not synthesized.','synthetic_zero_rain_prohibited':True,'pre_application_checklist':'pre_application_checklist.md'})
(P/'dependency_metadata.json').write_text(json.dumps(dep,ensure_ascii=False,indent=2)+'\n')
sim=json.loads((P/'simulation.json').read_text());sim.update({'simulated_estimated_inserts':21,'review_required':86,'physical_archive_rows_created_if_applied':21,'whole_row_inserts':21,'input_provenance_reviews_added':3,'restored':0,'missing':0,'duplicate_operations':0})
(P/'simulation.json').write_text(json.dumps(sim,ensure_ascii=False,indent=2)+'\n')
contract={'schema_version':'1.0.0','classification':'ESTIMATED','uncertainty':{'legacy_general_1h_masked_block':{'p50_abs_error_c':0.15,'p90_abs_error_c':0.55,'p95_abs_error_c':0.75,'scope':'general seasonal 2019–2020 masked-block holdout; not selected-filter conditional'},'conditional_duration_holdout':'See conditional_holdout_2019_2020.json; duration bins have empirical p95 upper edges 0.3–0.5 C with sample counts.','contextual_input_uncertainty':'NOT_NUMERICALLY_CALIBRATED','individual_prediction_interval_guaranteed':False},'consumer_display_contract':{'must_label':'ESTIMATED','show_empirical_quantile_scope':True,'show_validation_sample_size':True,'must_not_call_prediction_interval':True,'must_not_imply_individual_coverage_probability':True}}
(P/'uncertainty_contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
check='''# P3 předaplikační checklist (bez schválení se nic neaplikuje)\n\nTento dokument je pouze kontrolní plán; žádná databázová aplikace ani staging zde neproběhly. Každá cílová korekce by fyzicky vytvořila nový `archive` řádek: povinné `dateTime`, `usUnits`, `interval` a navržené `outTemp`. To je 21 fyzických řádků, nikoli 21 kompletních meteorologických řádků.\n\nPřed případnou samostatně schválenou aplikací: (1) vytvořit konzistentní read-only ověřenou zálohu cílových časů, jejich případných řádků a všech reconstruction_changes; ověřit obnovitelnost zálohy; (2) znovu ověřit, že každý timestamp je stále bez archive row a bez nových změn, že epizody jsou celé a dávka nepřekračuje 50; (3) ověřit `usUnits=16`, `interval=5`, jednotky a expected-old absence; (4) ověřit source-first dostupnost napříč relevantními archivy; (5) vkládat pouze outTemp s deklarovaným původem a uncertainty metadata; (6) po aplikaci ověřit přesně 21 řádků, hodnoty, změnovou historii a to, že jiné veličiny zůstaly NULL/nezměněné; (7) ověřit žádné duplicity a žádné syntetické srážky. Nevyplňovat rain nulou ani jinou veličinu jen kvůli vložení teplotního řádku.\n\nRollback plán pro budoucí schválený zásah: předem zaznamenat přesné cílové PK, stav absence řádků a identifikátory vzniklých eventů. Rollback může odstranit pouze řádky prokazatelně vytvořené danou dávkou a pouze po nové výslovné autorizaci; nejprve ověřit, že od aplikace nenastala další závislá změna. Pokud je stav nejednoznačný, zastavit rollback a eskalovat. Současný audit tento plán neprovádí.\n'''
(P/'pre_application_checklist.md').write_text(check)
# Update package README and generate content manifest at end.
readme=(P/'README.md').read_text();readme+='''\n\n## Revision v2.1 – endpoint filter-input history review\n\nThe active estimate set is 21 candidates. Three 2019-04 candidates (1556184600, 1556184900, 1556185200) are REVIEW_REQUIRED because both endpoint RH inputs include applied ESTIMATED history. The other 21 estimates were checked for reconstruction history across target all-variable history and endpoint filter variables outTemp, outHumidity, rain, rainRate and windSpeed; no endpoint events were found. The original v2 ZIP and the pre-review snapshot remain preserved separately. No database write or staging was performed. See `filter_input_history_summary.json` (workspace companion), `uncertainty_contract.json`, and `pre_application_checklist.md`.\n'''
(P/'README.md').write_text(readme)
# Machine-read manifest includes every regular file except itself.
artifacts={}
for f in sorted(P.iterdir()):
    if f.is_file() and f.name!='manifest.json':
        b=f.read_bytes();artifacts[f.name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
manifest={'package':'estimated_short_temperature_gaps_v2','revision':'v2.1','priority':'P3','classification':'MIXED_ESTIMATED_AND_REVIEW_REQUIRED','target_count':107,'restored_count':0,'estimated_count':21,'review_required_count':86,'missing_count':0,'decision':'Original P3 v2 is preserved as historical evidence. Three estimates with applied ESTIMATED RH filter inputs moved to REVIEW_REQUIRED; 21 independent-context estimates retained.','source_archives':['loucka_reconstruction','pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old','old_weewx','weewx_WH1080'],'batch_limit':50,'batch_count':1,'episode_split':False,'database_access':'READ_ONLY_SELECT_ONLY','writes_or_staging':False,'q1_2018':'excluded','year_2021':'diagnostic_only','artifacts':artifacts}
(P/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'estimated':21,'review_required':86,'endpoint_events':2,'manifest_artifacts':len(artifacts)},indent=2))
