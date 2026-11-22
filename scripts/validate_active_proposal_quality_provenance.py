#!/usr/bin/env python3
"""Validate schema-shaped value provenance sidecars and registry reconciliation without third-party packages."""
import json
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
schema=json.loads((R/'config/quality-provenance-record.schema.json').read_text());doc=json.loads((R/'data/active_proposal_quality_provenance.json').read_text());reg=json.loads((R/'config/active_proposal_registry.json').read_text());records=doc['records'];assert len(records)==324==doc['records_count']
required=set(schema['required']); props=set(schema['properties']); enums={k:set(v.get('enum',[])) for k,v in schema['properties'].items() if isinstance(v,dict) and 'enum' in v}
for x in records:
 assert set(x)==props or set(x)<=props,(set(x)-props,props-set(x))
 assert required<=set(x)
 assert x['schema_version']=='1.0' and x['origin_class'] in enums['origin_class'] and x['review_status'] in enums['review_status']
 assert x['uncertainty']['type'] in set(schema['properties']['uncertainty']['properties']['type']['enum']) and x['uncertainty']['type']=='unknown'
 assert x['uncertainty']['value'] is None and x['uncertainty']['unit']==x['unit']
 assert x['expected_target_state']['operation'] in ('insert','update','no_change')
 assert x['reason'] and 'NOT_APPROVED' in x['reason'] and 'NOT_APPLIED' in x['reason']
 assert x['source']['database'] and x['source']['timestamp_utc_epoch'] is not None and x['source']['value'] is not None
 assert x['source']['unit']
 assert x['validation']['group_id'] and x['validation']['metrics_ref']
 assert (R/x['validation']['metrics_ref']).exists()
 if x['origin_class']=='RESTORED':assert x['source']['database'] and isinstance(x['source']['value'],(int,float))
 else:assert x['origin_class']=='ESTIMATED' and x['validation']['holdout_scope'] and 'not an individual' in x['validation']['holdout_scope']
 assert x['review_status']=='REVIEW_REQUIRED'
 assert x['expected_target_state']['us_units'] in (16,17)
 package_id=x['batch_id'].rsplit(':batch-',1)[0]; pkg=next(q for q in reg['packages'] if q['package_id']==package_id and q['status']=='ACTIVE')
 op=next(q for q in pkg['operation_keys'] if int(q['timestamp'])==x['timestamp_utc_epoch'] and q['variable']==x['variable'])
 assert x['expected_target_state']['us_units']==op.get('target_us_units')
 assert op.get('source_unit_system') and 'target_us_units' in op
 if op['operation']=='insert': assert x['expected_target_state']['us_units']==16
 assert ('target code '+str(x['expected_target_state']['us_units'])) in x['source']['lineage_note']
by={(x['timestamp_utc_epoch'],x['variable']):x for x in records};assert len(by)==324
counts=Counter(x['origin_class'] for x in records);assert counts==Counter({'RESTORED':303,'ESTIMATED':21})
batches=defaultdict(int)
for x in records:batches[x['batch_id']]+=1
assert max(batches.values())<=50
assert sum(1 for x in records if x['variable']=='windSpeed' and x['source']['unit']=='m/s' and x['unit']=='km/h')>=1
print(json.dumps({'status':'PASS','records':len(records),'classes':dict(counts),'batches':len(batches),'max_batch_size':max(batches.values()),'individual_uncertainty':'UNKNOWN; grouped holdout metrics are not calibrated per-value intervals','proposal_status':'NOT_APPROVED / NOT_RUN / NOT_APPLIED'},ensure_ascii=False,indent=2))
