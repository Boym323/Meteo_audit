#!/usr/bin/env python3
"""Validate B5 offline overlap counts, interval containment, and conservative semantics."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/b5_gap_reviewed_source_cohort_overlay.json').read_text())
assert d['gap_event_count']==24523
assert d['input_rows_scanned_by_export']=={'source_only_2009_pilot':100,'source_only_2019_pilot':233,'source_only_2017_strict':10,'source_only_residual_strict':10,'source_only_2015_outtemp':2147}
assert d['matched_rows_by_export']=={'source_only_2009_pilot':100,'source_only_2019_pilot':233,'source_only_2017_strict':10,'source_only_residual_strict':10,'source_only_2015_outtemp':2143}
assert d['matched_source_rows']==2496 and d['unique_source_timestamps_inside_catalog_gaps']==2496
assert d['unique_expected_5m_slot_timestamps_inside_catalog_gaps']==1091
assert d['unique_offgrid_timestamps_inside_catalog_gaps']==1405
assert d['gap_events_with_any_selected_reviewed_source_timestamp']==213
with (R/'reports/2026-11-13-b5-gap-reviewed-source-overlap-row-evidence.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
assert len(rows)==2496
assert all(int(x['gap_prev_ts'])<int(x['source_timestamp'])<int(x['gap_target_ts']) for x in rows)
assert sum(int(x['expected_5m_slot_within_gap'])==1 for x in rows)==1091
with (R/'reports/2026-11-13-b5-gap-reviewed-source-overlap-by-event.csv').open(newline='',encoding='utf-8') as f: gaps=list(csv.DictReader(f))
assert len(gaps)==24523
assert sum(x['evidence_state']=='HAS_MATCH_IN_SELECTED_REVIEW_EXPORTS' for x in gaps)==213
assert all('NOT_NO_SOURCE' in x['evidence_state'] for x in gaps if x['reviewed_source_timestamp_count']=='0')
assert any('not evidence of source absence' in x for x in d['limitations'])
print(json.dumps({'status':'PASS','gap_events':len(gaps),'selected_input_rows':sum(d['input_rows_scanned_by_export'].values()),'matched_source_rows':len(rows),'unique_expected_5m_slot_rows':1091,'offgrid_rows':1405,'gap_events_with_selected_cohort_evidence':213,'no_match_is_not_no_source':True,'database_access':'NONE'}))
