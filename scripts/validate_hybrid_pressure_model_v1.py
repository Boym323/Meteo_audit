#!/usr/bin/env python3
"""Bounded 2018 Q4 holdout test of locally forecast increments on CHMI absolute anchors."""
import argparse,csv,hashlib,json,statistics
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from backtest_pressure_reconstruction_v3 import load_local,load_chmi,load_era5,load_spikes,interp,hypsometric_transport,SITE,HEIGHT

def metrics(x):
 if not x:return {'n':0,'mae_hpa':None,'median_bias_hpa':None,'p95_abs_hpa':None}
 es=[v for v in x];a=sorted(abs(v) for v in es);i=int(.95*(len(a)-1));f=.95*(len(a)-1)-i
 return {'n':len(es),'mae_hpa':statistics.fmean(abs(v) for v in es),'median_bias_hpa':statistics.median(es),'p95_abs_hpa':a[i]+(a[min(i+1,len(a)-1)]-a[i])*f}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--chmi10',type=Path,required=True);ap.add_argument('--era5',type=Path,required=True);ap.add_argument('--model',type=Path,required=True);ap.add_argument('--qc-spikes',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 rows,_=load_local(a.archive);chmi,chhash=load_chmi(a.chmi10);era,elev,ehash=load_era5(a.era5);spikes,qhash=load_spikes(a.qc_spikes);model=json.loads(a.model.read_text())['training_domain']
 def site_ref(t):
  r=rows.get(t);temp=r['outTemp_c'] if r else None
  if temp is None or not -40<=temp<=45:
   v=era['loucka_era5_nearest'].get(t);temp=v[1] if v else None
  if temp is None or not -40<=temp<=45:return None
  vals=[]
  for s in ('H','M'):
   p=interp(chmi[s],t,1200)
   if p is None:return None
   vals.append(hypsometric_transport(p,temp,HEIGHT[s],SITE))
  return statistics.fmean(vals)
 def control(t):
  r=rows.get(t)
  if not r or t in spikes or r['usUnits']!=16 or r['interval']!=5 or t%300:return False
  p,b,temp=r['pressure_hpa'],r['barometer_hpa'],r['outTemp_c']
  return (p is not None and 900<=p<=1050 and b is not None and 930<=b<=1080 and temp is not None and -40<=temp<=45 and model['barometer_hpa'][0]<=b<=model['barometer_hpa'][1] and model['outTemp_c'][0]<=temp<=model['outTemp_c'][1])
 # Fixed formula, no coefficient fit: Q4 2018 is the untouched contiguous time holdout.
 start=int(datetime(2018,10,1,tzinfo=timezone.utc).timestamp());end=int(datetime(2019,1,1,tzinfo=timezone.utc).timestamp())
 base_errors=[];hybrid_errors=[];details=[];monthly=defaultdict(lambda:{'base':[],'hybrid':[],'anomaly':[],'jumps':[]});daily=defaultdict(lambda:{'base':[],'hybrid':[],'anomaly':[]});absolute_level_residuals=[]
 for t,r in rows.items():
  if not start<=t<end or t%600!=300 or not control(t):continue
  if not all(control(x) for x in (t-300,t-600)):continue
  # Require exact CHMI ten-minute endpoints for this validation sample.
  if any(interp(chmi[s],u,0) is None for s in ('H','M') for u in (t-900,t-300,t+300)):continue
  p0=site_ref(t-300);p_10=site_ref(t-900);pt=site_ref(t);pnext=site_ref(t+300)
  if None in (p0,p_10,pt,pnext):continue
  local0=rows[t-300]['pressure_hpa'];localprev=rows[t-600]['pressure_hpa'];truth=rows[t]['pressure_hpa']-local0
  prev_ref_delta=p0-(p_10+p0)/2
  # Forecast only the recent local deviation from regional tendency, then add it to the CHMI level.
  local_prev_delta=local0-localprev
  anomaly=local_prev_delta-prev_ref_delta
  baseline_increment=pt-p0;hybrid_increment=baseline_increment+anomaly
  eb=baseline_increment-truth;eh=hybrid_increment-truth
  base_errors.append(eb);hybrid_errors.append(eh);absolute_level_residuals.append(pt-rows[t]['pressure_hpa'])
  month=datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m');day=datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d')
  monthly[month]['base'].append(eb);monthly[month]['hybrid'].append(eh);monthly[month]['anomaly'].append(anomaly)
  # Hybrid at midpoint is bounded by independently anchored reference endpoints;
  # record both adjacent 5-minute steps against the simple continuous baseline.
  hlevel=pt+anomaly
  step0=hlevel-p0;step1=pnext-hlevel;simple0=pt-p0;simple1=pnext-pt
  jump=max(abs(step0),abs(step1));baseline=max(abs(simple0),abs(simple1));monthly[month]['jumps'].append(jump)
  daily[day]['base'].append(eb);daily[day]['hybrid'].append(eh);daily[day]['anomaly'].append(anomaly)
  details.append({'dateTime_utc':t,'baseline_increment_hpa':baseline_increment,'hybrid_increment_hpa':hybrid_increment,'observed_local_increment_hpa':truth,'baseline_increment_error_hpa':eb,'hybrid_increment_error_hpa':eh,'hybrid_anomaly_hpa':anomaly,'hybrid_adjacent_max_5min_step_hpa':jump,'baseline_adjacent_max_5min_step_hpa':baseline})
 month_result={k:{'target_count':len(v['base']),'baseline_increment_error':metrics(v['base']),'hybrid_increment_error':metrics(v['hybrid']),'median_abs_hybrid_anomaly_hpa':statistics.median(abs(x) for x in v['anomaly']),'max_hybrid_adjacent_5min_step_hpa':max(v['jumps'],default=None)} for k,v in sorted(monthly.items())}
 daily_result={k:{'target_count':len(v['base']),'baseline_increment_error':metrics(v['base']),'hybrid_increment_error':metrics(v['hybrid']),'mean_hybrid_anomaly_hpa':statistics.fmean(v['anomaly'])} for k,v in sorted(daily.items())}
 res={'schema':'hybrid-pressure-local-increment-chmi-level-holdout-v1','state':'ESTIMATED_UNAPPROVED_DIAGNOSTIC','formula':'CHMI_transferred_mean(t) + [local_P(t-5m)-local_P(t-10m) - (CHMI(t-5m)-CHMI(t-10m))]','fit_or_tuned_parameters':False,'split':'2018-10-01..2018-12-31 UTC untouched holdout; fixed model formula; no fitting','target':'local 5-minute pressure increment from t-5m to withheld t; absolute local pressure is known to drift and is not used as independent absolute truth','quality':'usUnits=16, 5min interval/cadence, pressure/barometer/temp ranges, frozen V1 domain and corrected QC spike exclusion; exact CHMI ten-minute anchors required','archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'chmi10_manifest_sha256':chhash,'era5_manifest_sha256':ehash,'qc_spikes_sha256':qhash,'n_targets':len(details),'baseline_simple_interpolation_increment_error':metrics(base_errors),'hybrid_increment_error':metrics(hybrid_errors),'hybrid_increment_mae_relative_change':(metrics(base_errors)['mae_hpa']-metrics(hybrid_errors)['mae_hpa'])/metrics(base_errors)['mae_hpa'] if base_errors else None,'absolute_level_difference_vs_local_archive':metrics(absolute_level_residuals),'monthly_holdout':month_result,'daily_holdout':daily_result,'continuity':{'max_hybrid_adjacent_5min_step_hpa':max((x['hybrid_adjacent_max_5min_step_hpa'] for x in details),default=None),'max_baseline_adjacent_5min_step_hpa':max((x['baseline_adjacent_max_5min_step_hpa'] for x in details),default=None),'max_abs_hybrid_anomaly_hpa':max((abs(x['hybrid_anomaly_hpa']) for x in details),default=None),'artificial_seam_rule':'hybrid correction is applied only between same 10-minute CHMI reference anchors; report measured adjacent steps; no coalescing with original archive field'},'interpretation':'Increment holdout assesses local high-frequency changes only. Absolute level remains CHMI-anchored; level difference against archived pressure is shown separately and is not an accuracy score. Empirical residual P95 is not a calibrated prediction interval.'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')
 with a.out.with_name('hybrid-holdout-2018-Q4.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(details[0]) if details else ['dateTime_utc']);w.writeheader();w.writerows(details)
 print(json.dumps({'n':res['n_targets'],'baseline':res['baseline_simple_interpolation_increment_error'],'hybrid':res['hybrid_increment_error'],'relative_mae_change':res['hybrid_increment_mae_relative_change'],'max_anomaly':res['continuity']['max_abs_hybrid_anomaly_hpa']}))
if __name__=='__main__':main()
