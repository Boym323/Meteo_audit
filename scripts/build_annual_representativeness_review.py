#!/usr/bin/env python3
"""Summarize existing monthly B/E outputs for annual representativeness review."""
import csv,json,sqlite3,zlib,datetime as dt
from collections import defaultdict,Counter
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
TZ=ZoneInfo('Europe/Prague');DB=DATA/'historical_value_concordance.sqlite'
def rows(file):
 with (DATA/file).open(encoding='utf8',newline='') as f:return list(csv.DictReader(f))
def main():
 m=rows('STATISTICAL_VARIANTS_MONTHLY.csv');a=rows('STATISTICAL_VARIANTS_ANNUAL.csv');r=json.loads((DATA/'STATISTICAL_READINESS_CURRENT.json').read_text())
 vars={(x['period'],x['variable'],x['variant']):x for x in m}
 annual={(x['period'],x['variable'],x['variant']):x for x in a}
 screens={(x['period'],x['variable']):x for x in r['monthly']}
 years=('2010','2019','2023','2024');out=[]
 for year in years:
  months=[]
  for n in range(1,13):
   p=f'{year}-{n:02d}';b=vars.get((p,'outTemp','B_DOCUMENTED_SOURCE_AND_RECOVERY'));e=vars.get((p,'outTemp','E_FULL_CURRENT_ARCHIVE'));s=screens.get((p,'outTemp'))
   if not b or not e:continue
   months.append({'month':p,'expected_slots':int(b['expected_unique_slots']),'B_observed_slots':int(b['variant_on_grid_values']),'B_coverage':float(b['coverage'] or 0),'B_mean_C':float(b['mean_time_weighted']) if b['mean_time_weighted']!='' else None,'E_observed_slots':int(e['variant_on_grid_values']),'E_coverage':float(e['coverage'] or 0),'E_mean_C':float(e['mean_time_weighted']) if e['mean_time_weighted']!='' else None,'E_minus_B_C':float(e['mean_time_weighted'])-float(b['mean_time_weighted']) if b['mean_time_weighted']!='' and e['mean_time_weighted']!='' else None,'max_gap_seconds':int(s['max_observed_or_edge_gap_seconds']) if s else None,'days_passing_mean_rule':int(s['days_passing_mean_rule']) if s else None,'days_required_mean_rule':int(s['days_required_mean_rule']) if s else None})
  annual_b=annual.get((year,'outTemp','B_DOCUMENTED_SOURCE_AND_RECOVERY'));annual_e=annual.get((year,'outTemp','E_FULL_CURRENT_ARCHIVE'))
  out.append({'year':year,'B_annual_mean_C':float(annual_b['mean_time_weighted']),'E_annual_mean_C':float(annual_e['mean_time_weighted']),'B_coverage':float(annual_b['coverage']),'E_coverage':float(annual_e['coverage']),'months':months,'months_B_coverage_ge_95':sum(x['B_coverage']>=.95 for x in months),'months_with_mean_screen_days_pass':sum((x['days_passing_mean_rule'] or 0)>=(x['days_required_mean_rule'] or 10**9) for x in months),'worst_monthly_gap_seconds':max((x['max_gap_seconds'] or 0) for x in months),'worst_gap_month':max(months,key=lambda x:x['max_gap_seconds'] or 0)['month']})
 # Daily occurrence/coverage by B and E variants is calculated only for the four requested years.
 db=sqlite3.connect(f'file:{DB.resolve()}?mode=ro',uri=True)
 cadence=defaultdict(Counter);phase=defaultdict(Counter)
 lo=int(dt.datetime(2010,1,1,tzinfo=TZ).timestamp());hi=int(dt.datetime(2025,1,1,tzinfo=TZ).timestamp())
 for ts,interval in db.execute('SELECT dateTime,target_interval FROM timestamp_evidence WHERE dateTime>=? AND dateTime<?',(lo,hi)):
  local=dt.datetime.fromtimestamp(ts,TZ);year=local.strftime('%Y')
  if year not in years:continue
  step=int(interval or 0)*60
  if 0<step<=7200:cadence[(year,local.strftime('%Y-%m'))][int(interval)]+=1;phase[(year,local.strftime('%Y-%m'),int(interval))][int(ts%step)]+=1
 modes={};phases={}
 for key,c in cadence.items():
  mode=max(c,key=lambda x:(c[x],-x));modes[key]=mode;phases[key]=max(phase[(key[0],key[1],mode)],key=phase[(key[0],key[1],mode)].get)
 daily=defaultdict(lambda:{'E':0,'B':0})
 for ts,interval,blob in db.execute('SELECT dateTime,target_interval,comparison_zlib FROM timestamp_evidence WHERE dateTime>=? AND dateTime<?',(lo,hi)):
  local=dt.datetime.fromtimestamp(ts,TZ);year=local.strftime('%Y')
  if year not in years:continue
  month=local.strftime('%Y-%m');mode=modes.get((year,month));step=(mode or 5)*60;ph=phases.get((year,month),0);day=local.date();start=int(dt.datetime.combine(day,dt.time(),TZ).timestamp());first=start+((ph-start)%step)
  if ts<first or (ts-first)%step:continue
  value=json.loads(zlib.decompress(blob))['outTemp'];cat=value['provenance_category'];key=(year,day.isoformat())
  if value['target_value'] is not None:daily[key]['E']+=1
  if value['target_value'] is not None and cat in {'SOURCE_MATCHED','RECOVERED_SOURCE','RESTORED'}:daily[key]['B']+=1
 # Civil-day denominator uses local dates and the month's modal cadence/phase.
 daily_detail=[];daily_summary=[]
 for year in years:
  for month_num in range(1,13):
   month=f'{year}-{month_num:02d}';start=dt.date(int(year),month_num,1);end=dt.date(int(year)+1,1,1) if month_num==12 else dt.date(int(year),month_num+1,1)
   mode=modes.get((year,month),5);step=mode*60;ph=phases.get((year,month),0);d=start;cells=[]
   while d<end:
    ts0=int(dt.datetime.combine(d,dt.time(),TZ).timestamp());first=ts0+((ph-ts0)%step);next0=int(dt.datetime.combine(d+dt.timedelta(days=1),dt.time(),TZ).timestamp());exp=max(0,(next0-first+step-1)//step);x=daily[(year,d.isoformat())];cell={'date':d.isoformat(),'expected':exp,'B_observed':x['B'],'E_observed':x['E'],'B_coverage':x['B']/exp if exp else None,'E_coverage':x['E']/exp if exp else None};cells.append(cell);daily_detail.append({'year':year,'month':month,**cell});d+=dt.timedelta(days=1)
   bc=sum(x['B_observed'] for x in cells);ec=sum(x['E_observed'] for x in cells);ex=sum(x['expected'] for x in cells);bactive=sum(x['B_observed']>0 for x in cells);eactive=sum(x['E_observed']>0 for x in cells)
   daily_summary.append({'year':year,'month':month,'expected_slots':ex,'B_observed_slots':bc,'E_observed_slots':ec,'B_coverage':bc/ex if ex else 0,'E_coverage':ec/ex if ex else 0,'B_active_days':bactive,'B_zero_observation_days':len(cells)-bactive,'E_active_days':eactive,'B_days_coverage_ge_95':sum((x['B_coverage'] or 0)>=.95 for x in cells),'B_daily_coverage_min':min((x['B_coverage'] or 0) for x in cells),'B_daily_coverage_median':sorted((x['B_coverage'] or 0) for x in cells)[len(cells)//2]})
 db.close()
 for y in out:y['daily_distribution_summary']=[x for x in daily_summary if x['year']==y['year']]
 result={'schema':'loucka-annual-representativeness-review-v2','source_snapshot_id':json.loads((DATA/'STATISTICAL_VARIANTS_MANIFEST.json').read_text())['concordance_sqlite_sha256'],'scope':'outTemp monthly B/E comparison for the four highlighted years; day-level B/E occurrence, expected slots and coverage recomputed from exact local concordance values on the monthly modal cadence/phase grid.','years':out,'daily_distribution_by_month':daily_summary,'daily_distribution_by_day':daily_detail,'boundary_periods':{'2009':'partial first archive year; do not issue full-year statistic','2018':'Q1 protected; no year approval','2021':'diagnostic-only; no year approval','2026':'partial year through snapshot date; do not issue full-year statistic'},'screen_policy':'Retain existing annual gate: >=95% annual coverage, >=11 months passing, max gap <=6 hours, modal cadence share >=90%. No change authorized.'}
 (ROOT/'ANNUAL_REPRESENTATIVENESS_REVIEW.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
 print(json.dumps([{k:x[k] for k in ('year','B_annual_mean_C','E_annual_mean_C','B_coverage','months_B_coverage_ge_95','months_with_mean_screen_days_pass','worst_monthly_gap_seconds','worst_gap_month')} for x in out],indent=2))
if __name__=='__main__':main()
