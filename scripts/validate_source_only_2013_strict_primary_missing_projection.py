#!/usr/bin/env python3
"""Validate the frozen 2013 strict primary-field candidate disposition."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/source_only_2013_strict_primary_missing_projection.json').read_text())
assert d['result_counts']=={'strict_source_rows':4,'source_copies_agree_all_five_primary_fields':4,'usUnits_17_interval_5':4,'projected_target_absent_from_reconstruction':4,'exact_grid_rows':3,'off_grid_rows':1,'exact_luhamet_source_matches':0,'source_or_projected_change_events':0}
rows=d['candidates'];assert len(rows)==4
held=[x for x in rows if x['source_time']==1360266480]
assert len(held)==1 and held[0]['offset_seconds']==-120
assert held[0]['disposition']=='REVIEW_REQUIRED_OFF_GRID_NO_SUPPORTED_SHIFT'
assert held[0]['archive_presence_at_projection']=={k:False for k in ('loucka_reconstruction','pocasi-loucka.eu','pocasi-loucka.eu_GW1000','pocasi-loucka.eu_old','old_weewx','weewx_WH1080')}
registry=json.loads((ROOT/'config/active_proposal_registry.json').read_text())
package=next(p for p in registry['packages'] if p['package_id']=='restored-source-only-2013-july-pilot')
pilot={x['timestamp'] for x in package['operation_keys']}
assert pilot=={1373319000,1373319600,1373320200,1373320800}
assert all(x['disposition']=='RESTORED_PROPOSED_ACTIVE_2013_PILOT' for x in rows if x['source_time'] in pilot)
assert all(x['source_metadata']=={'usUnits':17,'interval':5} for x in rows)
assert all(x['source_change_events']==x['projection_change_events']==0 for x in rows)
assert d['safety']=={'database_writes':0,'staging':False,'application':False,'publication':False}
print('PASS: 2013 strict screen has 3 already-proposed grid rows and 1 unsupported off-grid source key; no new operation')
