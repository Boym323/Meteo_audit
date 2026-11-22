#!/usr/bin/env python3
"""Create conservative episode dispositions from frozen six-archive B5 availability/alignment evidence."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'data/b5_2009_2013_gap_per_archive_availability.json').read_text())
by={(r['year'],r['gap_id']):r for r in d['alignment_results']}
results=[]
for g in d['gaps']:
 y=int(g['prev_utc'][:4]);a=by.get((y,g['gap_id']))
 if a is None:
  cls='NO_OBSERVED_SOURCE_ROWS'; reason='No observed rows in any of the six archives inside this open interval; this does not establish station downtime or intentional deletion.'; n=0
 elif int(a['old_source_rows'])==int(a['off_300s_grid']) and int(a['rows_projecting_to_occupied_reconstruction_slots'])==int(a['old_source_rows']) and int(a['source_projection_collisions'])==0:
  cls='TIMESTAMP_DUPLICATE_SUSPECTED_REVIEW_REQUIRED';reason='All observed old_weewx source timestamps are off-grid and project to occupied reconstruction timestamps without within-episode projection collisions; time-shift identity is not proven.';n=int(a['old_source_rows'])
 elif int(a['old_source_rows'])==int(a['on_300s_grid']) and int(a['rows_projecting_to_occupied_reconstruction_slots'])==0:
  cls='SOURCE_SENSOR_STUCK_SUSPECTED_REVIEW_REQUIRED';reason='On-grid keys lack exact/projected target rows; both source-bearing episodes have flat outTemp series and fail the anomaly-free restoration gate.';n=int(a['old_source_rows'])
 else:
  cls='UNRESOLVED_MIXED_SOURCE_ALIGNMENT';reason='Mixed on/off-grid or projected-target state requires row-level review.';n=int(a['old_source_rows'])
 results.append({**g,'source_rows':n,'source_archives':['old_weewx','weewx_WH1080','pocasi-loucka.eu_old'] if n else [],'alignment_evidence':a,'disposition':cls,'reason':reason,'restoration_proposal_created':False})
from collections import Counter
counts=Counter(r['disposition'] for r in results)
out={'schema':'b5-2009-2013-gap-episode-disposition-v1','event_count':len(results),'disposition_counts':dict(counts),'source_rows_total':sum(r['source_rows'] for r in results),'source_rows_by_disposition':{k:sum(r['source_rows'] for r in results if r['disposition']==k) for k in counts},'proposal_count':sum(r['restoration_proposal_created'] for r in results),'interpretation':'Conservative dispositions summarize observed availability and alignment. TIMESTAMP_DUPLICATE_SUSPECTED and SOURCE_SENSOR_STUCK_SUSPECTED are not confirmed causes. NO_OBSERVED_SOURCE_ROWS is not proof of deletion or downtime.','safety':d['safety'],'events':results}
assert counts=={'NO_OBSERVED_SOURCE_ROWS':71,'SOURCE_SENSOR_STUCK_SUSPECTED_REVIEW_REQUIRED':2,'TIMESTAMP_DUPLICATE_SUSPECTED_REVIEW_REQUIRED':90}
assert out['source_rows_total']==192 and out['proposal_count']==0
(ROOT/'data/b5_2009_2013_gap_episode_disposition.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'PASS','events':len(results),'disposition_counts':dict(counts),'source_rows_by_disposition':out['source_rows_by_disposition'],'proposals':0},indent=2))
