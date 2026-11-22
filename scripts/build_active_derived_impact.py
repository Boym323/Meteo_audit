#!/usr/bin/env python3
"""Build a provisional dependency impact map for active primary-field proposals."""
import csv,json
from datetime import datetime,timezone
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
registry=json.loads((ROOT/'config/active_proposal_registry.json').read_text())
# Candidate physical dependencies distilled from DERIVED_VARIABLE_AUDIT.md.
# These are not proof of the historical Loucka producer/formula.
DEPS={
 'outTemp':['dewpoint','windchill','heatindex','appTemp','humidex','cloudbase','ET','vpd','wbgt','outHumAbs','outThetaE','GTS','GTSdate','yearGDD','seasonGDD','dayET','ET24'],
 'outHumidity':['dewpoint','heatindex','appTemp','humidex','cloudbase','ET','vpd','wbgt','outHumAbs','outThetaE'],
 'windSpeed':['windchill','appTemp','ET','windrun','wbgt'],
 'windGust':[], 'windDir':[],
 'barometer':['altimeter','outThetaE'], 'rain':[], 'rainRate':[]
}
ops=[]
for p in registry['packages']:
 if p['status']!='ACTIVE': continue
 path=ROOT/p['path']/'corrections.json'
 corrections=json.loads(path.read_text())
 if len(corrections)!=p['field_operations']:
  raise ValueError(f"count mismatch {p['package_id']}: {len(corrections)} != {p['field_operations']}")
 for c in corrections:
  var=c['variable'];ts=int(c['timestamp'])
  ops.append({'package_id':p['package_id'],'classification':p['classification'],'timestamp':ts,
              'operation':c['operation'],'variable':var,'candidate_derived_fields_with_any_changed_input':DEPS.get(var,[]),
              'dependency_basis':'PROVISIONAL_CANDIDATE_ONLY; historical formula/producer not verified'})
if len(ops)!=registry['active_operation_count']:
 raise ValueError(f"active operation total mismatch: {len(ops)}")
key_counts=Counter((o['timestamp'],o['variable']) for o in ops)
if any(n>1 for n in key_counts.values()): raise ValueError('duplicate active timestamp+variable operation')
bytime=defaultdict(list)
for o in ops: bytime[o['timestamp']].append(o)
pervar=Counter(o['variable'] for o in ops)
insert_rows=sum(o['operation']=='insert' for o in ops)
update_ops=sum(o['operation']=='update' for o in ops)
if insert_rows!=registry['active_insert_operations'] or update_ops!=registry['active_update_operations']:
 raise ValueError('insert/update count does not match active registry')
if any(sum(o['operation']=='insert' for o in g)>1 for g in bytime.values()): raise ValueError('duplicate physical insert at timestamp')
for ts in bytime:
 dt=datetime.fromtimestamp(ts,timezone.utc)
 if dt.year==2021 or (dt.year==2018 and dt.month<=3): raise ValueError(f'protected timestamp in active operations: {dt.isoformat()}')
impact=Counter()
for ts,group in bytime.items():
 affected=set()
 for o in group: affected.update(o['candidate_derived_fields_with_any_changed_input'])
 for f in affected: impact[f]+=1
rows=[]
for o in sorted(ops,key=lambda x:(x['timestamp'],x['variable'],x['package_id'])):
 rows.append({**o,'candidate_derived_with_any_proposed_input_count':len(o['candidate_derived_fields_with_any_changed_input']),
              'active_fields_at_timestamp':';'.join(sorted({x['variable'] for x in bytime[o['timestamp']]})),
              'physical_row_expectation':'new row if package operation insert; actual target state must be reread before any approved application'})
summary={
 'schema':'derived-active-impact-v1','as_of_utc':registry['as_of_utc'],'scope':'ACTIVE package proposals only',
 'source_registry':'config/active_proposal_registry.json','operation_count':len(ops),'timestamp_count':len(bytime),'physical_insert_operations':insert_rows,'update_operations':update_ops,'duplicate_timestamp_variable_operations':0,
 'operation_counts_by_primary_field':dict(sorted(pervar.items())),
 'candidate_derived_variables_timestamp_counts_with_any_proposed_input':dict(sorted(impact.items())),
 'unique_candidate_derived_variables':sorted({f for o in ops for f in o['candidate_derived_fields_with_any_changed_input']}),
 'active_packages':{p['package_id']:{'field_operations':p['field_operations'],'unique_timestamps':p['unique_timestamps']} for p in registry['packages'] if p['status']=='ACTIVE'},
 'uncertainty':'Counts mean a proposal changes at least one candidate input at that target timestamp; they do not prove the derived value should be recalculated or that every required input is present. Windowed/cumulative fields may extend beyond that timestamp. No historical equation, producer version, hardware/software preference, or live current target state is asserted.',
 'windowed_or_cumulative_fields':['dayET','ET24','GTS','GTSdate','yearGDD','seasonGDD'],
 'separate_summary_dependency':'A primary rain/rainRate correction may affect daily precipitation summaries; this is outside the 21-column derived-variable graph and requires its own day-boundary/aggregation verification.',
 'mandatory_order':['resolve and approve primary source values','reread current target/history and apply only if separately approved','locally shadow-compute derived fields only after every required input is quality-approved and epoch/formula is confirmed','validate against the applicable producer version and independent holdouts','recompute daily/monthly/yearly summaries only after row-level values are stable','publish/statistical use only under separate approval'],
 'safety':'READ_ONLY; no staging, write, recalculation, or publication; Q1 2018 protected; 2021 diagnostic-only'
}
(ROOT/'data/active_derived_correction_impact.json').write_text(json.dumps({'summary':summary,'operations':rows},indent=2)+'\n')
with (ROOT/'reports/2026-11-13-active-derived-correction-impact.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps({'operations':len(ops),'timestamps':len(bytime),'inserts':insert_rows,'updates':update_ops,'primary_counts':dict(pervar),'candidate_derived_variables_timestamp_counts_with_any_proposed_input':dict(impact)},indent=2))
