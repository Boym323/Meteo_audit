#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'data/b5_2009_2013_gap_episode_disposition.json'
d=json.loads(p.read_text());c=Counter(e['disposition'] for e in d['events'])
assert d['event_count']==163 and len(d['events'])==163
assert c=={'NO_OBSERVED_SOURCE_ROWS':71,'SOURCE_SENSOR_STUCK_SUSPECTED_REVIEW_REQUIRED':2,'TIMESTAMP_DUPLICATE_SUSPECTED_REVIEW_REQUIRED':90}
assert d['source_rows_total']==192 and d['proposal_count']==0
assert d['source_rows_by_disposition']=={'NO_OBSERVED_SOURCE_ROWS':0,'SOURCE_SENSOR_STUCK_SUSPECTED_REVIEW_REQUIRED':100,'TIMESTAMP_DUPLICATE_SUSPECTED_REVIEW_REQUIRED':92}
for e in d['events']:
 assert not e['restoration_proposal_created']
 if e['disposition']=='TIMESTAMP_DUPLICATE_SUSPECTED_REVIEW_REQUIRED':
  a=e['alignment_evidence'];assert int(a['off_300s_grid'])==e['source_rows']==int(a['rows_projecting_to_occupied_reconstruction_slots'])
  assert int(a['source_projection_collisions'])==0
 if e['disposition']=='SOURCE_SENSOR_STUCK_SUSPECTED_REVIEW_REQUIRED':assert e['prev_utc'].startswith('2009-')
assert d['safety']['writes']==0 and d['safety']['staging'] is False and d['safety']['application'] is False
assert d['safety']['excluded_years']==[2018,2021]
print('PASS: all 163 2009–2013 intervals have conservative source-state dispositions; no proposal, write, staging or protected-period access.')
