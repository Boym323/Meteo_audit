#!/usr/bin/env python3
"""Validate episode grouping against frozen short-gap source rows."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
src=json.loads((R/'data/short_gap_source_detail_per_target.json').read_text())['records']
out=json.loads((R/'data/b5_short_gap_zero_outtemp_2014_2015_review.json').read_text())
expect={(2014,164,74,156,0),(2015,140,55,48,70)}
assert out['summary']['rows']==304 and out['summary']['episodes']==129
assert out['summary']['target_change_events']==0 and out['summary']['proposals_created']==0
assert out['source_access']=='FROZEN_LOCAL_SNAPSHOT_ONLY; no database access'
assert {r['timestamp'] for r in out['records']}=={r['timestamp'] for r in src if r['utc_year'] in (2014,2015) and r['outTemp_exact_zero_source_present']}
for y,n,episodes,warm,near in expect:
 x=out['summary']['by_year'][str(y)]
 assert x['zero_targets']==n and x['runs']==episodes
 assert x['context_band_counts'].get('WARM_OR_COLD_INTERPOLATION_CONTRAST_GT_5C',0)==warm
 assert x['context_band_counts'].get('NEAR_ZERO_INTERPOLATION_CONTEXT',0)==near
 if y==2014: assert x['context_band_counts'].get('NO_ENDPOINT_CONTEXT',0)==8
assert all(x['interpretation'] in ('SOURCE_SENSOR_STUCK_SUSPECTED','REVIEW_REQUIRED_POSSIBLY_VALID_ZERO_OR_SENSOR_FAULT') for x in out['records'])
assert all(e['n']>=1 for e in out['episodes'])
print('PASS: 304 exact-zero source targets in 129 bounded candidate runs; 2014 156 warm-context flags/8 no endpoint context; 2015 48 warm-context/70 near-zero; zero events/proposals/writes.')
