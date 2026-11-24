#!/usr/bin/env python3
"""Create an uncalibrated ERA5 hourly regional layer with CHMI daily-support checks."""
import argparse,csv,gzip,hashlib,json,math,random,statistics
from collections import defaultdict
from datetime import datetime,timezone,timedelta
from pathlib import Path
from backtest_pressure_reconstruction_v3 import load_era5,hypsometric_transport,SITE

def metrics(errors):
 if not errors:return {'n':0,'mae_hpa':None,'median_bias_hpa':None,'p95_abs_hpa':None}
 a=sorted(abs(x) for x in errors);p=.95*(len(a)-1);i=int(p)
 return {'n':len(errors),'mae_hpa':statistics.fmean(abs(x) for x in errors),'median_bias_hpa':statistics.median(errors),'p95_abs_hpa':a[i]+(a[min(i+1,len(a)-1)]-a[i])*(p-i)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--era5',type=Path,required=True);ap.add_argument('--daily-manifest',type=Path,required=True);ap.add_argument('--daily-csv',type=Path,required=True);ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args()
 era,elev,ehash=load_era5(a.era5);manifest=json.loads(a.daily_manifest.read_text());item=next(x for x in manifest['files'] if x['station_id']=='0-20000-0-11774')
 if hashlib.sha256(a.daily_csv.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('daily CHMI SHA mismatch')
 daily={}
 with a.daily_csv.open(encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   if r['STATION']!='0-20000-0-11774' or r['ELEMENT']!='P' or r['TIMEFUNC']!='AVG' or r['QUALITY'] not in ('0','0.0') or not r['VALUE']:continue
   daily[r['DT'][:10]]=float(r['VALUE'])
 nearest=era['loucka_era5_nearest'];hours=[];byday=defaultdict(list)
 for t,(p,temp) in sorted(nearest.items()):
  d=datetime.fromtimestamp(t,timezone.utc)
  if not 2009<=d.year<=2017:continue
  target=hypsometric_transport(p,temp,elev['loucka_era5_nearest'],SITE)
  hours.append((t,p,temp,target));byday[d.strftime('%Y-%m-%d')].append((p,temp,target))
 out=a.out_dir;out.mkdir(parents=True,exist_ok=True)
 hourly_path=out/'era5-loucka-physical-hourly-2009-2017-unapproved.csv.gz'
 with gzip.open(hourly_path,'wt',newline='') as f:
  w=csv.writer(f);w.writerow(['dateTime_utc','era5_surface_pressure_hpa_grid','era5_temperature_2m_c','physical_pressure_hpa_425m','support_seconds','classification','approval_status','method']);w.writerows([[*r,3600,'ESTIMATED','UNAPPROVED','ERA5 surface pressure transported from grid elevation using contemporaneous ERA5 2m temperature'] for r in hours])
 comparisons=[];monthly=defaultdict(list);annual=defaultdict(list);daily_series=[]
 for day,vals in sorted(byday.items()):
  if day not in daily or len(vals)!=24:continue
  era_day=statistics.fmean(x[2] for x in vals);mean_temp=statistics.fmean(x[1] for x in vals)
  chmi_at_site=hypsometric_transport(daily[day],mean_temp,222.25,SITE);err=era_day-chmi_at_site
  date=datetime.fromisoformat(day).replace(tzinfo=timezone.utc);key=f'{date.year:04d}-{date.month:02d}'
  rec={'utc_date_label':day,'support':'CHMI daily TIMEFUNC=AVG, quality=0; compared with 24-hour UTC ERA5 mean on same date label','era5_valid_hours':len(vals),'era5_daily_mean_pressure_hpa_at_425m':era_day,'era5_daily_mean_temperature_c':mean_temp,'chmi_daily_mean_pressure_hpa_holesov':daily[day],'chmi_daily_mean_transferred_to_425m_hpa':chmi_at_site,'era5_minus_chmi_hpa':err}
  comparisons.append(rec);monthly[key].append(err);annual[str(date.year)].append(err);daily_series.append(rec)
 # Month-block uncertainty describes daily-mean comparisons only.
 rng=random.Random(26024);monthly_blocks=defaultdict(list)
 for r in comparisons:monthly_blocks[r['utc_date_label'][:7]].append(abs(r['era5_minus_chmi_hpa']))
 bootstrap=[]
 if len(monthly_blocks)>=3:
  keys=sorted(monthly_blocks)
  for _ in range(1000):bootstrap.append(statistics.fmean(v for k in [rng.choice(keys) for _ in keys] for v in monthly_blocks[k]))
 ci=[sorted(bootstrap)[25],sorted(bootstrap)[974]] if bootstrap else [None,None]
 expected={str(y):366 if y%4==0 and (y%100!=0 or y%400==0) else 365 for y in range(2009,2018)}
 annual_result={}
 for y in range(2009,2018):
  es=annual[str(y)];coverage=len(es)/expected[str(y)];m=metrics(es)
  # Strict daily-support screen: at least 80% year-day coverage and unchanged V2 error bounds.
  passed=(coverage>=.8 and m['n']>=250 and m['mae_hpa']<=2.0 and m['p95_abs_hpa']<=4.0 and abs(m['median_bias_hpa'])<=1.5)
  annual_result[str(y)]={'expected_days':expected[str(y)],'matched_quality_zero_daily_values_with_complete_era5_days':len(es),'daily_coverage':coverage,**m,'regional_daily_context_screen_pass':passed,'hourly_accuracy_validated':False,'decision':'GO_DAILY_REGIONAL_CONTEXT_ONLY' if passed else 'NO_GO_DAILY_CONTEXT_SCREEN'}
 # Daily/monthly descriptive statistics, all aligned to CHMI UTC date labels.
 month_stats={k:{'n_days':len(v),**metrics(v),'era5_mean_hpa':statistics.fmean(r['era5_daily_mean_pressure_hpa_at_425m'] for r in comparisons if r['utc_date_label'][:7]==k),'chmi_transferred_mean_hpa':statistics.fmean(r['chmi_daily_mean_transferred_to_425m_hpa'] for r in comparisons if r['utc_date_label'][:7]==k)} for k,v in sorted(monthly.items())}
 checks={'hourly_rows':len(hours),'unique_hourly_timestamps':len({x[0] for x in hours}),'duplicate_hourly_timestamps':len(hours)-len({x[0] for x in hours}),'max_adjacent_hourly_step_hpa':max((abs(hours[i][3]-hours[i-1][3]) for i in range(1,len(hours)) if hours[i][0]-hours[i-1][0]==3600),default=None),'daily_matched_rows':len(comparisons),'monthly_rows':len(month_stats),'daily_window_semantics':'same UTC date label; CHMI daily source is TIMEFUNC=AVG with explicit date label, not a point-time match','daily_hourly_completeness':'exactly 24 ERA5 hourly records required'}
 result={'schema':'era5-hourly-physical-daily-check-v1','state':'ESTIMATED_UNAPPROVED_NO_APPLY','period':'2009-01-01..2017-12-31','hourly_rows':len(hours),'hourly_series_sha256':hashlib.sha256(hourly_path.read_bytes()).hexdigest(),'era5_manifest_sha256':ehash,'chmi_daily_manifest_sha256':hashlib.sha256(a.daily_manifest.read_bytes()).hexdigest(),'chmi_daily_file_sha256':item['sha256'],'chmi_station':'0-20000-0-11774 Holešov, 222.25m','era5_grid_elevation_m':elev['loucka_era5_nearest'],'target_elevation_m':SITE,'transport':'no fitted offset: each ERA5 hourly surface pressure transported grid elevation to 425m with same-hour ERA5 2m temperature','daily_method':'CHMI P TIMEFUNC=AVG quality zero by UTC date label, transported from 222.25m using mean ERA5 daily 2m temperature; compare with mean of all 24 transported ERA5 hours on same date label','daily_gate':{'min_coverage':.8,'minimum_days':250,'max_mae_hpa':2.0,'max_p95_abs_hpa':4.0,'max_abs_median_bias_hpa':1.5,'source':'unchanged V2 regional error limits; daily support only'},'annual_daily_checks':annual_result,'monthly_daily_statistics':month_stats,'daily_uncertainty_mae_95ci_month_block_hpa':ci,'continuity_and_coverage_checks':checks,'hourly_decision':'Daily consistency cannot certify hourly departures. Keep hourly ERA5 only as a separate unapproved regional reanalysis layer; NO-GO to substitute for local 5-minute history or label it hourly observation truth.','limitations':['Daily check is date-label support, not a timestamp-level validation; timezone/day-window metadata is preserved.','ERA5 may assimilate CHMI observations.','No fitting to biased local pressure field; daily aggregate comparison is not independent if ERA5 assimilated the same station.','All hourly values remain UNAPPROVED.']}
 (out/'era5-daily-check-2009-2017.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 with (out/'era5-chmi-daily-comparison-2009-2017.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(comparisons[0]) if comparisons else ['utc_date_label']);w.writeheader();w.writerows(comparisons)
 print(json.dumps({'hourly_rows':len(hours),'daily_matched':len(comparisons),'annual':{y:{k:v for k,v in x.items() if k in ('daily_coverage','mae_hpa','median_bias_hpa','p95_abs_hpa','regional_daily_context_screen_pass')} for y,x in annual_result.items()},'hourly_series_sha256':result['hourly_series_sha256']}))
if __name__=='__main__':main()
