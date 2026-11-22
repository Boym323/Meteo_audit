#!/usr/bin/env python3
"""Overlay already-reviewed source-only row cohorts on the reconstruction gap catalog.

This is an offline evidence join. Absence from the selected exports does not mean
that no archive contains a measurement.
"""
import bisect,csv,json
from collections import Counter,defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
GAP=R/'reports/2026-11-12-gap-event-catalog.csv'
INPUTS=[
 ('source_only_2009_pilot','reports/2026-11-13-source-only-pilot-2009-row-evidence.csv','dateTime'),
 ('source_only_2019_pilot','reports/2026-11-13-source-only-pilot-2019-row-evidence.csv','dateTime'),
 ('source_only_2017_strict','reports/2026-11-13-source-only-strict-2017-row-evidence.csv','ts'),
 ('source_only_residual_strict','reports/2026-11-13-source-only-residual-strict-cohorts-row-evidence.csv','ts'),
 ('source_only_2015_outtemp','data/2015_source_only_outtemp_field_disposition.csv','target_time'),
]
pergap_csv=R/'reports/2026-11-13-b5-gap-reviewed-source-overlap-by-event.csv'
matched_csv=R/'reports/2026-11-13-b5-gap-reviewed-source-overlap-row-evidence.csv'
out_json=R/'data/b5_gap_reviewed_source_cohort_overlay.json'

with GAP.open(newline='',encoding='utf-8') as f:
 gaps=[]
 for i,r in enumerate(csv.DictReader(f),1):
  gaps.append({'gap_event_id':i,'prev_ts':int(r['prev_ts']),'target_ts':int(r['target_ts']),
   'delta_seconds':int(r['delta_seconds']),'prev_interval':int(r['prev_interval']),
   'current_interval':int(r['current_interval']),'utc_year':int(r['utc_year']),
   'prev_utc':r['prev_utc'],'target_utc':r['target_utc']})
starts=[g['prev_ts'] for g in gaps]
cohort_rows=[]
input_row_counts={}
for name,rel,col in INPUTS:
 with (R/rel).open(newline='',encoding='utf-8') as f:
  rows=list(csv.DictReader(f));input_row_counts[name]=len(rows)
  for r in rows:
   ts=int(r[col]); label=(r.get('classification') or r.get('field_quality_disposition') or r.get('restoration_decision') or 'UNCLASSIFIED_IN_SOURCE_EXPORT')
   i=bisect.bisect_left(starts,ts)-1
   if i>=0 and gaps[i]['prev_ts']<ts<gaps[i]['target_ts']:
    g=gaps[i]
    on_grid=(g['delta_seconds']%300==0 and g['prev_interval']==5 and g['current_interval']==5 and (ts-g['prev_ts'])%300==0)
    cohort_rows.append({'gap_event_id':g['gap_event_id'],'utc_year':g['utc_year'],'gap_prev_ts':g['prev_ts'],
     'gap_target_ts':g['target_ts'],'gap_delta_seconds':g['delta_seconds'],'source_timestamp':ts,
     'source_offset_from_prev_seconds':ts-g['prev_ts'],'expected_5m_slot_within_gap':int(on_grid),
     'cohort':name,'existing_review_label':label})

# Keep exact duplicate timestamps visible in the row-level file; event summaries
# count unique timestamps so overlapping source exports cannot inflate candidates.
cohorts_by_gap=defaultdict(lambda:defaultdict(set)); labels_by_gap=defaultdict(lambda:defaultdict(set))
for r in cohort_rows:
 cohorts_by_gap[r['gap_event_id']][r['source_timestamp']].add(r['cohort'])
 labels_by_gap[r['gap_event_id']][r['source_timestamp']].add(r['existing_review_label'])
