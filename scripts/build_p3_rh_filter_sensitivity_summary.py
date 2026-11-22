#!/usr/bin/env python3
"""Build deterministic P3 RH threshold sensitivity summary from saved SELECT results."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
raw=json.loads((r/'data/p3_no_rh_filter_holdout_20m.json').read_text())
old=json.loads((r/'proposals/estimated_short_temperature_gaps_v2/conditional_holdout_2019_2020.json').read_text())
meta=json.loads((r/'proposals/estimated_short_temperature_gaps_v2/candidate_metadata.json').read_text())
def q(rows,pct):
 total=sum(int(x[1]) for x in rows);goal=total*pct;cum=0
 for bucket,n in sorted(rows):
  cum+=int(n)
  if cum>=goal:return round(float(bucket)+.1,1)
out={}
for yr in (2019,2020):
 before=next(x for x in old['histograms'] if x['gap_minutes']==20)['years'][str(yr)]
 old_ext=next(x for x in old['extrema'][2]['rows'] if x['utc_year']==yr)
 new_rows=[x for x in raw['histogram'] if x['utc_year']==yr]
 new_ext=next(x for x in raw['extrema'] if x['utc_year']==yr)
 new_hist=[(x['err_bucket'],x['point_n']) for x in new_rows]
 n_ep=int(new_ext['episode_n'])
 out[str(yr)]={'episodes_with_rh_filter':before['episodes'],'episodes_without_rh_filter':n_ep,'added_episodes':n_ep-before['episodes'],'relative_increase_pct':round(100*(n_ep-before['episodes'])/before['episodes'],1),'points_without_rh_filter':sum(int(x[1]) for x in new_hist),'quantile_upper_edge_c':{'with_rh_filter':{str(k):q(before['histogram'],k) for k in (.5,.9,.95)},'without_rh_filter':{str(k):q(new_hist,k) for k in (.5,.9,.95)}},'maximum_point_error_bucket_c':max(float(x['err_bucket']) for x in new_rows),'maximum_hidden_max_error_c':float(new_ext['max_hidden_max_error_c']),'maximum_hidden_min_error_c':float(new_ext['max_hidden_min_error_c']),'with_rh_filter_extrema':{'episodes_hidden_max':int(old_ext['episodes_hidden_max']),'episodes_hidden_min':int(old_ext['episodes_hidden_min']),'max_hidden_max_error_c':old_ext['max_hidden_max_error_c'],'max_hidden_min_error_c':old_ext['max_hidden_min_error_c']}}
trio=[]
for ts in (1556184600,1556184900,1556185200):
 m=next(x for x in meta if x['timestamp']==ts)
 trio.append({'timestamp':ts,'outTemp_estimate_c':m['interpolation_value_c'],'left_rh_estimated_pct':m['context']['left']['rh'],'right_rh_estimated_pct':m['context']['right']['rh'],'minimum_margin_to_RH_filter_boundary_pp':24.8,'passes_non_RH_numeric_gates':all(v for k,v in m['gates'].items() if k not in ('rh20_95','endpoint_filter_input_history_clear') and isinstance(v,bool))})
total_before=sum(x['episodes_with_rh_filter'] for x in out.values());total_after=sum(x['episodes_without_rh_filter'] for x in out.values())
result={'scope':'20-minute hourly-anchor masked-block holdout, 2019-2020','comparison':'Same P3 method; omit only endpoint RH 20-95 screen','yearly':out,'total':{'episodes_with_RH_filter':total_before,'episodes_without_RH_filter':total_after,'added_episodes':total_after-total_before,'relative_increase_pct':round(100*(total_after-total_before)/total_before,1),'points_without_RH_filter':sum(x['points_without_rh_filter'] for x in out.values())},'candidate_trio':trio,'disposition':{'RESTORED':0,'ESTIMATED':0,'REVIEW_REQUIRED':3,'MISSING':0},'interpretation':['All three actual cases pass their original RH numerical screen and all other numeric gates; omitting RH does not change their eligibility.','Applied endpoint RH error is not calibrated; threshold margin is not an uncertainty bound.','No-RH holdout per-year quantile upper bins are similar or lower, but the 2019 maximum point error and hidden-minimum overshoot are 3.2 C; no quantile is a per-target interval.','No candidate package filter or method was changed.'],'db_writes':0}
(r/'data/p3_rh_filter_sensitivity_summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print('summary built; episodes',total_before,'->',total_after,'; disposition remains review-required for all 3')
