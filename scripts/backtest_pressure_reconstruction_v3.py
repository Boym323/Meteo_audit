#!/usr/bin/env python3
"""Blocked V3 pressure gap backtest. Read-only inputs; outputs remain unapproved."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,statistics
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
G,RD=9.80665,287.05
SITE=425.0
H_ID='0-20000-0-11774';M_ID='0-20000-0-11782'
HEIGHT={'H':222.25,'M':252.8}

def ts(s): return int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())
def q95(x):
 if not x:return None
 a=sorted(abs(y) for y in x);p=.95*(len(a)-1);i=int(p);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(p-i)
def metrics(x):
 if not x:return {'n':0,'mae_hpa':None,'bias_hpa':None,'p95_abs_hpa':None}
 return {'n':len(x),'mae_hpa':statistics.fmean(abs(y) for y in x),'bias_hpa':statistics.median(x),'p95_abs_hpa':q95(x)}
def interp(series,t,max_span):
 # series sorted integer seconds -> value; exact or bracketed linear estimate
 i=__import__('bisect').bisect_left(series[0],t)
 if i<len(series[0]) and series[0][i]==t:return series[1][i]
 if i==0 or i==len(series[0]):return None
 t0,t1=series[0][i-1],series[0][i]
 if t1-t0>max_span:return None
 f=(t-t0)/(t1-t0);return series[1][i-1]+f*(series[1][i]-series[1][i-1])
def load_local(path):
 rows={};byyear=defaultdict(int)
 with path.open(newline='') as f:
  for r in csv.DictReader(f):
   t=int(r['dateTime_utc']); row={k:(None if r[k]=='' else float(r[k])) for k in ('pressure_hpa','barometer_hpa','outTemp_c')};row['usUnits']=int(r['usUnits']);row['interval']=float(r['interval_min'] or 0);rows[t]=row;byyear[datetime.fromtimestamp(t,timezone.utc).year]+=1
 return rows,dict(byyear)
def load_chmi(root):
 # Verify each download against its response manifest.
 man=json.loads((root/'manifest.json').read_text());out={'H':{},'M':{}}
 for rec in man['records']:
  p=root/'raw'/rec['file'];raw=p.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=rec['sha256']:raise ValueError('CHMI10 SHA mismatch '+rec['file'])
  k='H' if '11774' in rec['file'] else 'M'
  with p.open(encoding='utf-8-sig',newline='') as f:
   for r in csv.DictReader(f):
    if r['QUALITY'] in ('0','0.0') and r['VALUE']:out[k][ts(r['DT'])]=float(r['VALUE'])
 return {k:(sorted(v),[v[t] for t in sorted(v)]) for k,v in out.items()},hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
def load_era5(root):
 man=json.loads((root/'manifest.json').read_text());out={};elev={}
 for rec in man['responses']:
  p=root/rec['file'];raw=p.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=rec['sha256']:raise ValueError('ERA5 SHA mismatch '+rec['file'])
  d=json.loads(raw);name=Path(rec['file']).stem.rsplit('-',1)[0];elev[name]=float(d['elevation']);h=d['hourly']
  out.setdefault(name,{}).update({ts(s+'Z'):(h['surface_pressure'][i],h['temperature_2m'][i]) for i,s in enumerate(h['time'])})
 return out,elev,hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
def era_predict(t,era,elev):
 h=t//3600*3600;t1=h+3600;a=era['loucka_era5_nearest'].get(h);b=era['loucka_era5_nearest'].get(t1)
 if not a or not b or any(v is None for v in (*a,*b)):return None
 f=(t-h)/3600;p=a[0]+f*(b[0]-a[0]);temp=a[1]+f*(b[1]-a[1]);return p*math.exp(G*(SITE-elev['loucka_era5_nearest'])/(RD*(temp+273.15)))
def chmi_predict(t,temp,chmi):
 out=[]
 for k in ('H','M'):
  p=interp(chmi[k],t,1200)
  if p is None:return None
  out.append(p*math.exp(G*(HEIGHT[k]-SITE)/(RD*(temp+273.15))))
 return statistics.fmean(out)
def local_predict(row,model):
 b,t=row['barometer_hpa'],row['outTemp_c']
 if b is None or t is None:return None
 raw=b*math.exp(-G*SITE/(RD*(t+273.15)))
 return raw+model['offset_hpa']+model['temperature_slope_hpa_per_c']*(t-model['temperature_center_c'])
def collect_predictions(rows,era,elev,chmi,v1):
 out={}
 for t,r in rows.items():
  if r['pressure_hpa'] is None or r['outTemp_c'] is None:continue
  vals={'chmi10':chmi_predict(t,r['outTemp_c'],chmi),'era5_hourly':era_predict(t,era,elev),'local_barometer_v1':local_predict(r,v1)}
  if vals['chmi10'] is not None and vals['era5_hourly'] is not None:vals['blend_chmi_era5']=.5*(vals['chmi10']+vals['era5_hourly'])
  if vals['chmi10'] is not None and vals['era5_hourly'] is not None and vals['local_barometer_v1'] is not None:vals['blend_all']=statistics.fmean((vals['chmi10'],vals['era5_hourly'],vals['local_barometer_v1']))
  out[t]=(r['pressure_hpa'],vals,r)
 return out
def fit_offset(preds,name,lo,hi):
 pairs=[(v[1][name],v[0],v[2]['outTemp_c']) for t,v in preds.items() if lo<=t<hi and v[1].get(name) is not None]
 if not pairs:return {'offset':0.,'temperature_slope':0.,'temperature_center':10.,'n':0}
 center=statistics.fmean(x[2] for x in pairs);offset=statistics.median(y-x for x,y,_ in pairs)
 # fixed, robust-free linear residual slope fitted on training only; clamp is deliberately absent
 den=sum((z-center)**2 for _,_,z in pairs);slope=sum((z-center)*(y-x-offset) for x,y,z in pairs)/den if den else 0.
 return {'offset_hpa':offset,'temperature_slope_hpa_per_c':slope,'temperature_center_c':center,'n':len(pairs)}
def seasonal(t):return ('DJF','MAM','JJA','SON')[(datetime.fromtimestamp(t,timezone.utc).month%12)//3]
def gap_backtest(rows,preds,calibration,years,seed=26024,blocks=40):
 # Sample non-overlapping candidate windows only inside fully represented five-minute local control spans.
 rng=random.Random(seed);durations=[300,1800,3600,21600,86400,259200,1209600,2419200];results={};selected=[]
 for y in years:
  times=sorted(t for t,v in preds.items() if datetime.fromtimestamp(t,timezone.utc).year==y and v[0] is not None)
  runs=[]; run=[]
  for t in times:
   if run and t!=run[-1]+300:runs.append(run);run=[]
   run.append(t)
  if run:runs.append(run)
  for secs in durations:
   npoints=secs//300
   choices=[]
   for run in runs:
    if len(run)>=npoints: choices.append((run,npoints))
   if not choices:continue
   # Draw from complete contiguous five-minute spans; cap the candidate pool
   # before checking overlap so multi-week windows stay bounded in runtime.
   chosen=[];attempts=0
   while len(chosen)<blocks and attempts<blocks*100:
    run,n= rng.choice(choices);idx=rng.randrange(0,len(run)-n+1);t=run[idx];attempts+=1
    if all(t+secs<=a or t>=a+length for a,length in chosen):chosen.append((t,secs))
   for start,length in chosen:
    targets=list(range(start,start+length,300))
    if any(t not in preds for t in targets):continue
    for t in targets:
     truth,base,row=preds[t]
     before=preds.get(t-300);after=preds.get(t+300)
     regime='fast_change' if before and after and abs(after[0]-before[0])>0.8 else 'stable'
     for name,p in base.items():
      if p is None:continue
      cal=calibration.get(name,{});est=p+cal.get('offset_hpa',0)+cal.get('temperature_slope_hpa_per_c',0)*(row['outTemp_c']-cal.get('temperature_center_c',10))
      selected.append({'year':y,'gap_s':length,'month':datetime.fromtimestamp(t,timezone.utc).month,'timestamp':t,'model':name,'error':est-truth,'regime':regime})
 bymonth_by_group=defaultdict(lambda:defaultdict(list))
 for x in selected:
  key=f"{x['model']}|{x['gap_s']}|{x['year']}|{seasonal(x['timestamp'])}|{x['regime']}"
  results.setdefault(key,[]).append(x['error'])
  bymonth=datetime.fromtimestamp(x['timestamp'],timezone.utc).strftime('%Y-%m')
  bymonth_by_group[key][bymonth].append(abs(x['error']))
 summary={k:metrics(v) for k,v in results.items()}
 # Uncertainty: month-block bootstrap CI, after one-pass grouping.
 for k in summary:
  bymonth=bymonth_by_group[k]
  if len(bymonth)>=3:
   rng2=random.Random(seed+int.from_bytes(hashlib.sha256(k.encode()).digest()[:4],'big'));maes=[]
   for _ in range(500):maes.append(statistics.fmean(v for m in [rng2.choice(list(bymonth)) for _ in bymonth] for v in bymonth[m]))
   summary[k]['mae_95ci_month_block_hpa']=[sorted(maes)[12],sorted(maes)[487]]
  else:summary[k]['mae_95ci_month_block_hpa']=None
 return summary,selected

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--chmi10',type=Path,required=True);ap.add_argument('--era5',type=Path,required=True);ap.add_argument('--model',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 rows,annual=load_local(a.archive);chmi,chhash=load_chmi(a.chmi10);era,elev,ehash=load_era5(a.era5);model=json.loads(a.model.read_text());v1=model['parameters']; v1={'offset_hpa':v1['offset_hpa'],'temperature_slope_hpa_per_c':v1['temperature_slope_hpa_per_c'],'temperature_center_c':v1['temperature_center_c']}; pred=collect_predictions(rows,era,elev,chmi,v1)
 train_lo=int(datetime(2020,1,1,tzinfo=timezone.utc).timestamp());train_hi=int(datetime(2022,1,1,tzinfo=timezone.utc).timestamp());select_hi=int(datetime(2023,1,1,tzinfo=timezone.utc).timestamp())
 names=('chmi10','era5_hourly','local_barometer_v1','blend_chmi_era5','blend_all');cal={n:fit_offset(pred,n,train_lo,train_hi) for n in names}
 val={n:metrics([pred[t][1][n]+cal[n]['offset_hpa']+cal[n]['temperature_slope_hpa_per_c']*(pred[t][2]['outTemp_c']-cal[n]['temperature_center_c'])-pred[t][0] for t in pred if train_hi<=t<select_hi and pred[t][1].get(n) is not None]) for n in names}
 eligible=[n for n in names if val[n]['n']>=1000];selected=min(eligible,key=lambda n:val[n]['mae_hpa']) if eligible else None
 hold={n:metrics([pred[t][1][n]+cal[n]['offset_hpa']+cal[n]['temperature_slope_hpa_per_c']*(pred[t][2]['outTemp_c']-cal[n]['temperature_center_c'])-pred[t][0] for t in pred if select_hi<=t<int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()) and pred[t][1].get(n) is not None]) for n in names}
 def paired_metrics(lo,hi):
  target=[t for t in pred if lo<=t<hi]
  common=[t for t in target if all(pred[t][1].get(n) is not None for n in names)]
  result={}
  for n in names:
   result[n]=metrics([pred[t][1][n]+cal[n]['offset_hpa']+cal[n]['temperature_slope_hpa_per_c']*(pred[t][2]['outTemp_c']-cal[n]['temperature_center_c'])-pred[t][0] for t in common])
   result[n]['n_all_targets']=len(target);result[n]['n_paired']=len(common);result[n]['coverage']=len(common)/len(target) if target else 0
  return result
 paired_validation=paired_metrics(train_hi,select_hi)
 paired_holdout=paired_metrics(select_hi,int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()))
 train_scores={n:metrics([pred[t][1][n]+cal[n]['offset_hpa']+cal[n]['temperature_slope_hpa_per_c']*(pred[t][2]['outTemp_c']-cal[n]['temperature_center_c'])-pred[t][0] for t in pred if train_lo<=t<train_hi and pred[t][1].get(n) is not None]) for n in names}
 gap,detail=gap_backtest(rows,pred,cal,[2023,2024,2025]);
 # Per-year input QC and frozen V1 checks, explicitly a derived-field masked
 # comparison rather than an independent calibration standard.
 year_errors=defaultdict(list); target_counts=defaultdict(int)
 for t,r in rows.items():
  y=datetime.fromtimestamp(t,timezone.utc).year
  if r['pressure_hpa'] is None or r['barometer_hpa'] is None or r['outTemp_c'] is None:continue
  if r['usUnits']!=16 or not 900<=r['pressure_hpa']<=1050 or not 930<=r['barometer_hpa']<=1080 or not -40<=r['outTemp_c']<=45:continue
  target_counts[y]+=1
  year_errors[y].append(local_predict(r,v1)-r['pressure_hpa'])
 annual_local={str(y):metrics(year_errors[y]) for y in sorted(year_errors)}
 annual_source_errors=defaultdict(lambda:defaultdict(list));annual_source_targets=defaultdict(int)
 for t,(truth,vals,row) in pred.items():
  year=datetime.fromtimestamp(t,timezone.utc).year;annual_source_targets[year]+=1
  for name,value in vals.items():
   if value is None:continue
   adj=cal.get(name,{})
   estimate=value+adj.get('offset_hpa',0)+adj.get('temperature_slope_hpa_per_c',0)*(row['outTemp_c']-adj.get('temperature_center_c',10))
   annual_source_errors[year][name].append(estimate-truth)
 annual_sources={str(y):{'n_all_local_pressure_controls':annual_source_targets[y],'models':{n:metrics(es) for n,es in annual_source_errors[y].items()}} for y in sorted(annual_source_targets)}
 hold_coverage={n:{'n_all_targets':sum(target_counts[y] for y in (2023,2024,2025)),'n_predictions':hold[n]['n'],'coverage':hold[n]['n']/sum(target_counts[y] for y in (2023,2024,2025)) if sum(target_counts[y] for y in (2023,2024,2025)) else 0} for n in names}
 result={'schema':'pressure-reconstruction-v3-backtest-v1','state':'READ_ONLY_DIAGNOSTIC_ESTIMATES_UNAPPROVED','archive_rows_by_year':annual,'archive_sha256':hashlib.sha256(a.archive.read_bytes()).hexdigest(),'chmi10_manifest_sha256':chhash,'era5_manifest_sha256':ehash,'mosnov_elevation_epoch':{'250.4_m':'through 2016-05-23T23:59Z','252.8_m':'from 2016-05-24T00:00Z','validation_2020_2025_used_m':252.8,'height_sensitivity_delta_2.4m_hpa_approx':0.3},'split':{'calibration':'2020-01-01..2021-12-31','model_selection':'2022 calendar year, minimum 1000 paired targets/model','untouched_holdout':'2023-01-01..2025-12-31','gap_backtest':'holdout only; synthetic contiguous masks, target is existing local pressure'},'calibration':cal,'selection_scores_2022':val,'selected_on_2022':selected,'paired_selection_scores_2022':paired_validation,'holdout_all_valid_controls':hold,'paired_holdout_scores':paired_holdout,'holdout_prediction_availability':hold_coverage,'training_fit_scores':train_scores,'frozen_local_v1_annual_masked_comparison':annual_local,'annual_competing_source_scores':annual_sources,'holdout_gap_metrics':gap,'gap_targets':len(detail),'gap_lengths_seconds':[300,1800,3600,21600,86400,259200,1209600,2419200],'quality_control':'Controls require pressure 900-1050 hPa, barometer 930-1080 hPa, outTemp -40..45 C and usUnits=16. Gap windows use contiguous five-minute records. Stable/fast_change split is based on absolute local pressure change across +/-5 minutes >0.8 hPa. Independent station/reanalysis sources are comparison references, not fully independent ground truth; ERA5 may assimilate CHMI.'}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':'BACKTEST_DONE','selected':selected,'holdout_n':{k:v['n'] for k,v in hold.items()},'gap_targets':len(detail),'gap_groups':len(gap),'report':str(a.out)}))
if __name__=='__main__':main()
