#!/usr/bin/env python3
"""Reconcile the 2014-2015 B5 temperature cohort's source-quality dispositions."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
con=json.loads((R/'data/b5_2014_2015_gap_source_concordance.json').read_text())
quality=json.loads((R/'data/b5_2014_2015_gap_episode_quality.json').read_text())
nonzero=json.loads((R/'data/b5_2014_2015_nonzero_candidate_context.json').read_text())
pergap=json.loads((R/'data/b5_2014_2015_per_gap_availability.json').read_text())
assert con['database_mode']=='READ_ONLY_SELECT_ONLY'
assert len(con['records'])==65 and sum(r['source_union_timestamps']>0 for r in con['records'])==50
assert sum(r['source_union_timestamps']==0 for r in con['records'])==15
assert con['source_rows_summary']['source_union_timestamps']==1844
assert con['source_rows_summary']['paired_timestamps']==1844
assert con['source_rows_summary']['old_only']==con['source_rows_summary']['wh1080_only']==0
assert con['source_rows_summary']['fields']['outTemp']['paired_nonnull']==139
assert con['source_rows_summary']['fields']['outTemp']['equal']==139
assert con['source_rows_summary']['fields']['outTemp']['conflict']==0
by=quality['aggregates_by_year']
assert by['2014']['paired_rows']==794 and by['2015']['paired_rows']==1050
assert by['2014']['wh_outTemp_nonnull']==794 and by['2015']['wh_outTemp_nonnull']==1050
assert by['2014']['wh_outTemp_zero']==783 and by['2015']['wh_outTemp_zero']==1042
assert by['2014']['euold_exact_rows']==12 and by['2015']['euold_exact_rows']==8
assert by['2014']['euold_outTemp_nonnull']==11 and by['2015']['euold_outTemp_nonnull']==8
assert by['2014']['exact_luhamet_pairs']==0 and by['2015']['exact_luhamet_pairs']==222
cand=nonzero['records']; sm=nonzero['summary']
assert len(cand)==19 and sm['n']==19
assert sm['allOldWhEqual'] and sm['allEuOldPresent'] and sm['allOffGrid'] and sm['allMatchEndpoint']
assert sm['nearestEndpointOffsetSeconds']=={'min':1,'max':120}
assert sum(x['year']==2014 for x in cand)==11 and sum(x['year']==2015 for x in cand)==8
assert all(x['timestamp_remainder_300']!=0 and x['euold_row_ts']==x['timestamp'] for x in cand)
assert all(x['source_outTemp']==x['wh_outTemp']==x['euold_outTemp'] for x in cand)
assert all(x['source_outTemp'] in (x['left_target_outTemp'],x['right_target_outTemp']) for x in cand)
cohort={(r['left_time'],r['right_time']) for r in con['records']}
scoped=[x for x in pergap['records'] if (x['left_time'],x['right_time']) in cohort]
assert len(scoped)==65 and sum(x['source_state']=='NO_SOURCE_ROW_OBSERVED_IN_SIX_ARCHIVES' for x in scoped)==15
# Verify this evidence produced no outTemp corrections in the active registry.
reg=json.loads((R/'config/active_proposal_registry.json').read_text())
targets={(x['timestamp'],'outTemp') for x in cand}
for pkg in reg['packages']:
 if pkg['status']!='ACTIVE':continue
 rows=json.loads((R/pkg['path']/'corrections.json').read_text())
 assert not any((int(x['timestamp']),x['variable']) in targets for x in rows),pkg['package_id']
report=(R/'reports/2026-11-14-B5-2014-2015-temperature-episode-review.md').read_text()
assert '1,825' in report and 'TIMESTAMP_DUPLICATE_SUSPECTED' in report and 'SOURCE_SENSOR_STUCK_SUSPECTED' in report
assert 'READ-ONLY SELECT only' in report
print('PASS: 65 episodes partition 50 source-present / 15 no-source; 1,844 source pairs; 1,825 zeros held; 19 off-grid endpoint matches REVIEW_REQUIRED; no proposals or writes.')
