#!/usr/bin/env python3
"""Build a standalone V3 pressure shadow series; never writes SQL."""
import argparse,csv,gzip,hashlib,json
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from backtest_pressure_reconstruction_v3 import local_predict,metrics

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--model',type=Path,required=True);ap.add_argument('--backtest',type=Path,required=True);ap.add_argument('--qc-spikes',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args()
 model=json.loads(a.model.read_text())['parameters'];model={'offset_hpa':model['offset_hpa'],'temperature_slope_hpa_per_c':model['temperature_slope_hpa_per_c'],'temperature_center_c':model['temperature_center_c']}
 bt=json.loads(a.backtest.read_text());local_cal=bt['calibration']['local_barometer_v1'];spikes=set()
 with a.qc_spikes.open(newline='') as f:
  for r in csv.DictReader(f):
   try:spikes.add(int(r.get('dateTime_utc') or r.get('dateTime')))
   except (ValueError,TypeError):pass
 a.out_dir.mkdir(parents=True,exist_ok=True);rows=[]
 with a.archive.open(newline='') as f:
  for raw in csv.DictReader(f):
   t=int(raw['dateTime_utc']); y=datetime.fromtimestamp(t,timezone.utc).year
   rows.append((t,raw))
 rows.sort(key=lambda x:x[0]);nullruns={};i=0
 while i<len(rows):
  t,r=rows[i]
  if r['pressure_hpa']!='':i+=1;continue
  j=i+1
  while j<len(rows) and rows[j][0]==rows[j-1][0]+300 and rows[j][1]['pressure_hpa']=='' :j+=1
  length=(j-i)*300
  for k in range(i,j):nullruns[rows[k][0]]=length
  i=j
 annual={};counts=defaultdict(int);candidates=[]
 q1a=int(datetime(2018,1,1,tzinfo=timezone.utc).timestamp());q1b=int(datetime(2018,4,1,tzinfo=timezone.utc).timestamp())
 # Conservative epoch-specific empirical error: measured backtest by year for long-term rows,
 # synthetic holdout gap errors for 2023-25 by nearest tested gap duration.
 yearerr={}
 for y in range(2009,2027):
  es=[]
  for t,r in rows:
   if datetime.fromtimestamp(t,timezone.utc).year!=y or not r['pressure_hpa'] or not r['barometer_hpa'] or not r['outTemp_c']:continue
   rr={'barometer_hpa':float(r['barometer_hpa']),'outTemp_c':float(r['outTemp_c'])};es.append(local_predict(rr,model)-float(r['pressure_hpa']))
  yearerr[y]=metrics(es)
 gaps=defaultdict(list)
 for key,m in bt['holdout_gap_metrics'].items():
  modelname,dur,year,season,regime=key.split('|')
  if modelname=='local_barometer_v1':gaps[int(dur)].append(m['p95_abs_hpa'])
 def gap_unc(sec):
  choices=sorted(gaps)
  if not choices:return None
  d=min(choices,key=lambda z:abs(z-sec));return max(gaps[d])
 with (a.out_dir/'pressure-reconstruction-v3-candidates-unapproved.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['dateTime_utc','original_pressure_hpa','estimated_pressure_hpa','classification','approval_status','method','gap_duration_seconds','empirical_uncertainty_p95_hpa','source_barometer_hpa','source_outTemp_c','model_sha256','source_archive_sha256','reason'])
  for t,r in rows:
   y=datetime.fromtimestamp(t,timezone.utc).year;counts[(y,'archive')]+=1
   if r['pressure_hpa']!='':counts[(y,'MEASURED')]+=1;continue
   if q1a<=t<q1b:counts[(y,'PROTECTED_Q1_2018')]+=1;continue
   b=None if r['barometer_hpa']=='' else float(r['barometer_hpa']);temp=None if r['outTemp_c']=='' else float(r['outTemp_c'])
   if t in spikes or b is None or temp is None or not 930<=b<=1080 or not -40<=temp<=45:
    counts[(y,'UNRESOLVED')]+=1;continue
   pred=local_predict({'barometer_hpa':b,'outTemp_c':temp},model)+local_cal['offset_hpa']+local_cal['temperature_slope_hpa_per_c']*(temp-local_cal['temperature_center_c'])
   if not 850<=pred<=1050:counts[(y,'UNRESOLVED')]+=1;continue
   gd=nullruns.get(t,300);unc=gap_unc(gd)
   if y<2020:unc=yearerr.get(y,{}).get('p95_abs_hpa')
   w.writerow([t,'',f'{pred:.4f}','ESTIMATED','UNAPPROVED','frozen_local_barometer_v1+2020-2021_residual_calibration',gd,'' if unc is None else f'{unc:.4f}',f'{b:.4f}',f'{temp:.3f}',hashlib.sha256(a.model.read_bytes()).hexdigest(),bt['archive_sha256'],'masked-pressure backtest; local reference transfer failed holdout gate; point estimate is non-approved'])
   counts[(y,'ESTIMATED_UNAPPROVED')]+=1
 # one row per archive timestamp, preserving original measured value and distinguishing estimates/unresolved/protected
 cat=a.out_dir/'pressure-reconstruction-v3-candidates-unapproved.csv';cand={}
 with cat.open(newline='') as f:
  for r in csv.DictReader(f):cand[int(r['dateTime_utc'])]=r
 series=a.out_dir/'pressure-series-unified-v3.csv.gz'
 with gzip.open(series,'wt',newline='') as f:
  w=csv.writer(f);w.writerow(['dateTime_utc','field','original_value_hpa','series_value_hpa','classification','approval_status','method','empirical_uncertainty_p95_hpa'])
  for t,r in rows:
   original=r['pressure_hpa'];c=cand.get(t)
   if original!='':w.writerow([t,'pressure',original,original,'MEASURED','SOURCE','archive.pressure',''])
   elif q1a<=t<q1b:w.writerow([t,'pressure','','','PROTECTED_Q1_2018','UNAPPROVED','',''])
   elif c:w.writerow([t,'pressure','',c['estimated_pressure_hpa'],'ESTIMATED','UNAPPROVED',c['method'],c['empirical_uncertainty_p95_hpa']])
   else:w.writerow([t,'pressure','','','UNRESOLVED','UNAPPROVED','',''])
 annualout=[]
 for y in range(2009,2027):annualout.append({'year':y,'archive_rows':counts[(y,'archive')],'measured':counts[(y,'MEASURED')],'estimated_unapproved':counts[(y,'ESTIMATED_UNAPPROVED')],'unresolved':counts[(y,'UNRESOLVED')],'protected_q1_2018':counts[(y,'PROTECTED_Q1_2018')],'measured_control_v1_metrics':yearerr[y]})
 manifest={'schema':'pressure-reconstruction-v3-unified-manifest','state':'ESTIMATES_UNAPPROVED_NO_APPLY','rows':len(rows),'candidate_rows':sum(counts[(y,'ESTIMATED_UNAPPROVED')] for y in range(2009,2027)),'annual':annualout,'source_archive_sha256':bt['archive_sha256'],'model_sha256':hashlib.sha256(a.model.read_bytes()).hexdigest(),'residual_calibration_2020_2021':local_cal,'backtest_sha256':hashlib.sha256(a.backtest.read_bytes()).hexdigest(),'candidate_csv_sha256':hashlib.sha256(cat.read_bytes()).hexdigest(),'candidate_csv_bytes':cat.stat().st_size,'unified_series_sha256':hashlib.sha256(series.read_bytes()).hexdigest(),'unified_series_bytes':series.stat().st_size,'protected_q1_2018':'no estimates created','v1_v2':'immutable source artifacts; not modified','period':'2009-01-01 through 2026-11-24 UTC; 2026 is an incomplete year','limitations':['V1 is a derived local pressure/barometer-temperature relation; holdout is a masked test against original archive pressure, not an independently calibrated reference sensor.','CHMI and ERA5 pressure transfers showed epoch-dependent large biases and are excluded from automatic V3 candidates.','All candidate values remain ESTIMATED/UNAPPROVED.']}
 (a.out_dir/'manifest-v3.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':'V3_SERIES_BUILT','rows':len(rows),'candidates':manifest['candidate_rows'],'series_sha256':manifest['unified_series_sha256'],'candidate_sha256':manifest['candidate_csv_sha256']}))
if __name__=='__main__':main()
