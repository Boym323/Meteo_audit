#!/usr/bin/env python3
"""Check P3 RH-filter sensitivity evidence and preserve the held trio disposition."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
d=json.loads((r/'data/p3_rh_filter_sensitivity_summary.json').read_text())
assert d['total']=={'episodes_with_RH_filter':4484,'episodes_without_RH_filter':5447,'added_episodes':963,'relative_increase_pct':21.5,'points_without_RH_filter':16341}
assert d['yearly']['2019']['quantile_upper_edge_c']=={'with_rh_filter':{'0.5':0.1,'0.9':0.3,'0.95':0.4},'without_rh_filter':{'0.5':0.1,'0.9':0.3,'0.95':0.4}}
assert d['yearly']['2020']['quantile_upper_edge_c']=={'with_rh_filter':{'0.5':0.1,'0.9':0.4,'0.95':0.5},'without_rh_filter':{'0.5':0.1,'0.9':0.3,'0.95':0.4}}
assert d['yearly']['2019']['maximum_point_error_bucket_c']==3.2
assert d['yearly']['2019']['maximum_hidden_min_error_c']==3.2
assert len(d['candidate_trio'])==3 and all(x['minimum_margin_to_RH_filter_boundary_pp']==24.8 for x in d['candidate_trio'])
assert d['disposition']=={'RESTORED':0,'ESTIMATED':0,'REVIEW_REQUIRED':3,'MISSING':0}
assert d['db_writes']==0
for f in ['sql/readonly/p3_conditional_holdout_20m_no_rh_filter_sensitivity.sql','sql/readonly/p3_extrema_holdout_20m_no_rh_filter_sensitivity.sql','reports/2026-11-13-p3-rh-filter-sensitivity-review.md']:
 assert (r/f).is_file()
print('PASS: 20-minute no-RH sensitivity counts, quantiles, extrema, candidate gate margins and held disposition')