with matched_csv.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(cohort_rows[0]) if cohort_rows else ['gap_event_id']);w.writeheader();w.writerows(cohort_rows)
summary_rows=[]
for g in gaps:
 by_ts=cohorts_by_gap[g['gap_event_id']]
 cand=[t for t in by_ts if g['prev_ts']<t<g['target_ts']]
 ongrid=[t for t in cand if g['delta_seconds']%300==0 and g['prev_interval']==5 and g['current_interval']==5 and (t-g['prev_ts'])%300==0]
 summary_rows.append({'gap_event_id':g['gap_event_id'],'utc_year':g['utc_year'],'prev_ts':g['prev_ts'],
  'target_ts':g['target_ts'],'delta_seconds':g['delta_seconds'],'reviewed_source_timestamp_count':len(cand),
  'reviewed_source_expected_5m_slot_count':len(ongrid),'reviewed_source_offgrid_count':len(cand)-len(ongrid),
  'reviewed_source_cohorts':';'.join(sorted({c for cs in by_ts.values() for c in cs})),
  'evidence_state':'HAS_MATCH_IN_SELECTED_REVIEW_EXPORTS' if cand else 'NO_MATCH_IN_SELECTED_REVIEW_EXPORTS_NOT_NO_SOURCE'})
with pergap_csv.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(summary_rows[0]));w.writeheader();w.writerows(summary_rows)

yearly=defaultdict(Counter)
input_counts={name:0 for name,_,_ in INPUTS}
for r in summary_rows:
 y=yearly[r['utc_year']];y['gap_events']+=1;y['events_with_reviewed_source_rows']+=r['reviewed_source_timestamp_count']>0
 y['unique_reviewed_source_timestamps_in_gaps']+=r['reviewed_source_timestamp_count']
 y['expected_5m_slot_timestamps']+=r['reviewed_source_expected_5m_slot_count']
 y['offgrid_timestamps']+=r['reviewed_source_offgrid_count']
unique_timestamps={r['source_timestamp'] for r in cohort_rows}
unique_on_grid={(r['source_timestamp']) for r in cohort_rows if r['expected_5m_slot_within_gap']==1}
for name,_,_ in INPUTS:
 input_counts[name]=sum(r['cohort']==name for r in cohort_rows)
payload={'schema':'b5-gap-reviewed-source-cohort-overlay-v1','method':'Offline interval join of existing gap-event catalog to five existing row-level source-only review exports. No database access.','gap_event_count':len(gaps),'review_export_row_count':sum(input_counts.values()),'input_rows_scanned_by_export':input_row_counts,'matched_rows_by_export':input_counts,
 'matched_source_rows':len(cohort_rows),'unique_source_timestamps_inside_catalog_gaps':len(unique_timestamps),
 'unique_expected_5m_slot_timestamps_inside_catalog_gaps':len(unique_on_grid),
 'unique_offgrid_timestamps_inside_catalog_gaps':len(unique_timestamps-unique_on_grid),
 'gap_events_with_any_selected_reviewed_source_timestamp':sum(r['reviewed_source_timestamp_count']>0 for r in summary_rows),
 'gap_events_without_selected_export_match':'unclassified by this join; must not be called no-source',
 'input_files':[x[1] for x in INPUTS]+[str(GAP.relative_to(R))],
 'output_files':[str(pergap_csv.relative_to(R)),str(matched_csv.relative_to(R))],
 'by_year':{str(y):dict(c) for y,c in sorted(yearly.items())},
 'limitations':['The five input exports cover selected source-only cohorts, not all 207,182 source-only timestamps or all six archives.','A source timestamp within a gap is not proof that it belongs to the expected physical measurement schedule.','The 5-minute-grid flag is only a timestamp alignment screen when both endpoint intervals equal 5; it does not prove source validity.','No-match in selected exports is not evidence of source absence.','Existing review labels are carried forward; this analysis does not approve or create corrections.','Q1 2018 and year 2021 were not reanalyzed.']}
out_json.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'BUILT','gap_events':len(gaps),'input_review_rows':sum(1 for _ in cohort_rows),'unique_candidate_timestamps':len(unique_timestamps),'unique_expected_5m_slot_timestamps':len(unique_on_grid),'gap_events_with_selected_source':payload['gap_events_with_any_selected_reviewed_source_timestamp']}))
